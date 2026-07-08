from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.models import Notificacion
from app.domain.entities.notificacion_entities import NotificacionDestino


class NotificacionRepositorioPort(ABC):

    @abstractmethod
    async def guardar_notificacion(self, notificacion: Notificacion) -> Notificacion:
        """Guarda una notificacion en la base de datos"""
        ...

    @abstractmethod
    async def guardar_destinos(
        self, destinos: List[NotificacionDestino]
    ) -> List[NotificacionDestino]:
        """Guarda los destinatarios de una notificacion"""
        ...

    @abstractmethod
    async def obtener_notificaciones_por_persona(
        self,
        persona_id: int,
        pagina: int = 1,
        tamano_pagina: int = 20,
    ) -> dict:
        """
        Obtiene notificaciones paginadas de una persona.

        Retorna:
            dict con claves: data, total, pagina, tamano_pagina, total_paginas, has_next
        """
        ...

    @abstractmethod
    async def obtener_notificacion_por_id(
        self, notificacion_id: int
    ) -> Optional[Notificacion]:
        """Obtiene una notificacion por su ID"""
        ...

    @abstractmethod
    async def marcar_como_entregada(self, destino_id: int) -> None:
        """Marca una notificacion como entregada al dispositivo"""
        ...

    @abstractmethod
    async def marcar_error_envio(self, destino_id: int, error: str) -> None:
        """Registra error de envio de notificacion"""
        ...
