from abc import ABC, abstractmethod
from typing import List, Dict


class FcmTokenRepositorioPort(ABC):

    @abstractmethod
    async def guardar_token(
        self, persona_id: int, token: str, plataforma: str
    ) -> None:
        """Guarda o actualiza un token FCM para una persona"""
        ...

    @abstractmethod
    async def obtener_tokens_por_persona(self, persona_id: int) -> List[str]:
        """Obtiene todos los tokens FCM activos de una persona"""
        ...

    @abstractmethod
    async def obtener_tokens_por_personas(
        self, persona_ids: List[int]
    ) -> Dict[int, List[str]]:
        """
        Obtiene tokens FCM para multiples personas.

        Retorna:
            {persona_id: [token1, token2]}
        """
        ...

    @abstractmethod
    async def eliminar_token(self, persona_id: int, token: str) -> None:
        """Elimina un token FCM (por ejemplo, cuando el dispositivo se desvincula)"""
        ...

    @abstractmethod
    async def obtener_todos_los_tokens(self) -> Dict[int, List[str]]:
        """
        Obtiene todos los tokens FCM registrados.

        Retorna:
            {persona_id: [token1, token2]}
        """
        ...
