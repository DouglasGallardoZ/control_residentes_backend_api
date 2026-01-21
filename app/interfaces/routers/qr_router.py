from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db, SessionLocal
from app.interfaces.schemas.schemas import (
    QRGenerarPropio, QRGenerarVisita, QRResponse, AccesoValidarRequest, QRListResponse, QRPaginatedResponse,
    VisitaResponse, ViviendaVisitasResponse
)
from app.infrastructure.db.models import QR as QRModel, Cuenta, Acceso as AccesoModel, ResidenteVivienda, Persona, Visita as VisitaModel, MiembroVivienda, Vivienda
from datetime import datetime
from app.infrastructure.utils.time_utils import ahora_sin_tz, timedelta
from app.config import get_settings
import secrets
import string

router = APIRouter(prefix="/api/v1/qr", tags=["QR"])
settings = get_settings()


def generar_token() -> str:
    """Genera un token QR seguro de longitud configurable"""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(settings.QR_TOKEN_LENGTH))


@router.post("/generar-propio", response_model=dict)
def generar_qr_propio(
    request: QRGenerarPropio,
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Genera un código QR propio para residente o miembro
    RF-Q01
    """
    try:
        # Obtener cuenta del usuario
        cuenta = db.query(Cuenta).filter(Cuenta.persona_titular_fk == usuario_id).first()
        if not cuenta or cuenta.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario no autorizado para generar QR"
            )
        
        # Validar fecha y hora
        hora_inicio = datetime.strptime(request.hora_inicio, "%H:%M").time()
        fecha_acceso = request.fecha_acceso
        dt_inicio = datetime.combine(fecha_acceso, hora_inicio)
        
        if dt_inicio < ahora_sin_tz():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha y hora deben ser futuras"
            )
        
        if request.duracion_horas <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La duración debe ser mayor a 0 horas"
            )
        
        # Obtener vivienda: verificar si es residente o miembro de familia
        vivienda_id = None
        
        # Verificar si es residente
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == cuenta.persona_titular_fk,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).first()
        
        if residente:
            vivienda_id = residente.vivienda_reside_fk
        else:
            # Verificar si es miembro de familia
            miembro = db.query(MiembroVivienda).filter(
                MiembroVivienda.persona_miembro_fk == cuenta.persona_titular_fk,
                MiembroVivienda.estado == "activo",
                MiembroVivienda.eliminado == False
            ).first()
            
            if miembro:
                vivienda_id = miembro.vivienda_familia_fk
        
        if not vivienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario no tiene una vivienda asignada como residente o miembro de familia activo"
            )
        
        # Generar token
        token = generar_token()
        hora_fin = dt_inicio + timedelta(hours=request.duracion_horas)
        
        # Crear QR
        qr = QRModel(
            cuenta_autoriza_fk=cuenta.cuenta_pk,
            vivienda_visita_fk=vivienda_id,
            hora_inicio_vigencia=dt_inicio,
            hora_fin_vigencia=hora_fin,
            token=token,
            estado="vigente",
            usuario_creado=request.usuario_creado
        )
        
        db.add(qr)
        db.commit()
        db.refresh(qr)
        
        return {
            "id": qr.qr_pk,
            "token": token,
            "hora_inicio": dt_inicio.isoformat(),
            "hora_fin": hora_fin.isoformat(),
            "estado": "vigente",
            "mensaje": "Código QR generado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generar-visita", response_model=dict)
def generar_qr_visita(
    request: QRGenerarVisita,
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Genera un código QR para autorizar visita
    RF-Q02
    """
    try:
        # Obtener cuenta del usuario
        cuenta = db.query(Cuenta).filter(Cuenta.persona_titular_fk == usuario_id).first()
        if not cuenta or cuenta.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario no autorizado para generar QR"
            )
        
        # Validar datos de visita
        if not request.visita_identificacion or not request.visita_nombres or not request.visita_apellidos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los datos de la visita son obligatorios"
            )
        
        # Validar fecha y hora
        hora_inicio = datetime.strptime(request.hora_inicio, "%H:%M").time()
        fecha_acceso = request.fecha_acceso
        dt_inicio = datetime.combine(fecha_acceso, hora_inicio)
        
        if dt_inicio < ahora_sin_tz():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha y hora deben ser futuras"
            )
        
        if request.duracion_horas <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La duración debe ser mayor a 0 horas"
            )
        
        # Obtener vivienda: verificar si es residente o miembro de familia
        vivienda_id = None
        
        # Verificar si es residente
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == cuenta.persona_titular_fk,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).first()
        
        if residente:
            vivienda_id = residente.vivienda_reside_fk
        else:
            # Verificar si es miembro de familia
            miembro = db.query(MiembroVivienda).filter(
                MiembroVivienda.persona_miembro_fk == cuenta.persona_titular_fk,
                MiembroVivienda.estado == "activo",
                MiembroVivienda.eliminado == False
            ).first()
            
            if miembro:
                vivienda_id = miembro.vivienda_familia_fk
        
        if not vivienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario no tiene una vivienda asignada como residente o miembro de familia activo"
            )
        
        # Verificar si ya existe un visitante con la misma identificación en esta vivienda
        visita_existente = db.query(VisitaModel).filter(
            VisitaModel.vivienda_visita_fk == vivienda_id,
            VisitaModel.identificacion == request.visita_identificacion,
            VisitaModel.eliminado == False
        ).first()
        
        if visita_existente:
            # Reutilizar el registro existente
            visita_id = visita_existente.visita_pk
        else:
            # Crear nuevo registro de visita en tabla visita
            visita = VisitaModel(
                vivienda_visita_fk=vivienda_id,
                identificacion=request.visita_identificacion,
                nombres=request.visita_nombres,
                apellidos=request.visita_apellidos,
                usuario_creado=request.usuario_creado
            )
            
            db.add(visita)
            db.flush()  # Obtener el ID de la visita sin hacer commit
            visita_id = visita.visita_pk
        
        # Generar token
        token = generar_token()
        hora_fin = dt_inicio + timedelta(hours=request.duracion_horas)
        
        # Crear QR
        qr = QRModel(
            cuenta_autoriza_fk=cuenta.cuenta_pk,
            vivienda_visita_fk=vivienda_id,
            visita_ingreso_fk=visita_id,
            hora_inicio_vigencia=dt_inicio,
            hora_fin_vigencia=hora_fin,
            token=token,
            estado="vigente",
            usuario_creado=request.usuario_creado
        )
        
        db.add(qr)
        db.commit()
        db.refresh(qr)
        
        # Determinar si la visita fue nueva o reutilizada
        mensaje_visita = "Visitante reutilizado" if visita_existente else "Nuevo visitante registrado"
        
        return {
            "id": qr.qr_pk,
            "token": token,
            "hora_inicio": dt_inicio.isoformat(),
            "hora_fin": hora_fin.isoformat(),
            "estado": "vigente",
            "visita_id": visita_id,
            "mensaje": f"Código QR para visita generado correctamente - {mensaje_visita}",
            "es_visitante_nuevo": visita_existente is None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{qr_id}", response_model=QRResponse)
def obtener_qr(qr_id: int, db: Session = Depends(get_db)):
    """
    Obtiene información de un código QR
    """
    qr = db.query(QRModel).filter(QRModel.qr_pk == qr_id).first()
    if not qr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR no encontrado"
        )
    return qr


