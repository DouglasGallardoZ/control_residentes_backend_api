from typing import List, Optional
from app.domain.ports.notificacion_push_port import NotificacionPushPort
from app.infrastructure.notifications.fcm_client import FCMClient


class NotificacionPushImpl(NotificacionPushPort):
    """Adaptador concreto: envio de push notifications via FCM"""

    def __init__(self, fcm_client: FCMClient):
        self.fcm = fcm_client

    async def enviar_push_individual(
        self,
        token: str,
        titulo: str,
        cuerpo: str,
        datos: Optional[dict] = None,
    ) -> bool:
        try:
            self.fcm.enviar_notificacion_push(
                token, titulo, cuerpo, datos or {}
            )
            return True
        except Exception:
            return False

    async def enviar_push_multicast(
        self,
        tokens: List[str],
        titulo: str,
        cuerpo: str,
        datos: Optional[dict] = None,
    ) -> dict:
        if not tokens:
            return {"exitosos": 0, "fallidos": 0, "errores": []}

        try:
            resultado = self.fcm.enviar_notificacion_multicast(
                tokens, titulo, cuerpo, datos or {}
            )
            return {
                "exitosos": resultado.get("exitosos", 0),
                "fallidos": resultado.get("fallidos", 0),
                "errores": [],
            }
        except Exception as e:
            return {
                "exitosos": 0,
                "fallidos": len(tokens),
                "errores": [str(e)],
            }

    async def enviar_push_por_topico(
        self,
        topico: str,
        titulo: str,
        cuerpo: str,
        datos: Optional[dict] = None,
    ) -> bool:
        try:
            self.fcm.enviar_notificacion_topico(
                topico, titulo, cuerpo, datos or {}
            )
            return True
        except Exception:
            return False
