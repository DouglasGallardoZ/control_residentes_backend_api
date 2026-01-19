# Use cases para generación y validación de QR
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import secrets
import string


class GenerarQRUseCase(ABC):
    """Caso de uso para generar código QR"""

    @abstractmethod
    def ejecutar(
        self,
        cuenta_id: int,
        vivienda_id: int,
        hora_inicio: datetime,
        duracion_horas: int,
        usuario: str,
        visita_id: Optional[int] = None
    ) -> dict:
        """
        Genera un código QR para residente o visita
        
        Args:
            cuenta_id: ID de la cuenta que autoriza
            vivienda_id: ID de la vivienda
            hora_inicio: Hora inicial de vigencia
            duracion_horas: Duración en horas
            usuario: Usuario que crea el QR
            visita_id: ID de visita (opcional, para QR de visita)
            
        Returns:
            dict con datos del QR generado
        """
        pass


class ValidarQRUseCase(ABC):
    """Caso de uso para validar código QR"""

    @abstractmethod
    def ejecutar(self, token: str) -> dict:
        """
        Valida un código QR
        
        Args:
            token: Token del QR
            
        Returns:
            dict con resultado de validación
        """
        pass


class _GenerarQRImpl(GenerarQRUseCase):
    """Implementación del caso de uso Generar QR"""

    def __init__(self, qr_repository):
        self.qr_repository = qr_repository

    def ejecutar(
        self,
        cuenta_id: int,
        vivienda_id: int,
        hora_inicio: datetime,
        duracion_horas: int,
        usuario: str,
        visita_id: Optional[int] = None
    ) -> dict:
        from datetime import timedelta
        
        # Generar token único
        token = self._generar_token()
        
        # Calcular hora final
        hora_fin = hora_inicio + timedelta(hours=duracion_horas)
        
        # Crear QR en repositorio
        qr_data = {
            "cuenta_id": cuenta_id,
            "vivienda_id": vivienda_id,
            "hora_inicio_vigencia": hora_inicio,
            "hora_fin_vigencia": hora_fin,
            "token": token,
            "estado": "vigente",
            "usuario_creado": usuario,
            "visita_id": visita_id
        }
        
        qr_creado = self.qr_repository.crear(qr_data)
        
        return {
            "id": qr_creado.id,
            "token": token,
            "hora_inicio": hora_inicio.isoformat(),
            "hora_fin": hora_fin.isoformat(),
            "estado": "vigente"
        }

    @staticmethod
    def _generar_token() -> str:
        """Genera un token aleatorio seguro"""
        caracteres = string.ascii_letters + string.digits
        return ''.join(secrets.choice(caracteres) for _ in range(32))


class _ValidarQRImpl(ValidarQRUseCase):
    """Implementación del caso de uso Validar QR"""

    def __init__(self, qr_repository):
        self.qr_repository = qr_repository

    def ejecutar(self, token: str) -> dict:
        qr = self.qr_repository.obtener_por_token(token)
        
        if not qr:
            return {
                "valido": False,
                "razon": "QR no encontrado"
            }
        
        if qr.eliminado:
            return {
                "valido": False,
                "razon": "QR eliminado"
            }
        
        if not qr.es_vigente():
            return {
                "valido": False,
                "razon": "QR expirado"
            }
        
        if qr.estado.value == "usado":
            return {
                "valido": False,
                "razon": "QR ya utilizado"
            }
        
        return {
            "valido": True,
            "qr_id": qr.id,
            "cuenta_id": qr.cuenta_id,
            "vivienda_id": qr.vivienda_id,
            "visita_id": qr.visita_id
        }
