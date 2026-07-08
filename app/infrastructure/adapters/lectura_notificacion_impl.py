import json
from app.domain.ports.lectura_notificacion_port import LecturaNotificacionPort
from app.infrastructure.firestore.client import FirestoreClient
from app.infrastructure.utils.time_utils import ahora_utc


class LecturaNotificacionImpl(LecturaNotificacionPort):
    """
    Adaptador concreto: estado de lectura en Firestore para tiempo real.

    Sincroniza el estado de lectura de notificaciones en Firestore
    para que la app Flutter pueda suscribirse a cambios en tiempo real
    via listeners de Firestore.
    """

    COLECCION = "notifications"

    def __init__(self, firestore_client: FirestoreClient):
        self.fs = firestore_client

    async def _sincronizar_firestore(
        self, persona_id: int, notificacion_id: int, leido: bool
    ) -> None:
        """Sincroniza el estado de lectura en Firestore"""
        doc_data = {
            "notificacion_id": notificacion_id,
            "persona_id": persona_id,
            "leido": leido,
            "leido_en": ahora_utc().isoformat() if leido else None,
        }
        documento_id = str(notificacion_id)
        self.fs.crear_documento(
            self.COLECCION, documento_id, doc_data
        )

    async def marcar_como_leida(
        self, persona_id: int, notificacion_id: int
    ) -> None:
        await self._sincronizar_firestore(persona_id, notificacion_id, True)

    async def marcar_todas_como_leidas(self, persona_id: int) -> None:
        try:
            docs = self.fs.obtener_coleccion(self.COLECCION)
            for doc in docs:
                doc_persona_id = doc.get("persona_id")
                notificacion_id = doc.get("notificacion_id")
                if doc_persona_id == persona_id and notificacion_id:
                    await self._sincronizar_firestore(
                        persona_id, notificacion_id, True
                    )
        except Exception:
            pass

    async def obtener_no_leidas(self, persona_id: int) -> int:
        # El conteo real se obtiene desde PostgreSQL (mas preciso)
        # Este metodo existe para cumplir la interfaz del puerto
        return 0
