"""
Contenedor de inyeccion de dependencias para la aplicacion.

Centraliza la creacion y configuracion de adaptadores y servicios,
permitiendo cambiar implementaciones sin modificar la logica de negocio.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.database import get_db
from app.infrastructure.firestore.client import FirestoreClient
from app.infrastructure.notifications.fcm_client import FCMClient

from app.infrastructure.adapters.notificacion_repositorio_impl import (
    NotificacionRepositorioImpl,
)
from app.infrastructure.adapters.fcm_token_repositorio_impl import (
    FcmTokenRepositorioImpl,
)
from app.infrastructure.adapters.notificacion_push_impl import (
    NotificacionPushImpl,
)
from app.infrastructure.adapters.lectura_notificacion_impl import (
    LecturaNotificacionImpl,
)

from app.application.services.notificacion_service import NotificacionService
from app.application.services.bitacora_service import BitacoraService


def get_notificacion_repositorio(db: Session = Depends(get_db)) -> NotificacionRepositorioImpl:
    return NotificacionRepositorioImpl(db)


def get_bitacora_service(db: Session = Depends(get_db)) -> BitacoraService:
    return BitacoraService(db)


def get_fcm_token_repositorio() -> FcmTokenRepositorioImpl:
    return FcmTokenRepositorioImpl(FirestoreClient())


def get_notificacion_push() -> NotificacionPushImpl:
    return NotificacionPushImpl(FCMClient())


def get_lectura_notificacion() -> LecturaNotificacionImpl:
    return LecturaNotificacionImpl(FirestoreClient())


def get_notificacion_service(
    db: Session = Depends(get_db),
) -> NotificacionService:
    return NotificacionService(
        notificacion_repo=get_notificacion_repositorio(db),
        fcm_token_repo=get_fcm_token_repositorio(),
        push_service=get_notificacion_push(),
        lectura_service=get_lectura_notificacion(),
    )
