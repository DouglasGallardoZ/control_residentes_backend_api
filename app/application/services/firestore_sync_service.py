"""
Servicio para sincronizar notificaciones entre PostgreSQL y Firestore.

Firestore se usa para:
- Tiempo real (estado de lectura): la app Flutter se suscribe a cambios
- Tokens FCM: almacenamiento de tokens de dispositivos
- PostgreSQL es la fuente de verdad
"""
from typing import List, Dict
from datetime import datetime

from app.infrastructure.firestore.client import FirestoreClient


class FirestoreSyncService:

    COLECCION_NOTIFICACIONES = "notifications"
    COLECCION_TOKENS = "fcm_tokens"
    SUBCOLECCION_ITEMS = "items"
    SUBCOLECCION_TOKENS = "tokens"

    def __init__(self):
        self.fs = FirestoreClient()

    # ─── TOKENS FCM ────────────────────────────────────────

    async def guardar_token_fcm(
        self, persona_id: int, token: str, plataforma: str
    ) -> None:
        """Guarda un token FCM en Firestore"""
        ahora = datetime.utcnow().isoformat()
        datos = {
            "token": token,
            "plataforma": plataforma,
            "creado_en": ahora,
            "ultimo_uso": ahora,
        }
        await self.fs.guardar_subdocumento(
            self.COLECCION_TOKENS,
            str(persona_id),
            self.SUBCOLECCION_TOKENS,
            token,
            datos,
        )

    async def obtener_tokens_por_persona(self, persona_id: int) -> List[str]:
        """Obtiene todos los tokens FCM de una persona"""
        docs = await self.fs.obtener_subcoleccion(
            self.COLECCION_TOKENS,
            str(persona_id),
            self.SUBCOLECCION_TOKENS,
        )
        return [doc.get("token") for doc in docs if doc.get("token")]

    async def obtener_tokens_por_personas(
        self, persona_ids: List[int]
    ) -> Dict[int, List[str]]:
        """Obtiene tokens FCM para multiples personas"""
        resultado = {}
        for pid in persona_ids:
            tokens = await self.obtener_tokens_por_persona(pid)
            if tokens:
                resultado[pid] = tokens
        return resultado

    async def eliminar_token_fcm(self, persona_id: int, token: str) -> None:
        """Elimina un token FCM"""
        path = (
            f"{self.COLECCION_TOKENS}/{persona_id}/"
            f"{self.SUBCOLECCION_TOKENS}/{token}"
        )
        await self.fs.eliminar_documento(path, "")

    # ─── ESTADO DE LECTURA (TIEMPO REAL) ───────────────────

    async def sincronizar_notificacion_enviada(
        self,
        persona_id: int,
        notificacion_id: int,
        titulo: str,
        cuerpo: str,
        categoria: str,
        prioridad: str,
        ruta_accion: str = None,
        datos_accion: dict = None,
    ) -> None:
        """Crea una copia de la notificacion en Firestore para tiempo real"""
        ahora = datetime.utcnow().isoformat()
        await self.fs.guardar_subdocumento(
            self.COLECCION_NOTIFICACIONES,
            str(persona_id),
            self.SUBCOLECCION_ITEMS,
            str(notificacion_id),
            {
                "notificacion_id": notificacion_id,
                "titulo": titulo,
                "cuerpo": cuerpo,
                "categoria": categoria,
                "prioridad": prioridad,
                "ruta_accion": ruta_accion or "",
                "datos_accion": datos_accion or {},
                "leido": False,
                "fecha_creacion": ahora,
                "fecha_lectura": None,
            },
        )

    async def marcar_como_leida(
        self, persona_id: int, notificacion_id: int
    ) -> None:
        """Actualiza el estado de lectura en Firestore"""
        await self.fs.guardar_subdocumento(
            self.COLECCION_NOTIFICACIONES,
            str(persona_id),
            self.SUBCOLECCION_ITEMS,
            str(notificacion_id),
            {
                "leido": True,
                "fecha_lectura": datetime.utcnow().isoformat(),
            },
        )

    async def marcar_todas_como_leidas(self, persona_id: int) -> None:
        """Marca todas las notificaciones como leidas en Firestore"""
        docs = await self.fs.obtener_subcoleccion(
            self.COLECCION_NOTIFICACIONES,
            str(persona_id),
            self.SUBCOLECCION_ITEMS,
        )
        for doc in docs:
            notif_id = doc.get("id") or doc.get("notificacion_id")
            if notif_id:
                await self.marcar_como_leida(persona_id, notif_id)

    async def eliminar_notificacion(
        self, persona_id: int, notificacion_id: int
    ) -> None:
        """Elimina una notificacion de Firestore"""
        await self.fs.guardar_subdocumento(
            self.COLECCION_NOTIFICACIONES,
            str(persona_id),
            self.SUBCOLECCION_ITEMS,
            str(notificacion_id),
            {"eliminado": True},
        )
