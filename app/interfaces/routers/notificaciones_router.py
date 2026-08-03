from fastapi import APIRouter, Depends, Query, HTTPException, Path
from typing import Optional, List
from sqlalchemy.orm import Session

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import NotificacionDestino
from app.infrastructure.dependencies import get_notificacion_service
from app.infrastructure.security.auth import obtener_usuario_con_rol, requerir_rol
from app.application.services.notificacion_service import NotificacionService
from app.application.services.firestore_sync_service import FirestoreSyncService
from app.infrastructure.utils.auditoria_helpers import registrar_bitacora
from app.domain.entities.notificacion_entities import SolicitudNotificacion
from datetime import datetime
from app.interfaces.schemas.notificaciones_schemas import (
    TokenFCMRequest,
    EliminarTokenFCMRequest,
    SolicitudNotificacionRequest,
    NotificacionPaginadaResponse,
    ConteoNoLeidasResponse,
    RespuestaEnvioNotificacionResponse,
    DestinatarioResponse,
    MensajeResponse,
)

router = APIRouter(
    prefix="/api/v1/notificaciones",
    tags=["Notificaciones"],
)


# ─── TOKENS FCM ────────────────────────────────────────────


@router.post("/token", response_model=MensajeResponse)
async def registrar_token_fcm(
    request: TokenFCMRequest,
    usuario: dict = Depends(obtener_usuario_con_rol),
    servicio: NotificacionService = Depends(get_notificacion_service),
):
    """Registra el token FCM de un dispositivo para recibir push notifications"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    await servicio.registrar_token_dispositivo(
        persona_id, request.token_fcm, request.plataforma
    )
    return {"mensaje": "Token FCM registrado exitosamente"}


@router.delete("/token", response_model=MensajeResponse)
async def eliminar_token_fcm(
    request: EliminarTokenFCMRequest,
    usuario: dict = Depends(obtener_usuario_con_rol),
    servicio: NotificacionService = Depends(get_notificacion_service),
):
    """Elimina un token FCM (desvincula dispositivo)"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    await servicio.eliminar_token_dispositivo(persona_id, request.token_fcm)
    return {"mensaje": "Token FCM eliminado exitosamente"}


# ─── NOTIFICACIONES (USUARIO) ──────────────────────────────


@router.get("", response_model=NotificacionPaginadaResponse)
async def listar_notificaciones(
    pagina: int = Query(1, ge=1),
    tamano_pagina: int = Query(20, ge=1, le=100),
    usuario: dict = Depends(obtener_usuario_con_rol),
    servicio: NotificacionService = Depends(get_notificacion_service),
):
    """Lista las notificaciones del usuario autenticado con paginacion"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    resultado = await servicio.obtener_notificaciones(
        persona_id, pagina, tamano_pagina
    )
    return resultado


@router.get("/no-leidas", response_model=ConteoNoLeidasResponse)
async def contar_no_leidas(
    usuario: dict = Depends(obtener_usuario_con_rol),
    servicio: NotificacionService = Depends(get_notificacion_service),
):
    """Obtiene el contador de notificaciones no leidas del usuario"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    resultado = await servicio.obtener_notificaciones(
        persona_id, pagina=1, tamano_pagina=1
    )
    return {"no_leidas": resultado.get("no_leidas", 0)}


@router.put("/{notificacion_id}/leer", response_model=MensajeResponse)
async def marcar_como_leida(
    notificacion_id: int = Path(..., ge=1),
    usuario: dict = Depends(obtener_usuario_con_rol),
    db: Session = Depends(get_db),
):
    """Marca una notificacion como leida en PostgreSQL y Firestore"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    destino = (
        db.query(NotificacionDestino)
        .filter(
            NotificacionDestino.notificacion_envio_fk == notificacion_id,
            NotificacionDestino.persona_receptor_fk == persona_id,
            NotificacionDestino.eliminado == False,
        )
        .first()
    )
    if not destino:
        raise HTTPException(
            status_code=404, detail="Notificacion no encontrada"
        )

    destino.entregada = True
    destino.hora_entregado = datetime.now()
    destino.fecha_actualizado = datetime.now()
    db.commit()

    try:
        firestore_sync = FirestoreSyncService()
        await firestore_sync.marcar_como_leida(persona_id, notificacion_id)
    except Exception as e:
        print(f"Error sincronizando Firestore: {e}")

    return {"mensaje": "Notificacion marcada como leida"}


@router.put("/leer-todas", response_model=MensajeResponse)
async def marcar_todas_como_leidas(
    usuario: dict = Depends(obtener_usuario_con_rol),
    db: Session = Depends(get_db),
):
    """Marca todas las notificaciones del usuario como leidas"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    destinos = (
        db.query(NotificacionDestino)
        .filter(
            NotificacionDestino.persona_receptor_fk == persona_id,
            NotificacionDestino.eliminado == False,
        )
        .all()
    )
    for destino in destinos:
        destino.entregada = True
        destino.hora_entregado = datetime.now()
        destino.fecha_actualizado = datetime.now()
    db.commit()

    try:
        firestore_sync = FirestoreSyncService()
        await firestore_sync.marcar_todas_como_leidas(persona_id)
    except Exception as e:
        print(f"Error sincronizando Firestore: {e}")

    return {"mensaje": "Todas las notificaciones marcadas como leidas"}


