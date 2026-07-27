from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.interfaces.schemas.schemas import PersonaCreate
from app.interfaces.schemas.miembro_schemas import (
    SolicitarMiembroRequest,
    AprobarRechazarRequest,
    SolicitudesPendientesResponse,
    SolicitudAprobadaResponse,
    SolicitudRechazadaResponse,
    EstadoSolicitudResponse,
)
from app.infrastructure.db.models import (
    Persona, ResidenteVivienda, MiembroVivienda, Vivienda,
    Notificacion, NotificacionDestino,
)
from app.infrastructure.dependencies import get_notificacion_service
from app.infrastructure.security.auth import obtener_usuario_con_rol, requerir_rol
from app.application.services.notificacion_service import NotificacionService
from datetime import datetime, date
from app.infrastructure.utils.time_utils import ahora_sin_tz
from app.infrastructure.utils.auditoria_helpers import registrar_bitacora
from pydantic import BaseModel, Field
from typing import Optional
import json

router = APIRouter(prefix="/api/v1/miembros", tags=["Miembros de Familia"])


@router.get("/familia", response_model=dict)
def listar_miembros_familia(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Lista miembros de familia con paginacion y busqueda."""
    query = (
        db.query(MiembroVivienda, Persona, Vivienda)
        .join(Persona, MiembroVivienda.persona_miembro_fk == Persona.persona_pk)
        .join(Vivienda, MiembroVivienda.vivienda_familia_fk == Vivienda.vivienda_pk)
        .filter(MiembroVivienda.eliminado == False, Persona.eliminado == False)
    )
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Persona.nombres.ilike(term)) | (Persona.identificacion.ilike(term))
        )
    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(Persona.apellidos.asc()).offset(offset).limit(page_size).all()

    data = []
    for m, p, v in items:
        residente = db.query(Persona).filter(
            Persona.persona_pk == m.persona_residente_fk
        ).first()
        data.append({
            "persona_id": p.persona_pk,
            "nombres": p.nombres,
            "apellidos": p.apellidos,
            "identificacion": p.identificacion,
            "parentesco": m.parentesco,
            "estado": m.estado,
            "manzana": v.manzana,
            "villa": v.villa,
            "residente_nombre": f"{residente.nombres} {residente.apellidos}" if residente else "N/A",
        })

    return {"data": data, "total": total, "page": page, "page_size": page_size}


class AgregarMiembroFamiliaRequest(BaseModel):
    """Schema para agregar miembro de familia"""
    # Identificación del residente titular
    identificacion_residente: str
    
    # Ubicación de la vivienda
    manzana: str
    villa: str
    
    # Datos de la persona
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = "Ecuador"
    correo: str = None
    celular: str = None
    direccion_alternativa: str = None
    
    # Parentesco
    parentesco: str
    parentesco_otro_desc: str = None
    
    # Auditoría
    usuario_creado: str = "api_user"


class DesactivarMiembroRequest(BaseModel):
    """Schema para desactivar miembro de familia"""
    usuario_actualizado: str = "api_user"
    fecha_actualizado: Optional[str] = None


class ReactivarMiembroRequest(BaseModel):
    """Schema para reactivar miembro de familia"""
    usuario_actualizado: str = "api_user"
    fecha_actualizado: Optional[str] = None


@router.post("/agregar", response_model=dict)
def agregar_miembro_familia(
    request: AgregarMiembroFamiliaRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Agrega un miembro de familia a un residente
    RF-R02: Agregar miembro de familia
    """
    try:
        # Validar parentescos válidos
        parentescos_validos = ['padre', 'madre', 'esposo', 'esposa', 'hijo', 'hija', 'otro']
        if request.parentesco.lower() not in parentescos_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parentesco inválido. Válidos: {', '.join(parentescos_validos)}"
            )
        
        # Validar vivienda por manzana y villa
        vivienda = db.query(Vivienda).filter(
            Vivienda.manzana == request.manzana,
            Vivienda.villa == request.villa
        ).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vivienda no encontrada para manzana '{request.manzana}' y villa '{request.villa}'"
            )
        
        vivienda_id = vivienda.vivienda_pk
        
        # Obtener la persona residente por identificación
        persona_residente = db.query(Persona).filter(
            Persona.identificacion == request.identificacion_residente
        ).first()
        if not persona_residente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Residente con identificación '{request.identificacion_residente}' no encontrado"
            )
        
        # Validar que el residente existe en esa vivienda
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == persona_residente.persona_pk,
            ResidenteVivienda.vivienda_reside_fk == vivienda_id,
            ResidenteVivienda.estado == "activo"
        ).first()
        if not residente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Residente con identificación '{request.identificacion_residente}' no está registrado como residente activo en esa vivienda"
            )
        
        # Validar que no exista persona con mismo documento
        persona_existe = db.query(Persona).filter(
            Persona.identificacion == request.identificacion
        ).first()
        if persona_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una persona con identificación {request.identificacion}"
            )
        
        # Crear persona
        persona = Persona(
            identificacion=request.identificacion,
            tipo_identificacion=request.tipo_identificacion,
            nacionalidad=request.nacionalidad,
            nombres=request.nombres,
            apellidos=request.apellidos,
            fecha_nacimiento=request.fecha_nacimiento,
            correo=request.correo,
            celular=request.celular,
            direccion_alternativa=request.direccion_alternativa,
            usuario_creado=request.usuario_creado
        )
        
        db.add(persona)
        db.flush()
        
        # Crear miembro familia
        miembro = MiembroVivienda(
            vivienda_familia_fk=vivienda_id,
            persona_residente_fk=residente.persona_residente_fk,
            persona_miembro_fk=persona.persona_pk,
            parentesco=request.parentesco.lower(),
            parentesco_otro_desc=request.parentesco_otro_desc if request.parentesco == 'otro' else None,
            usuario_creado=request.usuario_creado
        )
        
        db.add(miembro)
        db.flush()
        db.commit()
        db.refresh(miembro)

        registrar_bitacora(db, usuario, "miembro_vivienda",
                           miembro.miembro_vivienda_pk, "crear",
                           f"Miembro {persona.nombres} {persona.apellidos} agregado")

        return {
            "success": True,
            "miembro_id": miembro.miembro_vivienda_pk,
            "persona_id": persona.persona_pk,
            "vivienda_id": vivienda_id,
            "mensaje": "Miembro de familia agregado exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/{vivienda_id}", response_model=dict)
