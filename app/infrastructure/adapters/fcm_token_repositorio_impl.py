from typing import List
from datetime import datetime
from app.domain.ports.fcm_token_repositorio_port import FcmTokenRepositorioPort
from app.infrastructure.firestore.client import FirestoreClient


class FcmTokenRepositorioImpl(FcmTokenRepositorioPort):
    """Adaptador concreto: gestion de tokens FCM en Firestore"""

    COLECCION_RAIZ = "fcm_tokens"

    def __init__(self, firestore_client: FirestoreClient):
        self.fs = firestore_client

    def _token_a_documento_id(self, persona_id: int, token: str) -> str:
        """Convierte persona_id + token en un ID de documento valido"""
        token_limpio = token.replace("/", "_").replace(".", "_")
        return f"{persona_id}_{token_limpio}"

    async def guardar_token(
        self, persona_id: int, token: str, plataforma: str
    ) -> None:
        documento_id = self._token_a_documento_id(persona_id, token)
        doc_data = {
            "persona_id": persona_id,
            "token": token,
            "plataforma": plataforma,
            "creado": datetime.utcnow().isoformat(),
            "ultimo_uso": datetime.utcnow().isoformat(),
            "activo": True,
        }
        self.fs.crear_documento(self.COLECCION_RAIZ, documento_id, doc_data)

    async def obtener_tokens_por_persona(self, persona_id: int) -> List[str]:
        try:
            docs = self.fs.obtener_coleccion(self.COLECCION_RAIZ)
            tokens = []
            for doc in docs:
                if doc.get("persona_id") == persona_id and doc.get("activo", True):
                    token = doc.get("token")
                    if token:
                        tokens.append(token)
            return tokens
        except Exception:
            return []

    async def obtener_tokens_por_personas(
        self, persona_ids: List[int]
    ) -> dict:
        resultado = {}
        for persona_id in persona_ids:
            tokens = await self.obtener_tokens_por_persona(persona_id)
            if tokens:
                resultado[persona_id] = tokens
        return resultado

    async def eliminar_token(self, persona_id: int, token: str) -> None:
        documento_id = self._token_a_documento_id(persona_id, token)
        self.fs.eliminar_documento(self.COLECCION_RAIZ, documento_id)

    async def obtener_todos_los_tokens(self) -> dict:
        try:
            docs = self.fs.obtener_coleccion(self.COLECCION_RAIZ)
            resultado = {}
            for doc in docs:
                pid = doc.get("persona_id")
                token = doc.get("token")
                if pid and token and doc.get("activo", True):
                    if pid not in resultado:
                        resultado[pid] = []
                    resultado[pid].append(token)
            return resultado
        except Exception:
            return {}
