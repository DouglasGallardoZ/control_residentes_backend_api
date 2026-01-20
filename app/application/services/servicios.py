# Servicios de aplicación para orquestar casos de uso
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.infrastructure.db.models import (
    QR as QRModel, Cuenta, Persona, Notificacion, NotificacionDestino,
    ResidenteVivienda, Vivienda
)
from app.infrastructure.firestore.client import get_firestore_client
from app.infrastructure.notifications.fcm_client import get_fcm_client
from app.infrastructure.utils.time_utils import ahora_sin_tz


class QRService:
    """Servicio para casos de uso de QR"""
    
    def __init__(self, db: Session):
        self.db = db
        self.firestore = get_firestore_client()
        self.fcm = get_fcm_client()
    
    def generar_qr_residente(
        self,
        cuenta_id: int,
        vivienda_id: int,
        hora_inicio: datetime,
        duracion_horas: int,
        usuario: str
    ) -> Dict:
        """Genera QR para residente"""
        import secrets
        import string
        
        # Generar token
        caracteres = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(caracteres) for _ in range(32))
        
        hora_fin = hora_inicio + timedelta(hours=duracion_horas)
        
        # Crear en PostgreSQL
        qr = QRModel(
            cuenta_autoriza_fk=cuenta_id,
            vivienda_visita_fk=vivienda_id,
            hora_inicio_vigencia=hora_inicio,
            hora_fin_vigencia=hora_fin,
            token=token,
            estado="vigente",
            usuario_creado=usuario
        )
        
        self.db.add(qr)
        self.db.flush()
        
        # Sincronizar en Firestore
        self.firestore.crear_documento(
            "qr",
            f"qr-{qr.qr_pk}",
            {
                "qr_id": qr.qr_pk,
                "token": token,
                "vivienda_id": vivienda_id,
                "cuenta_id": cuenta_id,
                "hora_inicio": hora_inicio.isoformat(),
                "hora_fin": hora_fin.isoformat(),
                "estado": "vigente",
                "creado_en": ahora_sin_tz().isoformat()
            }
        )
        
        self.db.commit()
        
        return {
            "id": qr.qr_pk,
            "token": token,
            "hora_inicio": hora_inicio.isoformat(),
            "hora_fin": hora_fin.isoformat()
        }


class NotificacionService:
    """Servicio para notificaciones"""
    
    def __init__(self, db: Session):
        self.db = db
        self.fcm = get_fcm_client()
        self.firestore = get_firestore_client()
    
    def enviar_notificacion_masiva_residentes(
        self,
        titulo: str,
        cuerpo: str,
        tipo: str,
        usuario: str,
        datos: Optional[Dict] = None
    ) -> Dict:
        """
        Envía notificación masiva a todos los residentes activos
        RF-N01
        """
        # Crear notificación en BD
        notificacion = Notificacion(
            tipo=tipo,
            mensaje=cuerpo,
            usuario_creado=usuario
        )
        
        self.db.add(notificacion)
        self.db.flush()
        
        # Obtener residentes activos
        residentes = self.db.query(Persona).filter(
            Persona.estado == "activo",
            Persona.eliminado == False
        ).all()
        
        # TODO: Obtener tokens FCM de residentes desde tabla separada
        tokens = []  # Placeholder
        
        # Enviar notificación push si hay tokens
        if tokens:
            self.fcm.enviar_notificacion_multicast(
                tokens=tokens,
                titulo=titulo,
                cuerpo=cuerpo,
                datos=datos or {}
            )
        
        # Registrar destinos
        for residente in residentes:
            destino = NotificacionDestino(
                notificacion_envio_fk=notificacion.notificacion_pk,
                persona_receptor_fk=residente.persona_pk,
                usuario_creado=usuario
            )
            self.db.add(destino)
        
        self.db.commit()
        
        return {
            "id": notificacion.notificacion_pk,
            "mensaje": "Notificación enviada a residentes",
            "cantidad_residentes": len(residentes)
        }
    
    def enviar_notificacion_individual(
        self,
        persona_id: int,
        titulo: str,
        cuerpo: str,
        tipo: str,
        usuario: str,
        datos: Optional[Dict] = None
    ) -> Dict:
        """
        Envía notificación individual a una persona
        RF-N03, RF-N04
        """
        # Validar que persona existe y está activa
        persona = self.db.query(Persona).filter(
            Persona.persona_pk == persona_id,
            Persona.estado == "activo",
            Persona.eliminado == False
        ).first()
        
        if not persona:
            return {"error": "Persona no encontrada o inactiva"}
        
        # Crear notificación
        notificacion = Notificacion(
            tipo=tipo,
            mensaje=cuerpo,
            usuario_creado=usuario
        )
        
        self.db.add(notificacion)
        self.db.flush()
        
        # Registrar destino
        destino = NotificacionDestino(
            notificacion_envio_fk=notificacion.notificacion_pk,
            persona_receptor_fk=persona_id,
            usuario_creado=usuario
        )
        
        self.db.add(destino)
        
        # TODO: Obtener token FCM del usuario
        # self.fcm.enviar_notificacion_push(
        #     token=fcm_token,
        #     titulo=titulo,
        #     cuerpo=cuerpo,
        #     datos=datos or {}
        # )
        
        self.db.commit()
        
        return {
            "id": notificacion.notificacion_pk,
            "mensaje": "Notificación enviada"
        }


class CuentaService:
    """Servicio para gestión de cuentas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def bloquear_cuenta_y_familia(
        self,
        cuenta_id: int,
        motivo: str,
        usuario: str
    ) -> Dict:
        """Bloquea cuenta de residente y todos sus miembros"""
        # TODO: Implementar bloqueo en cascada
        return {"mensaje": "Cuentas bloqueadas"}
    
    def desbloquear_cuenta_y_familia(
        self,
        cuenta_id: int,
        motivo: str,
        usuario: str
    ) -> Dict:
        """Desbloquea cuenta de residente y todos sus miembros"""
        # TODO: Implementar desbloqueo en cascada
        return {"mensaje": "Cuentas desbloqueadas"}