def obtener_miembros_familia(
    vivienda_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los miembros de familia de una vivienda
    """
    try:
        vivienda = db.query(Vivienda).filter(Vivienda.vivienda_pk == vivienda_id).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        miembros = db.query(MiembroVivienda).filter(
            MiembroVivienda.vivienda_familia_fk == vivienda_id,
            MiembroVivienda.eliminado == False,
        ).all()
        
        miembros_data = []
        for miembro in miembros:
            persona = miembro.persona_miembro
            residente = db.query(Persona).filter(
                Persona.persona_pk == miembro.persona_residente_fk
            ).first()
            
            miembros_data.append({
                "miembro_id": miembro.miembro_vivienda_pk,
                "persona_id": persona.persona_pk,
                "residente_titula": f"{residente.nombres} {residente.apellidos}" if residente else "N/A",
                "nombres": f"{persona.nombres} {persona.apellidos}",
                "identificacion": persona.identificacion,
                "parentesco": miembro.parentesco,
                "correo": persona.correo,
                "celular": persona.celular,
                "estado" : miembro.estado
            })
        
        return {
            "vivienda_id": vivienda_id,
            "total_miembros": len(miembros_data),
            "miembros": miembros_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{miembro_id}/desactivar", response_model=dict)
def desactivar_miembro(
    miembro_id: int,
    request: DesactivarMiembroRequest,
    db: Session = Depends(get_db)
):
    """
    Desactiva un miembro de familia
    RF-R04: Desactivar miembro
    """
    try:
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.miembro_vivienda_pk == miembro_id
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro no encontrado"
            )
        
        miembro.estado = "inactivo"
        miembro.fecha_actualizado = ahora_sin_tz()
        miembro.usuario_actualizado = request.usuario_actualizado

        db.commit()

        registrar_bitacora(db, usuario, "miembro_vivienda", miembro_id,
                           "desactivar", f"Miembro {miembro_id} desactivado",
                           valor_anterior="activo", valor_nuevo="inactivo")

        return {
            "success": True,
            "mensaje": "Miembro desactivado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{miembro_id}/reactivar", response_model=dict)
def reactivar_miembro(
    miembro_id: int,
    request: ReactivarMiembroRequest,
    db: Session = Depends(get_db)
):
    """
    Reactiva un miembro de familia
    RF-R06: Reactivar miembro
    """
    try:
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.miembro_vivienda_pk == miembro_id
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro no encontrado"
            )
        
        miembro.estado = "activo"
        miembro.fecha_actualizado = ahora_sin_tz()
        miembro.usuario_actualizado = request.usuario_actualizado

        db.commit()

        registrar_bitacora(db, usuario, "miembro_vivienda", miembro_id,
                           "reactivar", f"Miembro {miembro_id} reactivado",
                           valor_anterior="inactivo", valor_nuevo="activo")

        return {
            "success": True,
            "mensaje": "Miembro reactivado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{miembro_id}", response_model=dict)
def eliminar_miembro(
    miembro_id: int,
    motivo_eliminado: str = "Eliminación de miembro",
    usuario_actualizado: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Elimina un miembro de familia (soft delete)
    """
    try:
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.miembro_vivienda_pk == miembro_id
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro no encontrado"
            )
        
        miembro.eliminado = True
        miembro.motivo_eliminado = motivo_eliminado
        miembro.fecha_actualizado = ahora_sin_tz()
        miembro.usuario_actualizado = usuario_actualizado

        db.commit()

        registrar_bitacora(db, usuario, "miembro_vivienda", miembro_id,
                           "eliminar", f"Miembro {miembro_id} eliminado")

        return {
            "success": True,
            "mensaje": "Miembro eliminado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/manzana-villa/{manzana}/{villa}", response_model=dict)