# ─── ADMIN ─────────────────────────────────────────────────


@router.post(
    "/enviar", response_model=RespuestaEnvioNotificacionResponse
)
async def enviar_notificacion(
    request: SolicitudNotificacionRequest,
    usuario: dict = Depends(requerir_rol("admin")),
    servicio: NotificacionService = Depends(get_notificacion_service),
    db: Session = Depends(get_db),
):
    """Envia una notificacion push a residentes o miembros (admin)"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    solicitud = SolicitudNotificacion(
        titulo=request.titulo,
        mensaje=request.mensaje,
        prioridad=request.prioridad,
        categoria=request.categoria,
        persona_emisor_id=persona_id,
        destinatario_ids=request.destinatario_ids or [],
        enviar_a_todos=request.enviar_a_todos,
        ruta_accion=request.ruta_accion,
        datos_accion=request.datos_accion,
    )

    try:
        resultado = await servicio.enviar_notificacion(solicitud)
        db.commit()
        registrar_bitacora(db, usuario, "notificacion",
                           resultado.notificacion_id, "enviar",
                           f"Notificacion a {resultado.total_destinatarios} destinatarios")
        return resultado
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar notificacion: {str(e)}",
        )


@router.get(
    "/destinatarios", response_model=list[DestinatarioResponse]
)
async def listar_destinatarios(
    busqueda: Optional[str] = Query(
        None, description="Buscar por nombre o identificacion"
    ),
    manzana: Optional[str] = Query(
        None, description="Filtrar por manzana (ej: A, B, C)"
    ),
    villa: Optional[str] = Query(
        None, description="Filtrar por villa (requiere manzana)"
    ),
    tipo: Optional[str] = Query(
        None, description="Filtrar por tipo: residente, propietario, miembro_familia"
    ),
    usuario: dict = Depends(requerir_rol("admin")),
    db: Session = Depends(get_db),
):
    """
    Lista posibles destinatarios para envio de notificaciones.

    Filtros:
    - busqueda: Busca por nombre, apellido o identificacion
    - manzana: Filtra residentes de una manzana especifica
    - villa: Filtra por villa (requiere manzana)
    - manzana+villa: Filtra residentes de una vivienda especifica
    - sin filtros: Retorna todos los residentes y miembros
    """
    destinatarios = await _obtener_destinatarios(
        db, busqueda, manzana, villa, tipo
    )
    return destinatarios


@router.get(
    "/manzanas", response_model=List[str]
)
async def listar_manzanas(
    usuario: dict = Depends(requerir_rol("admin")),
    db: Session = Depends(get_db),
):
    """Lista las manzanas disponibles con residentes activos"""
    from app.infrastructure.db.models import Vivienda, ResidenteVivienda

    manzanas = (
        db.query(Vivienda.manzana)
        .join(
            ResidenteVivienda,
            Vivienda.vivienda_pk == ResidenteVivienda.vivienda_reside_fk,
        )
        .filter(
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False,
            Vivienda.estado == "activo",
        )
        .distinct()
        .order_by(Vivienda.manzana)
        .all()
    )
    return sorted(set(m[0] for m in manzanas if m[0]))


# ─── HELPERS ─────────────────────────────────────────────────


async def _obtener_destinatarios(
    db: Session,
    busqueda: Optional[str] = None,
    manzana: Optional[str] = None,
    villa: Optional[str] = None,
    tipo: Optional[str] = None,
) -> list:
    """Obtiene destinatarios con filtros opcionales por ubicacion"""
    from app.infrastructure.db.models import (
        Persona, ResidenteVivienda, MiembroVivienda, PropietarioVivienda,
        Vivienda,
    )

    query_residentes = (
        db.query(
            Persona.persona_pk.label("persona_id"),
            Persona.nombres,
            Persona.apellidos,
            Persona.identificacion,
            Vivienda.manzana,
            Vivienda.villa,
        )
        .join(
            ResidenteVivienda,
            Persona.persona_pk == ResidenteVivienda.persona_residente_fk,
        )
        .join(
            Vivienda,
            ResidenteVivienda.vivienda_reside_fk == Vivienda.vivienda_pk,
        )
        .filter(
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False,
            Persona.eliminado == False,
        )
    )

    query_propietarios = (
        db.query(
            Persona.persona_pk.label("persona_id"),
            Persona.nombres,
            Persona.apellidos,
            Persona.identificacion,
            Vivienda.manzana,
            Vivienda.villa,
        )
        .join(
            PropietarioVivienda,
            Persona.persona_pk == PropietarioVivienda.persona_propietario_fk,
        )
        .join(
            Vivienda,
            PropietarioVivienda.vivienda_propiedad_fk == Vivienda.vivienda_pk,
        )
        .filter(
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False,
            Persona.eliminado == False,
        )
    )

    query_miembros = (
        db.query(
            Persona.persona_pk.label("persona_id"),
            Persona.nombres,
            Persona.apellidos,
            Persona.identificacion,
            Vivienda.manzana,
            Vivienda.villa,
        )
        .join(
            MiembroVivienda,
            Persona.persona_pk == MiembroVivienda.persona_miembro_fk,
        )
        .join(
            Vivienda,
            MiembroVivienda.vivienda_familia_fk == Vivienda.vivienda_pk,
        )
        .filter(
            MiembroVivienda.estado == "activo",
            MiembroVivienda.eliminado == False,
            Persona.eliminado == False,
        )
    )

    if manzana:
        mz = manzana.strip().upper()
        query_residentes = query_residentes.filter(Vivienda.manzana == mz)
        query_propietarios = query_propietarios.filter(Vivienda.manzana == mz)
        query_miembros = query_miembros.filter(Vivienda.manzana == mz)

    if villa and manzana:
        query_residentes = query_residentes.filter(Vivienda.villa == villa.strip())
        query_propietarios = query_propietarios.filter(Vivienda.villa == villa.strip())
        query_miembros = query_miembros.filter(Vivienda.villa == villa.strip())

    if busqueda:
        termino = f"%{busqueda.strip()}%"
        filtro = (
            Persona.nombres.ilike(termino)
            | Persona.apellidos.ilike(termino)
            | Persona.identificacion.ilike(termino)
        )
        query_residentes = query_residentes.filter(filtro)
        query_propietarios = query_propietarios.filter(filtro)
        query_miembros = query_miembros.filter(filtro)

    resultado = []
    ids_vistos = set()

    if tipo is None or tipo == "residente":
        for r in query_residentes.all():
            if r.persona_id not in ids_vistos:
                ids_vistos.add(r.persona_id)
                resultado.append({
                    "persona_id": r.persona_id,
                    "nombre_completo": f"{r.nombres} {r.apellidos}",
                    "identificacion": r.identificacion,
                    "manzana": r.manzana,
                    "villa": r.villa,
                    "tipo": "residente",
                })

    if tipo is None or tipo == "propietario":
        for p in query_propietarios.all():
            if p.persona_id not in ids_vistos:
                ids_vistos.add(p.persona_id)
                resultado.append({
                    "persona_id": p.persona_id,
                    "nombre_completo": f"{p.nombres} {p.apellidos}",
                    "identificacion": p.identificacion,
                    "manzana": p.manzana,
                    "villa": p.villa,
                    "tipo": "propietario",
                })

    if tipo is None or tipo == "miembro_familia":
        for m in query_miembros.all():
            if m.persona_id not in ids_vistos:
                ids_vistos.add(m.persona_id)
                resultado.append({
                    "persona_id": m.persona_id,
                    "nombre_completo": f"{m.nombres} {m.apellidos}",
                    "identificacion": m.identificacion,
                    "manzana": m.manzana,
                    "villa": m.villa,
                    "tipo": "miembro_familia",
                })

    return sorted(
        resultado,
        key=lambda x: (
            (x.get("manzana") or ""),
            (x.get("villa") or ""),
            x.get("nombre_completo", ""),
        ),
    )


@router.delete(
    "/{notificacion_id}", response_model=MensajeResponse
)
async def eliminar_notificacion(
    notificacion_id: int = Path(..., ge=1),
    usuario: dict = Depends(obtener_usuario_con_rol),
    db: Session = Depends(get_db),
):
    """Elimina (soft delete) una notificacion del usuario"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    destino = (
        db.query(NotificacionDestino)
        .filter(
            NotificacionDestino.notificacion_envio_fk == notificacion_id,
            NotificacionDestino.persona_receptor_fk == persona_id,
            NotificacionDestino.eliminado == False,
        )
        .first()
    )

    if not destino:
        raise HTTPException(
            status_code=404, detail="Notificacion no encontrada"
        )

    destino.eliminado = True
    db.commit()

    return {"mensaje": "Notificacion eliminada"}
