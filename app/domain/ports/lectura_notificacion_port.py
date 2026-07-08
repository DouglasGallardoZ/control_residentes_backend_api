from abc import ABC, abstractmethod


class LecturaNotificacionPort(ABC):

    @abstractmethod
    async def marcar_como_leida(
        self, persona_id: int, notificacion_id: int
    ) -> None:
        """Marca una notificacion como leida en Firestore para tiempo real"""
        ...

    @abstractmethod
    async def marcar_todas_como_leidas(self, persona_id: int) -> None:
        """Marca todas las notificaciones como leidas para una persona"""
        ...

    @abstractmethod
    async def obtener_no_leidas(self, persona_id: int) -> int:
        """Obtiene el conteo de notificaciones no leidas desde PostgreSQL"""
        ...