def obtener_miembros_por_ubicacion(
    manzana: str,
    villa: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los miembros de familia de una vivienda por manzana y villa
    """
    try:
        # Obtener vivienda
        vivienda = db.query(Vivienda).filter(
            Vivienda.manzana == manzana,
            Vivienda.villa == villa,
            Vivienda.estado == "activo"
        ).first()
        
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        # Obtener miembros de familia activos
        miembros = db.query(MiembroVivienda).filter(
            MiembroVivienda.vivienda_familia_fk == vivienda.vivienda_pk,
            # MiembroVivienda.estado == "activo",
            MiembroVivienda.eliminado == False
        ).all()
        
        miembros_data = []
        for miembro in miembros:
            persona = miembro.persona_miembro
            miembros_data.append({
                "miembro_id": miembro.miembro_vivienda_pk,
                "persona_id": persona.persona_pk,
                "identificacion": persona.identificacion,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "correo": persona.correo,
                "celular": persona.celular,
                "parentesco": miembro.parentesco,
                "estado": miembro.estado
            })
        
        return {
            "vivienda_id": vivienda.vivienda_pk,
            "manzana": vivienda.manzana,
            "villa": vivienda.villa,
            "total_miembros": len(miembros_data),
            "miembros": miembros_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ═══════════════════════════════════════════════════════════════
# AUTO-REGISTRO DE MIEMBRO CON AUTORIZACION DEL TITULAR
# ═══════════════════════════════════════════════════════════════
# POST /agregar (existente) sigue funcionando sin cambios para
# admin y titular que registran directamente.
# Estos endpoints son solo para el flujo de auto-registro.
# ═══════════════════════════════════════════════════════════════


# ─── SOLICITAR REGISTRO (MIEMBRO) ────────────────────────────


@router.post("/solicitar", response_model=dict)
async def solicitar_registro_miembro(
    request: SolicitarMiembroRequest,
    db: Session = Depends(get_db),
    notificacion_service: NotificacionService = Depends(
        get_notificacion_service
    ),
):
    """
    AUTO-REGISTRO: Crea una solicitud que requiere aprobacion del titular.

    NO crea Persona ni MiembroVivienda hasta que el titular APRUEBE.
    Envia notificacion push al titular + sincroniza Firestore para badge.
    """
    try:
        parentescos_validos = [
            "padre", "madre", "esposo", "esposa",
            "hijo", "hija", "otro",
        ]
        if request.parentesco not in parentescos_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parentesco invalido. Validos: {parentescos_validos}",
            )

        if (
            request.parentesco == "otro"
            and not request.parentesco_otro_desc
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe especificar parentesco_otro_desc",
            )

        vivienda = db.query(Vivienda).filter(
            Vivienda.manzana == request.manzana.strip().upper(),
            Vivienda.villa == request.villa.strip(),
            Vivienda.estado == "activo",
            Vivienda.eliminado == False,
        ).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada",
            )

        residente = (
            db.query(ResidenteVivienda)
            .join(
                Persona,
                ResidenteVivienda.persona_residente_fk == Persona.persona_pk,
            )
            .filter(
                ResidenteVivienda.vivienda_reside_fk == vivienda.vivienda_pk,
                ResidenteVivienda.estado == "activo",
                ResidenteVivienda.eliminado == False,
                Persona.identificacion == request.identificacion_residente,
            )
            .first()
        )
        if not residente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Residente titular no encontrado en esta vivienda",
            )

        persona_existente = db.query(Persona).filter(
            Persona.identificacion == request.identificacion,
            Persona.estado == "activo",
            Persona.eliminado == False,
        ).first()
        if persona_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una persona activa con esta identificacion",
            )

        solicitud_pendiente = (
            db.query(Notificacion)
            .filter(
                Notificacion.tipo == "solicitud_miembro",
                Notificacion.eliminado == False,
                Notificacion.mensaje.contains(request.identificacion),
            )
            .first()
        )
        if solicitud_pendiente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una solicitud pendiente para esta identificacion",
            )

        datos_miembro = {
            "identificacion": request.identificacion,
            "tipo_identificacion": request.tipo_identificacion,
            "nombres": request.nombres,
            "apellidos": request.apellidos,
            "fecha_nacimiento": str(request.fecha_nacimiento),
            "nacionalidad": request.nacionalidad,
            "correo": request.correo,
            "celular": request.celular,
            "direccion_alternativa": request.direccion_alternativa,
            "parentesco": request.parentesco,
            "parentesco_otro_desc": request.parentesco_otro_desc,
            "manzana": vivienda.manzana,
            "villa": vivienda.villa,
            "vivienda_id": vivienda.vivienda_pk,
            "residente_id": residente.persona_residente_fk,
            "token_fcm": request.token_fcm,
            "plataforma": request.plataforma,
        }

        titulo = "Solicitud de registro de familiar"
        cuerpo = (
            f"{request.nombres} {request.apellidos} quiere registrarse "
            f"como {request.parentesco} en tu vivienda "
            f"(Mz {vivienda.manzana}, Villa {vivienda.villa})."
        )

        resultado = await notificacion_service.enviar_notificacion_individual(
            persona_id=residente.persona_residente_fk,
            titulo=titulo,
            cuerpo=cuerpo,
            tipo="solicitud_miembro",
            prioridad="alta",
            categoria="visita",
            ruta_accion="/aprobacionMiembro",
            datos_accion={
                "nombres": request.nombres,
                "apellidos": request.apellidos,
                "identificacion": request.identificacion,
                "parentesco": request.parentesco,
                "parentesco_otro_desc": request.parentesco_otro_desc,
                "manzana": vivienda.manzana,
                "villa": vivienda.villa,
                "fecha_nacimiento": str(request.fecha_nacimiento),
                "correo": request.correo,
                "celular": request.celular,
                "datos_miembro": datos_miembro,
            },
        )

        notificacion = (
            db.query(Notificacion)
            .filter(
                Notificacion.notificacion_pk
                == resultado.notificacion_id,
            )
            .first()
        )
        if notificacion:
            mensaje_previo = json.loads(notificacion.mensaje)
            mensaje_previo["datos_accion"]["notificacionId"] = (
                notificacion.notificacion_pk
            )
            notificacion.mensaje = json.dumps(mensaje_previo)

        db.commit()

        registrar_bitacora(db, usuario, "miembro_vivienda", 0,
                           "solicitar",
                           f"Solicitud de miembro: {request.nombres} {request.apellidos}")

        return {
            "success": True,
            "notificacion_id": resultado.notificacion_id,
            "mensaje": (
                "Solicitud enviada al residente titular. "
                "Recibiras una notificacion cuando sea revisada."
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ─── LISTAR SOLICITUDES PENDIENTES (TITULAR) ─────────────────


@router.get(
    "/solicitudes/pendientes",
    response_model=SolicitudesPendientesResponse,
)
async def listar_solicitudes_pendientes(
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_con_rol),
):
    """Lista solicitudes pendientes para el titular autenticado"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(
            status_code=400,
            detail="Usuario sin persona asociada",
        )

    try:
        solicitudes = (
            db.query(Notificacion, NotificacionDestino)
            .join(
                NotificacionDestino,
                Notificacion.notificacion_pk
                == NotificacionDestino.notificacion_envio_fk,
            )
            .filter(
                NotificacionDestino.persona_receptor_fk == persona_id,
                Notificacion.tipo == "solicitud_miembro",
                Notificacion.eliminado == False,
                NotificacionDestino.eliminado == False,
            )
            .order_by(Notificacion.fecha_creado.desc())
            .all()
        )

        resultado = []
        for notif, destino in solicitudes:
            try:
                data = json.loads(notif.mensaje)
                datos = data.get("datos_accion", {}).get("datos_miembro", {})
                resultado.append({
                    "notificacion_id": notif.notificacion_pk,
                    "nombres": datos.get("nombres", ""),
                    "apellidos": datos.get("apellidos", ""),
                    "identificacion": datos.get("identificacion", ""),
                    "parentesco": datos.get("parentesco", ""),
                    "parentesco_otro_desc": datos.get("parentesco_otro_desc"),
                    "manzana": datos.get("manzana", ""),
                    "villa": datos.get("villa", ""),
                    "fecha_solicitud": (
                        notif.fecha_creado.isoformat()
                        if notif.fecha_creado
                        else None
                    ),
                })
            except json.JSONDecodeError:
                pass

        return {"total": len(resultado), "solicitudes": resultado}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ─── APROBAR SOLICITUD ──────────────────────────────────────


