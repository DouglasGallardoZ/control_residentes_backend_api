from fastapi import APIRouter, Depends, Query, HTTPException, Path
from typing import Optional
from sqlalchemy.orm import Session

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import NotificacionDestino
from app.infrastructure.dependencies import get_notificacion_service
from app.infrastructure.security.auth import obtener_usuario_con_rol, requerir_rol
from app.application.services.notificacion_service import NotificacionService
from app.application.services.firestore_sync_service import FirestoreSyncService
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
    busqueda: Optional[str] = Query(None),
    usuario: dict = Depends(requerir_rol("admin")),
    servicio: NotificacionService = Depends(get_notificacion_service),
    db: Session = Depends(get_db),
):
    """Lista posibles destinatarios para envio de notificaciones (admin)"""
    persona_id = usuario.get("persona_id")
    if not persona_id:
        raise HTTPException(status_code=400, detail="Usuario sin persona asociada")

    destinatarios = await servicio.obtener_destinatarios(
        busqueda=busqueda, db=db
    )
    return destinatarios


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
