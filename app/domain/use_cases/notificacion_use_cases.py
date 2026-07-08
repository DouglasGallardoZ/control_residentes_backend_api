from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.notificacion_entities import (
    SolicitudNotificacion,
    RespuestaEnvioNotificacion,
    NotificacionPersona,
    DestinatarioInfo,
)


class EnviarNotificacionUseCase(ABC):

    @abstractmethod
    async def ejecutar(
        self, solicitud: SolicitudNotificacion
    ) -> RespuestaEnvioNotificacion:
        """Envia una notificacion a los destinatarios especificados"""
        ...


class ObtenerNotificacionesUseCase(ABC):

    @abstractmethod
    async def ejecutar(
        self,
        persona_id: int,
        pagina: int = 1,
        tamano_pagina: int = 20,
    ) -> dict:
        """
        Obtiene las notificaciones paginadas de una persona.

        Retorna dict con:
            data: List[NotificacionPersona]
            total: int
            pagina: int
            tamano_pagina: int
            total_paginas: int
            has_next: bool
            no_leidas: int
        """
        ...


class MarcarNotificacionLeidaUseCase(ABC):

    @abstractmethod
    async def ejecutar(self, persona_id: int, notificacion_id: int) -> None:
        """Marca una notificacion como leida por la persona"""
        ...


class ObtenerDestinatariosUseCase(ABC):

    @abstractmethod
    async def ejecutar(
        self, busqueda: Optional[str] = None
    ) -> List[DestinatarioInfo]:
        """
        Obtiene lista de posibles destinatarios para notificaciones.

        Si busqueda es None, retorna todos los destinatarios disponibles.
        Si busqueda tiene texto, filtra por nombre o identificacion.
        """
        ...


class RegistrarTokenFCMUseCase(ABC):

    @abstractmethod
    async def ejecutar(
        self, persona_id: int, token: str, plataforma: str
    ) -> None:
        """Registra o actualiza el token FCM de una persona"""
        ...


class EliminarTokenFCMUseCase(ABC):

    @abstractmethod
    async def ejecutar(self, persona_id: int, token: str) -> None:
        """Elimina un token FCM (desvincula dispositivo)"""
        ...
