from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.interfaces.schemas.schemas import (
    PersonaCreate, PersonaResponse
)

from app.infrastructure.security.auth import requerir_rol
from app.infrastructure.db.models import Persona, PropietarioVivienda, ResidenteVivienda, Vivienda
from datetime import datetime, date
from pydantic import BaseModel, field_validator, EmailStr
from app.infrastructure.utils.time_utils import ahora_sin_tz
from app.infrastructure.utils.auditoria_helpers import registrar_bitacora
from app.domain.validators import (
    validar_cedula_ecuatoriana,
    validar_edad_minima,
    validar_celular
)
import json

router = APIRouter(prefix="/api/v1/propietarios", tags=["Propietarios"])


class RegistrarPropietarioRequest(BaseModel):
    """Schema para registrar propietario"""
    # Datos de la persona
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = "Ecuador"
    correo: str
    celular: str
    direccion_alternativa: str = None
    
    # Ubicación de la vivienda
    manzana: str
    villa: str
    
    # Indica que viene del flujo de cambio de propietario
    from_change_owner: bool = False


class RegistrarConyyugeRequest(BaseModel):
    """Schema para registrar cónyuge como copropietario"""
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = "Ecuador"
    correo: EmailStr
    celular: str
    direccion_alternativa: str = None

    @field_validator("identificacion")
    @classmethod
    def validar_identificacion(cls, v, info):
        tipo = info.data.get("tipo_identificacion", "Cedula")
        if tipo == "Cedula":
            if not v or not v.isdigit() or len(v) != 10:
                raise ValueError("Error: cedula ecuatoriana invalida")
            if not validar_cedula_ecuatoriana(v):
                raise ValueError("Error: cedula ecuatoriana invalida")
        elif tipo in ("pasaporte", "otro"):
            if not v or v.strip() == "":
                raise ValueError("Error: identificacion no puede estar vacia")
        return v

    @field_validator("nombres")
    @classmethod
    def validar_nombres(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Error: los nombres son obligatorios")
        return v.strip()

    @field_validator("apellidos")
    @classmethod
    def validar_apellidos(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Error: los apellidos son obligatorios")
        return v.strip()

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha(cls, v):
        error = validar_edad_minima(v)
        if error:
            raise ValueError(error)
        return v

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, v):
        error = validar_celular(v)
        if error:
            raise ValueError(error)
        return v


class BajaRequest(BaseModel):
    """Schema para baja de propietario"""
    motivo: str


class EliminarPropietarioRequest(BaseModel):
    """Schema para eliminar propietario (body del DELETE)"""
    motivo: str = "Cambio de propietario"


class CambioPropiedadRequest(BaseModel):
    """Schema para cambio de propietario"""
    vivienda_id: int
    nuevo_propietario_id: int
    motivo_cambio: str


class ActualizarPropietarioRequest(BaseModel):
    """Schema para actualizar propietario"""
    correo_nuevo: str = None
    celular_nuevo: str = None
    direccion_alternativa: str = None


@router.post("", response_model=dict)
def registrar_propietario(
    request: RegistrarPropietarioRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Registra un nuevo propietario y lo asigna a una vivienda
    RF-P01: Registrar propietario
    """
    try:
        email = usuario.get("email", "") or "user_system"
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
            usuario_creado=email
        )
        
        db.add(persona)
        db.flush()
        
        # Validar propietario titular activo en esta vivienda
        anterior = None
        if request.from_change_owner:
            # PRIMERO desactivar al anterior (para liberar constraint)
            anterior = db.query(PropietarioVivienda).filter(
                PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
                PropietarioVivienda.tipo_propietario == "titular",
                PropietarioVivienda.estado == "activo",
                PropietarioVivienda.eliminado == False
            ).first()
            if anterior:
                email = usuario.get("email", "") or "user_system"
                anterior.estado = "inactivo"
                anterior.eliminado = True
                anterior.fecha_actualizado = datetime.utcnow()
                anterior.usuario_actualizado = email

                conyuge = db.query(PropietarioVivienda).filter(
                    PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
                    PropietarioVivienda.tipo_propietario == "conyuge",
                    PropietarioVivienda.estado == "activo",
                    PropietarioVivienda.eliminado == False
                ).first()
                if conyuge:
                    conyuge.estado = "inactivo"
                    conyuge.eliminado = True
                    conyuge.fecha_actualizado = datetime.utcnow()
                    conyuge.usuario_actualizado = email

                db.flush()  # LIBERAR CONSTRAINT antes de crear el nuevo
        else:
            # Validación normal: rechazar si ya existe propietario activo
            propietario_titular_existente = db.query(PropietarioVivienda).filter(
                PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
                PropietarioVivienda.tipo_propietario == "titular",
                PropietarioVivienda.estado == "activo",
                PropietarioVivienda.eliminado == False
            ).first()

            if propietario_titular_existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Esta vivienda ya tiene un propietario titular registrado"
                )
        
        # Crear relación propietario-vivienda con tipo_propietario="titular"
        propietario = PropietarioVivienda(
            vivienda_propiedad_fk=vivienda_id,
            persona_propietario_fk=persona.persona_pk,
            tipo_propietario="titular",
            estado="activo",
            usuario_creado=email
        )
        
        db.add(propietario)
        # db.flush()
        
        # # Registrar propietario también como residente
        # residente = ResidenteVivienda(
        #     vivienda_reside_fk=vivienda_id,
        #     persona_residente_fk=persona.persona_pk,
        #     estado='activo',
        #     usuario_creado=request.usuario_creado
        # )
        # db.add(residente)
        db.commit()
        db.refresh(persona)

        if request.from_change_owner:
            registrar_bitacora(db, usuario, "propietario_vivienda", vivienda_id,
                               "cambiar_propietario",
                               f"Propietario anterior desactivado. Nuevo propietario registrado: {persona.persona_pk}",
                               valor_anterior=str(anterior.persona_propietario_fk) if anterior else "ninguno",
                               valor_nuevo=str(persona.persona_pk))
        else:
            registrar_bitacora(db, usuario, "propietario_vivienda",
                               propietario.propietario_vivienda_pk, "crear",
                               f"Propietario {persona.nombres} {persona.apellidos} creado")

        return {
            "success": True,
            "persona_id": persona.persona_pk,
            "propietario_id": propietario.propietario_vivienda_pk,
            "vivienda_id": vivienda_id,
            "mensaje": "Propietario registrado con exito"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{propietario_id}/conyuge", response_model=dict)
def obtener_conyuge(
    propietario_id: int,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Obtiene el conyuge de un propietario."""
    propietario = db.query(PropietarioVivienda).filter(
        PropietarioVivienda.propietario_vivienda_pk == propietario_id,
        PropietarioVivienda.eliminado == False,
    ).first()
    if not propietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propietario no encontrado",
        )

    conyuge = (
        db.query(PropietarioVivienda, Persona)
        .join(
            Persona,
            PropietarioVivienda.persona_propietario_fk == Persona.persona_pk,
        )
        .filter(
            PropietarioVivienda.vivienda_propiedad_fk == propietario.vivienda_propiedad_fk,
            PropietarioVivienda.tipo_propietario == "conyuge",
            PropietarioVivienda.eliminado == False,
            Persona.eliminado == False,
        )
        .first()
    )

    if not conyuge:
        return {"conyuge": None}

    return {
        "conyuge": {
            "conyuge_id": conyuge[0].propietario_vivienda_pk,
            "persona_id": conyuge[1].persona_pk,
            "nombres": conyuge[1].nombres,
            "apellidos": conyuge[1].apellidos,
            "identificacion": conyuge[1].identificacion,
            "correo": conyuge[1].correo,
            "celular": conyuge[1].celular,
            "estado": conyuge[0].estado,
        }
    }


@router.post("/{propietario_id}/conyuge", response_model=dict)
def registrar_conyuge_propietario(
    propietario_id: int,
    request: RegistrarConyyugeRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Registra un cónyuge como copropietario
    RF-P02: Registrar cónyuge
    """
    try:
        email = usuario.get("email", "") or "user_system"
        # Validar propietario existe y activo
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id,
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False,
        ).first()
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado o inactivo"
            )
        
        vivienda_id = propietario.vivienda_propiedad_fk
        
        # Validar que no exista persona con mismo documento
        persona_existe = db.query(Persona).filter(
            Persona.identificacion == request.identificacion
        ).first()
        if persona_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una persona con identificación {request.identificacion}"
            )
        
        # Crear persona (cónyuge)
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
            usuario_creado=email
        )
        
        db.add(persona)
        db.flush()
        
        # Validar que solo exista un cónyuge por propiedad
        conyuge_existente = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.tipo_propietario == "conyuge",
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).first()
        
        if conyuge_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta vivienda ya tiene un cónyuge registrado"
            )
        
        # Crear relación cónyuge-vivienda con tipo_propietario="conyuge"
        conyuge = PropietarioVivienda(
            vivienda_propiedad_fk=vivienda_id,
            persona_propietario_fk=persona.persona_pk,
            tipo_propietario="conyuge",
            estado="activo",
            usuario_creado=email
        )
        
        db.add(conyuge)
        db.commit()
        db.refresh(persona)
        db.refresh(conyuge)

        registrar_bitacora(db, usuario, "propietario_vivienda",
                           conyuge.propietario_vivienda_pk, "crear_conyuge",
                           f"Conyuge registrado para propietario {propietario_id} en Mz {propietario.vivienda.manzana}, Villa {propietario.vivienda.villa}",
                           valor_nuevo=json.dumps({"persona_id": persona.persona_pk, "vivienda_id": vivienda_id, "tipo": "conyuge"}))

        return {
            "success": True,
            "persona_id": persona.persona_pk,
            "conyuge_id": conyuge.propietario_vivienda_pk,
            "vivienda_id": vivienda_id,
            "mensaje": "Cónyuge registrado exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{vivienda_id}", response_model=dict)
def obtener_propietarios_vivienda(
    vivienda_id: int,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Obtiene todos los propietarios de una vivienda
    """
    try:
        vivienda = db.query(Vivienda).filter(Vivienda.vivienda_pk == vivienda_id).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        propietarios = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.eliminado == False
        ).all()
        
        propietarios_data = []
        conyuge_data = None
        for prop in propietarios:
            persona = prop.persona
            item = {
                "propietario_id": prop.propietario_vivienda_pk,
                "persona_id": persona.persona_pk,
                "nombres": f"{persona.nombres} {persona.apellidos}",
                "identificacion": persona.identificacion,
                "correo": persona.correo,
                "celular": persona.celular
            }
            propietarios_data.append(item)
            if prop.tipo_propietario == "conyuge" and not conyuge_data:
                conyuge_data = item

        return {
            "vivienda_id": vivienda_id,
            "total_propietarios": len(propietarios_data),
            "propietarios": propietarios_data,
            "conyuge": conyuge_data,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{propietario_id}", response_model=dict)
def eliminar_propietario(
    propietario_id: int,
    request: EliminarPropietarioRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Elimina un propietario (soft delete)
    """
    try:
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id
        ).first()
        
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        email = usuario.get("email", "") or "user_system"
        propietario.eliminado = True
        propietario.estado = "inactivo"
        propietario.motivo_eliminado = request.motivo
        propietario.fecha_actualizado = ahora_sin_tz()
        propietario.usuario_actualizado = email
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Propietario eliminado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{propietario_id}", response_model=dict)
def actualizar_propietario(
    propietario_id: int,
    request: ActualizarPropietarioRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Actualiza información del propietario
    RF-P03: Permite actualizar email, celular y dirección
    Campos NO modificables: identificación, nombres, apellidos, manzana, villa
    """
    try:
        email = usuario.get("email", "") or "user_system"
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id,
            PropietarioVivienda.eliminado == False
        ).first()
        
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        # Obtener persona asociada
        persona = db.query(Persona).filter(
            Persona.persona_pk == propietario.persona_propietario_fk
        ).first()
        
        # Actualizar solo campos permitidos
        if request.correo_nuevo:
            # Validar formato email básico
            if "@" not in request.correo_nuevo or "." not in request.correo_nuevo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de email inválido"
                )
            persona.correo = request.correo_nuevo
        
        if request.celular_nuevo:
            # Validar celular
            if len(request.celular_nuevo) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Celular inválido"
                )
            persona.celular = request.celular_nuevo
        
        if request.direccion_alternativa:
            persona.direccion_alternativa = request.direccion_alternativa
        
        persona.fecha_actualizado = ahora_sin_tz()
        persona.usuario_actualizado = email
        
        db.commit()

        registrar_bitacora(db, usuario, "propietario_vivienda",
                           propietario_id, "actualizar",
                           f"Propietario {propietario_id} actualizado")

        return {
            "success": True,
            "mensaje": "Información del propietario actualizada correctamente",
            "propietario_id": propietario_id,
            "campos_actualizados": {
                "email": request.correo_nuevo is not None,
                "celular": request.celular_nuevo is not None,
                "direccion": request.direccion_alternativa is not None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{propietario_id}/baja", response_model=dict)
def baja_propietario(
    propietario_id: int,
    request: BajaRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Baja de propietario (cambiar estado a inactivo)
    RF-P04: Desactiva propietario e inactiva también al cónyuge si existe
    """
    try:
        email = usuario.get("email", "") or "user_system"
        if not request.motivo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El motivo de baja es obligatorio"
            )
        
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id,
            PropietarioVivienda.eliminado == False
        ).first()
        
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        if propietario.estado == "inactivo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El propietario ya se encuentra inactivo"
            )
        
        # Cambiar propietario a inactivo
        propietario.estado = "inactivo"
        propietario.fecha_actualizado = ahora_sin_tz()
        propietario.usuario_actualizado = email
        propietario.motivo_eliminado = request.motivo
        
        # Obtener y desactivar cónyuge si existe
        conyuge_procesado = False
        
        # Buscar cónyuge directo por tipo_propietario
        conyuge_prop = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == propietario.vivienda_propiedad_fk,
            PropietarioVivienda.tipo_propietario == "conyuge",
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).first()
        
        if conyuge_prop:
            conyuge_prop.estado = "inactivo"
            conyuge_prop.fecha_actualizado = ahora_sin_tz()
            conyuge_prop.usuario_actualizado = email
            conyuge_prop.motivo_eliminado = f"Baja asociada a propietario titular: {request.motivo}"
            conyuge_procesado = True
        
        db.commit()

        registrar_bitacora(db, usuario, "propietario_vivienda",
                           propietario_id, "baja",
                           f"Propietario {propietario_id} dado de baja. Motivo: {request.motivo}",
                           valor_anterior="activo", valor_nuevo="inactivo")

        return {
            "mensaje": "Propietario dado de baja correctamente",
            "propietario_id": propietario_id,
            "conyuge_procesado": conyuge_procesado,
            "motivo": request.motivo
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{propietario_id}/desbloquear", response_model=dict)
def desbloquear_propietario(
    propietario_id: int,
    request: dict,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Reactiva un propietario que fue dado de baja. Tambien reactiva al conyuge si existe."""
    email = usuario.get("email", "") or "user_system"
    motivo = request.get("motivo")
    if not motivo or not motivo.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error: el motivo de desbloqueo es obligatorio",
        )

    propietario = db.query(PropietarioVivienda).filter(
        PropietarioVivienda.propietario_vivienda_pk == propietario_id,
        PropietarioVivienda.eliminado == False,
    ).first()
    if not propietario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propietario no encontrado",
        )
    if propietario.estado == "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Advertencia: el propietario ya se encuentra activo",
        )

    propietario.estado = "activo"
    propietario.fecha_actualizado = datetime.utcnow()
    propietario.usuario_actualizado = email

    conyuge = db.query(PropietarioVivienda).filter(
        PropietarioVivienda.vivienda_propiedad_fk == propietario.vivienda_propiedad_fk,
        PropietarioVivienda.tipo_propietario == "conyuge",
        PropietarioVivienda.estado == "inactivo",
        PropietarioVivienda.eliminado == False,
    ).first()
    conyuge_reactivado = False
    if conyuge:
        conyuge.estado = "activo"
        conyuge.fecha_actualizado = datetime.utcnow()
        conyuge.usuario_actualizado = email
        conyuge_reactivado = True

    db.commit()

    registrar_bitacora(db, usuario, "propietario_vivienda", propietario_id,
                       "desbloquear",
                       f"Propietario {propietario_id} desbloqueado. Motivo: {motivo}",
                       valor_anterior="inactivo", valor_nuevo="activo")

    respuesta = "Propietario desbloqueado correctamente"
    if conyuge_reactivado:
        respuesta += " (conyuge tambien reactivado)"
    return {
        "mensaje": respuesta,
        "propietario_id": propietario_id,
        "conyuge_reactivado": conyuge_reactivado,
    }