@router.put(
    "/solicitudes/{notificacion_id}/aprobar",
    response_model=SolicitudAprobadaResponse,
)
async def aprobar_solicitud_miembro(
    notificacion_id: int,
    request_body: AprobarRechazarRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_con_rol),
):
    """Aprueba la solicitud: crea Persona + MiembroVivienda(activo)"""
    persona_id = usuario.get("persona_id")

    try:
        notificacion = db.query(Notificacion).filter(
            Notificacion.notificacion_pk == notificacion_id,
            Notificacion.tipo == "solicitud_miembro",
            Notificacion.eliminado == False,
        ).first()
        if not notificacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada",
            )

        destino = (
            db.query(NotificacionDestino)
            .filter(
                NotificacionDestino.notificacion_envio_fk
                == notificacion_id,
                NotificacionDestino.persona_receptor_fk == persona_id,
            )
            .first()
        )
        if not destino:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para aprobar esta solicitud",
            )

        mensaje_data = json.loads(notificacion.mensaje)
        datos = mensaje_data.get("datos_accion", {}).get("datos_miembro", {})

        persona_existente = db.query(Persona).filter(
            Persona.identificacion == datos.get("identificacion"),
            Persona.estado == "activo",
            Persona.eliminado == False,
        ).first()
        if persona_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una persona activa con esta identificacion",
            )

        fecha_nac = None
        if datos.get("fecha_nacimiento"):
            fecha_nac = datetime.strptime(
                datos["fecha_nacimiento"], "%Y-%m-%d"
            ).date()

        nueva_persona = Persona(
            identificacion=datos.get("identificacion"),
            tipo_identificacion=datos.get("tipo_identificacion", "cedula"),
            nombres=datos.get("nombres"),
            apellidos=datos.get("apellidos"),
            fecha_nacimiento=fecha_nac,
            nacionalidad=datos.get("nacionalidad", "Ecuador"),
            correo=datos.get("correo"),
            celular=datos.get("celular"),
            direccion_alternativa=datos.get("direccion_alternativa"),
            estado="activo",
            usuario_creado=request_body.usuario_actualizado,
        )
        db.add(nueva_persona)
        db.flush()

        nuevo_miembro = MiembroVivienda(
            vivienda_familia_fk=datos.get("vivienda_id"),
            persona_residente_fk=persona_id,
            persona_miembro_fk=nueva_persona.persona_pk,
            parentesco=datos.get("parentesco"),
            parentesco_otro_desc=datos.get("parentesco_otro_desc"),
            estado="activo",
            usuario_creado=request_body.usuario_actualizado,
        )
        db.add(nuevo_miembro)
        db.flush()

        notificacion.tipo = "miembro_aprobado"
        destino.entregada = True

        token_fcm = datos.get("token_fcm")
        if token_fcm:
            try:
                from app.application.services.firestore_sync_service import (
                    FirestoreSyncService,
                )
                from app.infrastructure.notifications.fcm_client import (
                    FCMClient,
                )

                firestore = FirestoreSyncService()
                await firestore.guardar_token_fcm(
                    nueva_persona.persona_pk,
                    token_fcm,
                    datos.get("plataforma", "android"),
                )

                fcm = FCMClient()
                fcm.enviar_notificacion_push(
                    token=token_fcm,
                    titulo="Solicitud Aprobada",
                    cuerpo=(
                        f"Tu solicitud para registrarte como {datos.get('parentesco')} "
                        f"en Mz {datos.get('manzana')}, Villa {datos.get('villa')} "
                        f"ha sido APROBADA."
                    ),
                    datos={
                        "tipo": "miembro_aprobado",
                        "persona_id": str(nueva_persona.persona_pk),
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    },
                )
            except Exception as e:
                print(f"Error enviando push de aprobacion: {e}")

        db.commit()

        registrar_bitacora(db, usuario, "miembro_vivienda",
                           nuevo_miembro.miembro_vivienda_pk, "aprobar",
                           f"Solicitud aprobada: {nueva_persona.nombres} {nueva_persona.apellidos}")

        return {
            "success": True,
            "persona_id": nueva_persona.persona_pk,
            "miembro_id": nuevo_miembro.miembro_vivienda_pk,
            "mensaje": "Miembro aprobado y registrado exitosamente.",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ─── RECHAZAR SOLICITUD ─────────────────────────────────────


@router.put(
    "/solicitudes/{notificacion_id}/rechazar",
    response_model=SolicitudRechazadaResponse,
)
async def rechazar_solicitud_miembro(
    notificacion_id: int,
    request_body: AprobarRechazarRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_con_rol),
):
    """Rechaza la solicitud. NO crea Persona."""
    persona_id = usuario.get("persona_id")

    try:
        notificacion = db.query(Notificacion).filter(
            Notificacion.notificacion_pk == notificacion_id,
            Notificacion.tipo == "solicitud_miembro",
            Notificacion.eliminado == False,
        ).first()
        if not notificacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada",
            )

        destino = (
            db.query(NotificacionDestino)
            .filter(
                NotificacionDestino.notificacion_envio_fk
                == notificacion_id,
                NotificacionDestino.persona_receptor_fk == persona_id,
            )
            .first()
        )
        if not destino:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para rechazar esta solicitud",
            )

        notificacion.tipo = "miembro_rechazado"
        if request_body.motivo:
            notificacion.motivo_eliminado = request_body.motivo
        destino.entregada = True

        mensaje_data = json.loads(notificacion.mensaje)
        datos_miembro = mensaje_data.get("datos_accion", {}).get("datos_miembro", {})
        token_fcm = datos_miembro.get("token_fcm")
        if token_fcm:
            try:
                from app.infrastructure.notifications.fcm_client import (
                    FCMClient,
                )

                motivo_rechazo = request_body.motivo or "No especificado"
                fcm = FCMClient()
                fcm.enviar_notificacion_push(
                    token=token_fcm,
                    titulo="Solicitud Rechazada",
                    cuerpo=(
                        f"Tu solicitud para registrarte como "
                        f"{datos_miembro.get('parentesco', 'familiar')} "
                        f"ha sido RECHAZADA. Motivo: {motivo_rechazo}"
                    ),
                    datos={
                        "tipo": "miembro_rechazado",
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    },
                )
            except Exception as e:
                print(f"Error enviando push de rechazo: {e}")

        db.commit()

        registrar_bitacora(db, usuario, "miembro_vivienda",
                           notificacion_id, "rechazar",
                           f"Solicitud rechazada: notificacion {notificacion_id}")

        return {"success": True, "mensaje": "Solicitud rechazada."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ─── CONSULTAR ESTADO (MIEMBRO CONSULTA) ────────────────────


@router.get(
    "/solicitudes/estado/{identificacion}",
    response_model=EstadoSolicitudResponse,
)
async def consultar_estado_solicitud(
    identificacion: str,
    db: Session = Depends(get_db),
):
    """
    Consulta el estado de una solicitud por identificacion.

    Primero busca en notificaciones para determinar si paso por el
    flujo de autorizacion. Solo retorna 'aprobado' si existe una
    notificacion 'miembro_aprobado' Y la persona fue creada a partir
    de ella. Ignora personas creadas por otros flujos (POST /agregar,
    pruebas, etc.).
    """
    try:
        notificacion = (
            db.query(Notificacion)
            .filter(
                Notificacion.tipo.in_(
                    [
                        "solicitud_miembro",
                        "miembro_aprobado",
                        "miembro_rechazado",
                    ]
                ),
                Notificacion.eliminado == False,
                Notificacion.mensaje.contains(identificacion),
            )
            .order_by(Notificacion.fecha_creado.desc())
            .first()
        )

        if not notificacion:
            return {
                "estado": "no_encontrado",
                "mensaje": "No se encontro solicitud para esta identificacion",
            }

        if notificacion.tipo == "miembro_aprobado":
            try:
                mensaje_data = json.loads(notificacion.mensaje)
                datos = mensaje_data.get("datos_accion", {}).get("datos_miembro", {})
                persona = db.query(Persona).filter(
                    Persona.identificacion
                    == datos.get("identificacion"),
                    Persona.estado == "activo",
                    Persona.eliminado == False,
                ).first()
                if persona:
                    miembro = db.query(MiembroVivienda).filter(
                        MiembroVivienda.persona_miembro_fk
                        == persona.persona_pk,
                        MiembroVivienda.estado == "activo",
                        MiembroVivienda.eliminado == False,
                    ).first()
                    return {
                        "estado": "aprobado",
                        "persona_id": persona.persona_pk,
                        "miembro_id": (
                            miembro.miembro_vivienda_pk if miembro else None
                        ),
                    }
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        if notificacion.tipo == "miembro_rechazado":
            return {
                "estado": "rechazado",
                "motivo": notificacion.motivo_eliminado,
            }

        if notificacion.tipo == "solicitud_miembro":
            return {
                "estado": "pendiente",
                "notificacion_id": notificacion.notificacion_pk,
            }

        return {"estado": "no_encontrado"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ═══════════════════════════════════════════════════════════════
# RESIDENTE GESTIONA SUS MIEMBROS (BLOQUEAR / DESBLOQUEAR)
# ═══════════════════════════════════════════════════════════════


class BloquearDesbloquearRequest(BaseModel):
    motivo: str = Field(..., min_length=1, description="Motivo del bloqueo/desbloqueo")


@router.post(
    "/{miembro_id}/bloquear", response_model=dict
)
def bloquear_miembro_por_residente(
    miembro_id: int,
    request: BloquearDesbloquearRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("residente")),
):
    """
    Permite que un residente bloquee a uno de sus miembros de familia.
    Solo el titular asociado al miembro puede bloquearlo.
    """
    persona_id = usuario.get("persona_id")

    miembro = (
        db.query(MiembroVivienda)
        .filter(
            MiembroVivienda.persona_miembro_fk == miembro_id,
            MiembroVivienda.estado == 'activo',
            MiembroVivienda.eliminado == False,
        )
        .first()
    )

    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado",
        )

    if miembro.persona_residente_fk != persona_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene autorizacion sobre este miembro",
        )

    if miembro.estado == "inactivo":
        return {
            "success": True,
            "mensaje": "Advertencia: la cuenta ya se encuentra inactiva",
        }

    miembro.estado = "inactivo"
    miembro.fecha_actualizado = ahora_sin_tz()
    miembro.usuario_actualizado = usuario.get("email", "")
    db.commit()

    registrar_bitacora(db, usuario, "miembro_vivienda", miembro_id,
                       "bloquear", f"Miembro {miembro_id} bloqueado por residente",
                       valor_anterior="activo", valor_nuevo="inactivo")
    return {"success": True, "mensaje": "Miembro bloqueado correctamente"}


