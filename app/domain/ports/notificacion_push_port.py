from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class NotificacionPushPort(ABC):

    @abstractmethod
    async def enviar_push_individual(
        self,
        token: str,
        titulo: str,
        cuerpo: str,
        datos: Optional[dict] = None,
    ) -> bool:
        """Envia una notificacion push a un solo dispositivo"""
        ...

    @abstractmethod
    async def enviar_push_multicast(
        self,
        tokens: List[str],
        titulo: str,
        cuerpo: str,
        datos: Optional[dict] = None,
    ) -> Dict[str, any]:
        """
        Envia notificacion push a multiples dispositivos.

        Retorna:
            {"exitosos": int, "fallidos": int, "errores": List[str]}
        """
        ...

    @abstractmethod
    async def enviar_push_por_topico(
        self,
        topico: str,
        titulo: str,
        cuerpo: str,
        datos: Optional[dict] = None,
    ) -> bool:
        """Envia notificacion push a un topico FCM"""
        ...
