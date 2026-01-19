import firebase_admin
from firebase_admin import credentials, messaging
from app.config import get_settings
from typing import List, Dict, Any, Optional

settings = get_settings()


class FCMClient:
    """Cliente para Firebase Cloud Messaging"""
    
    def __init__(self):
        try:
            # Usar la misma instancia de Firebase Admin del cliente de Firestore
            self.messaging_client = messaging
        except Exception as e:
            print(f"Error inicializando FCM: {e}")
            raise
    
    def enviar_notificacion_push(
        self,
        token: str,
        titulo: str,
        cuerpo: str,
        datos: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Envía una notificación push a un dispositivo específico
        
        Args:
            token: Token FCM del dispositivo
            titulo: Título de la notificación
            cuerpo: Cuerpo del mensaje
            datos: Datos adicionales
            
        Returns:
            message_id del mensaje enviado
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo
                ),
                data=datos or {},
                token=token
            )
            
            message_id = self.messaging_client.send(message)
            return message_id
        except Exception as e:
            print(f"Error enviando notificación FCM: {e}")
            raise
    
    def enviar_notificacion_multicast(
        self,
        tokens: List[str],
        titulo: str,
        cuerpo: str,
        datos: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envía una notificación push a múltiples dispositivos
        
        Args:
            tokens: Lista de tokens FCM
            titulo: Título de la notificación
            cuerpo: Cuerpo del mensaje
            datos: Datos adicionales
            
        Returns:
            Dict con estadísticas de envío
        """
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo
                ),
                data=datos or {},
                tokens=tokens
            )
            
            response = self.messaging_client.send_multicast(message)
            
            return {
                "exitosos": response.success_count,
                "fallidos": response.failure_count,
                "respuestas": response.responses
            }
        except Exception as e:
            print(f"Error enviando notificaciones multicast FCM: {e}")
            raise
    
    def suscribir_a_topico(self, tokens: List[str], topico: str) -> Dict[str, Any]:
        """
        Suscribe múltiples dispositivos a un tópico
        
        Args:
            tokens: Lista de tokens FCM
            topico: Nombre del tópico
            
        Returns:
            Respuesta de suscripción
        """
        try:
            response = self.messaging_client.make_topic_management_client().make_topic_mgt_req(
                instance_id_tokens=tokens,
                topic=topico
            )
            return {"exito": True, "topico": topico}
        except Exception as e:
            print(f"Error suscribiendo a tópico FCM: {e}")
            raise
    
    def enviar_notificacion_topico(
        self,
        topico: str,
        titulo: str,
        cuerpo: str,
        datos: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Envía una notificación a todos los dispositivos suscritos a un tópico
        
        Args:
            topico: Nombre del tópico
            titulo: Título de la notificación
            cuerpo: Cuerpo del mensaje
            datos: Datos adicionales
            
        Returns:
            message_id del mensaje enviado
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=cuerpo
                ),
                data=datos or {},
                topic=topico
            )
            
            message_id = self.messaging_client.send(message)
            return message_id
        except Exception as e:
            print(f"Error enviando notificación a tópico FCM: {e}")
            raise


def get_fcm_client() -> FCMClient:
    """Obtiene instancia de FCMClient"""
    return FCMClient()