@router.post(
    "/{miembro_id}/desbloquear", response_model=dict
)
def desbloquear_miembro_por_residente(
    miembro_id: int,
    request: BloquearDesbloquearRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("residente")),
):
    """
    Permite que un residente desbloquee a uno de sus miembros de familia.
    Solo el titular asociado al miembro puede desbloquearlo.
    """
    persona_id = usuario.get("persona_id")

    miembro = (
        db.query(MiembroVivienda)
        .filter(
            MiembroVivienda.persona_miembro_fk == miembro_id,
            MiembroVivienda.eliminado == False,
            MiembroVivienda.estado == 'inactivo',
        )
        .first()
    )

    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado",
        )

    if miembro.persona_residente_fk != persona_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene autorizacion sobre este miembro",
        )

    if miembro.estado == "activo":
        return {
            "success": True,
            "mensaje": "Advertencia: la cuenta ya se encuentra activa",
        }

    miembro.estado = "activo"
    miembro.fecha_actualizado = ahora_sin_tz()
    miembro.usuario_actualizado = usuario.get("email", "")
    db.commit()

    registrar_bitacora(db, usuario, "miembro_vivienda", miembro_id,
                       "desbloquear", f"Miembro {miembro_id} desbloqueado por residente",
                       valor_anterior="inactivo", valor_nuevo="activo")
    return {"success": True, "mensaje": "Miembro desbloqueado correctamente"}


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS DE VISITANTES POR USUARIO
# ═══════════════════════════════════════════════════════════════