@router.get("/cuenta/generados", response_model=QRPaginatedResponse)
def listar_qr_por_cuenta(
    usuario_id: int,
    page: int = Query(settings.PAGINATION_DEFAULT_PAGE, ge=1),
    page_size: int = Query(settings.PAGINATION_DEFAULT_PAGE_SIZE, ge=1, le=settings.PAGINATION_MAX_PAGE_SIZE),
    tipo_ingreso: str = None,  # "propio", "visita", o None para todos
    db: Session = Depends(get_db)
):
    """
    Lista QRs generados por la cuenta del usuario autenticado (paginado)
    Parámetros:
    - page: número de página (default 1)
    - page_size: cantidad de items por página (default 10, máximo 100)
    - tipo_ingreso: filtrar por tipo ("propio", "visita", o None para todos)
    Retorna: datos paginados con token, estado, tipo de ingreso, fechas de vigencia
    RF-Q03
    """
    try:
        # Validar parámetros de paginación
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100  # Máximo 100 items por página
        
        # Validar tipo_ingreso
        if tipo_ingreso and tipo_ingreso not in ["propio", "visita"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tipo_ingreso debe ser 'propio', 'visita' o vacío"
            )
        
        # Obtener cuenta del usuario
        cuenta = db.query(Cuenta).filter(Cuenta.persona_titular_fk == usuario_id).first()
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario no autorizado"
            )
        
        # Construir query base
        query_base = db.query(QRModel).filter(
            QRModel.cuenta_autoriza_fk == cuenta.cuenta_pk
        )
        
        # Aplicar filtro de tipo_ingreso si se proporciona
        if tipo_ingreso == "propio":
            query_base = query_base.filter(QRModel.visita_ingreso_fk == None)
        elif tipo_ingreso == "visita":
            query_base = query_base.filter(QRModel.visita_ingreso_fk != None)
        
        # Obtener total de QRs con filtro aplicado
        total = query_base.count()
        
        # Calcular offset y total de páginas
        offset = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        
        # Obtener QRs paginados con filtro
        qrs = query_base.order_by(QRModel.fecha_creado.desc()).offset(offset).limit(page_size).all()
        
        # Transformar QRs para incluir tipo de ingreso
        data = []
        for qr in qrs:
            tipo_ingreso_calc = "visita" if qr.visita_ingreso_fk is not None else "propio"
            data.append(QRListResponse(
                qr_pk=qr.qr_pk,
                token=qr.token,
                estado=qr.estado,
                tipo_ingreso=tipo_ingreso_calc,
                hora_inicio_vigencia=qr.hora_inicio_vigencia,
                hora_fin_vigencia=qr.hora_fin_vigencia,
                fecha_creado=qr.fecha_creado
            ))
        
        return QRPaginatedResponse(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/visitantes/{persona_id}", response_model=ViviendaVisitasResponse)
def obtener_visitantes_vivienda(
    persona_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de visitantes registrados para la vivienda del usuario
    El usuario puede ser residente o miembro de familia
    Retorna identificación, nombres, apellidos y fecha de registro
    para que puedan ser reutilizados al generar QRs de visita
    
    RF-Q04: Consultar visitantes disponibles para reutilización
    """
    try:
        # Obtener persona
        persona = db.query(Persona).filter(Persona.persona_pk == persona_id).first()
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona no encontrada"
            )
        
        # Determinar vivienda y rol del usuario
        vivienda_id = None
        
        # Verificar si es residente
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == persona_id,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).first()
        
        if residente:
            vivienda_id = residente.vivienda_reside_fk
        else:
            # Verificar si es miembro de familia
            miembro = db.query(MiembroVivienda).filter(
                MiembroVivienda.persona_miembro_fk == persona_id,
                MiembroVivienda.estado == "activo",
                MiembroVivienda.eliminado == False
            ).first()
            
            if miembro:
                vivienda_id = miembro.vivienda_familia_fk
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no es residente ni miembro de familia activo"
                )
        
        # Obtener vivienda
        vivienda = db.query(Vivienda).filter(Vivienda.vivienda_pk == vivienda_id).first()
        
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vivienda no encontrada"
            )
        
        # Obtener visitantes de la vivienda
        visitantes = db.query(VisitaModel).filter(
            VisitaModel.vivienda_visita_fk == vivienda_id,
            VisitaModel.eliminado == False
        ).order_by(VisitaModel.fecha_creado.desc()).all()
        
        # Transformar a VisitaResponse
        visitantes_response = [
            VisitaResponse(
                visita_id=v.visita_pk,
                identificacion=v.identificacion,
                nombres=v.nombres,
                apellidos=v.apellidos,
                fecha_creado=v.fecha_creado
            )
            for v in visitantes
        ]
        
        return ViviendaVisitasResponse(
            vivienda_id=vivienda.vivienda_pk,
            manzana=vivienda.manzana,
            villa=vivienda.villa,
            visitantes=visitantes_response,
            total=len(visitantes_response)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