# DEPRECADO: usar POST /api/v1/viviendas/cambio-propietario
@router.post("/cambio-propiedad", response_model=dict)
def cambio_propietario_vivienda(
    request: CambioPropiedadRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    [DEPRECADO] Cambio de propietario de vivienda.
    Usar POST /api/v1/viviendas/cambio-propietario en su lugar.
    """
    import warnings
    warnings.warn(
        "POST /propietarios/cambio-propiedad esta deprecado. "
        "Usar POST /viviendas/cambio-propietario",
        DeprecationWarning,
    )
    raise HTTPException(
        status_code=410,
        detail="Endpoint deprecado. Usar POST /api/v1/viviendas/cambio-propietario",
    )


@router.get("/manzana-villa/{manzana}/{villa}", response_model=dict)
def obtener_propietarios_por_ubicacion(
    manzana: str,
    villa: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Obtiene todos los propietarios de una vivienda por manzana y villa
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
        
        # Obtener propietarios activos
        propietarios = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda.vivienda_pk,
            # PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).all()
        
        propietarios_data = []
        conyuge_data = None
        for propietario in propietarios:
            persona = propietario.persona
            item = {
                "propietario_id": propietario.propietario_vivienda_pk,
                "persona_id": persona.persona_pk,
                "identificacion": persona.identificacion,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "correo": persona.correo,
                "celular": persona.celular,
                "estado": propietario.estado,
                "tipo_propietario": propietario.tipo_propietario
            }
            propietarios_data.append(item)
            if propietario.tipo_propietario == "conyuge" and not conyuge_data:
                conyuge_data = item

        return {
            "vivienda_id": vivienda.vivienda_pk,
            "manzana": vivienda.manzana,
            "villa": vivienda.villa,
            "total_propietarios": len(propietarios_data),
            "propietarios": propietarios_data,
            "conyuge": conyuge_data,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS DE CONYUGES
# ═══════════════════════════════════════════════════════════════


class ActualizarConyugeRequest(BaseModel):
    correo: str = None
    celular: str = None


@router.put("/conyuges/{conyuge_id}", response_model=dict)
def actualizar_conyuge(
    conyuge_id: int,
    request: ActualizarConyugeRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Actualiza correo y celular de un conyuge."""
    email = usuario.get("email", "") or "user_system"
    prop = db.query(PropietarioVivienda).filter(
        PropietarioVivienda.propietario_vivienda_pk == conyuge_id,
        PropietarioVivienda.tipo_propietario == "conyuge",
        PropietarioVivienda.eliminado == False,
    ).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Conyuge no encontrado")
    persona = db.query(Persona).filter(
        Persona.persona_pk == prop.persona_propietario_fk
    ).first()
    if request.correo:
        persona.correo = request.correo
    if request.celular:
        persona.celular = request.celular
    persona.fecha_actualizado = ahora_sin_tz()
    persona.usuario_actualizado = email
    db.commit()
    return {"success": True, "mensaje": "Conyuge actualizado correctamente"}


@router.delete("/conyuges/{conyuge_id}", response_model=dict)
def eliminar_conyuge(
    conyuge_id: int,
    request: EliminarPropietarioRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Elimina (soft delete) un conyuge."""
    prop = db.query(PropietarioVivienda).filter(
        PropietarioVivienda.propietario_vivienda_pk == conyuge_id,
        PropietarioVivienda.tipo_propietario == "conyuge",
        PropietarioVivienda.eliminado == False,
    ).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Conyuge no encontrado")
    email = usuario.get("email", "") or "user_system"
    prop.eliminado = True
    prop.motivo_eliminado = request.motivo
    prop.estado = "inactivo"
    prop.fecha_actualizado = ahora_sin_tz()
    prop.usuario_actualizado = email
    db.commit()
    return {"success": True, "mensaje": "Conyuge eliminado correctamente"}