@router.get("/visitantes", response_model=dict)
def listar_visitantes_usuario(
    usuario_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_con_rol),
):
    """Lista visitantes registrados para un usuario."""
    from app.infrastructure.db.models import Visita as VisitaModel
    vivienda_id = None
    residente = db.query(ResidenteVivienda).filter(
        ResidenteVivienda.persona_residente_fk == usuario_id,
        ResidenteVivienda.estado == "activo",
        ResidenteVivienda.eliminado == False,
    ).first()
    if residente:
        vivienda_id = residente.vivienda_reside_fk
    if not vivienda_id:
        return {"data": [], "total": 0, "page": page, "page_size": page_size}

    query = db.query(VisitaModel).filter(
        VisitaModel.vivienda_visita_fk == vivienda_id,
        VisitaModel.eliminado == False,
    )
    total = query.count()
    visitas = query.order_by(VisitaModel.fecha_creado.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    data = [
        {
            "visita_id": v.visita_pk,
            "identificacion": v.identificacion,
            "nombres": v.nombres,
            "apellidos": v.apellidos,
            "fecha_creado": v.fecha_creado.isoformat() if v.fecha_creado else None,
        }
        for v in visitas
    ]
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/visitantes/{visitante_id}", response_model=dict)
def obtener_visitante_usuario(
    visitante_id: int,
    usuario_id: int = Query(...),
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_con_rol),
):
    """Obtiene un visitante especifico."""
    from app.infrastructure.db.models import Visita as VisitaModel
    v = db.query(VisitaModel).filter(
        VisitaModel.visita_pk == visitante_id,
        VisitaModel.eliminado == False,
    ).first()
    if not v:
        raise HTTPException(status_code=404, detail="Visitante no encontrado")
    return {
        "visita_id": v.visita_pk,
        "identificacion": v.identificacion,
        "nombres": v.nombres,
        "apellidos": v.apellidos,
        "fecha_creado": v.fecha_creado.isoformat() if v.fecha_creado else None,
    }


@router.post("/visitantes", response_model=dict)
def crear_visitante_usuario(
    request: dict,
    usuario_id: int = Query(...),
    db: Session = Depends(get_db),
    usuario: dict = Depends(obtener_usuario_con_rol),
):
    """Crea o actualiza un visitante."""
    from app.infrastructure.db.models import Visita as VisitaModel
    vivienda_id = None
    residente = db.query(ResidenteVivienda).filter(
        ResidenteVivienda.persona_residente_fk == usuario_id,
        ResidenteVivienda.estado == "activo",
        ResidenteVivienda.eliminado == False,
    ).first()
    if residente:
        vivienda_id = residente.vivienda_reside_fk
    if not vivienda_id:
        raise HTTPException(status_code=404, detail="Vivienda no encontrada para este usuario")

    if request.get("id"):
        visita = db.query(VisitaModel).filter(
            VisitaModel.visita_pk == request["id"],
            VisitaModel.vivienda_visita_fk == vivienda_id,
        ).first()
        if visita:
            visita.nombres = request.get("nombre", visita.nombres)
            visita.identificacion = request.get("telefono", visita.identificacion)
            db.commit()
            registrar_bitacora(db, usuario, "visita", visita.visita_pk,
                               "actualizar", "Visitante actualizado")
            return {"success": True, "visita_id": visita.visita_pk, "mensaje": "Visitante actualizado"}

    visita = VisitaModel(
        vivienda_visita_fk=vivienda_id,
        identificacion=request.get("telefono", request.get("identificacion", "")),
        nombres=request.get("nombre", ""),
        usuario_creado=usuario.get("email", ""),
    )
    db.add(visita)
    db.commit()
    db.refresh(visita)
    registrar_bitacora(db, usuario, "visita", visita.visita_pk,
                       "crear", "Visitante creado")
    return {"success": True, "visita_id": visita.visita_pk, "mensaje": "Visitante creado"}
