# Domain - Entidades centrales del negocio
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class EstadoEnum(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"


class ParentescoEnum(str, Enum):
    PADRE = "padre"
    MADRE = "madre"
    ESPOSO = "esposo"
    ESPOSA = "esposa"
    HIJO = "hijo"
    HIJA = "hija"
    OTRO = "otro"


class EstadoQREnum(str, Enum):
    VIGENTE = "vigente"
    EXPIRADO = "expirado"
    USADO = "usado"
    ANULADO = "anulado"


class TipoAccesoEnum(str, Enum):
    QR_RESIDENTE = "qr_residente"
    QR_VISITA = "qr_visita"
    VISITA_SIN_QR = "visita_sin_qr"
    VISITA_PEATONAL = "visita_peatonal"
    RESIDENTE_AUTOMATICO = "residente_automatico"
    MANUAL_GUARDIA = "manual_guardia"


class ResultadoAccesoEnum(str, Enum):
    AUTORIZADO = "autorizado"
    RECHAZADO = "rechazado"
    NO_AUTORIZADO = "no_autorizado"
    FALLO_BIOMETRICO = "fallo_biometrico"
    FALLO_PLACA = "fallo_placa"
    CODIGO_EXPIRADO = "codigo_expirado"
    CODIGO_INVALIDO = "codigo_invalido"
    CUENTA_BLOQUEADA = "cuenta_bloqueada"
    ERROR_SISTEMA = "error_sistema"
    CANCELADO = "cancelado"


@dataclass
class Persona:
    """Entidad de Persona en el dominio"""
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    usuario_creado: str
    nacionalidad: str = "Ecuador"
    correo: Optional[str] = None
    celular: Optional[str] = None
    direccion_alternativa: Optional[str] = None
    estado: EstadoEnum = EstadoEnum.ACTIVO
    eliminado: bool = False
    motivo_eliminado: Optional[str] = None
    id: Optional[int] = None
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    usuario_actualizado: Optional[str] = None

    def es_activo(self) -> bool:
        return self.estado == EstadoEnum.ACTIVO and not self.eliminado

    def puede_acceder(self) -> bool:
        return self.es_activo()


@dataclass
class Vivienda:
    """Entidad de Vivienda"""
    manzana: str
    villa: str
    usuario_creado: str
    estado: EstadoEnum = EstadoEnum.ACTIVO
    eliminado: bool = False
    motivo_eliminado: Optional[str] = None
    id: Optional[int] = None
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    usuario_actualizado: Optional[str] = None

    def es_activa(self) -> bool:
        return self.estado == EstadoEnum.ACTIVO and not self.eliminado


@dataclass
class Residente:
    """Entidad de Residente de una vivienda"""
    vivienda_id: int
    persona_id: int
    usuario_creado: str
    doc_autorizacion_pdf: Optional[str] = None
    estado: EstadoEnum = EstadoEnum.ACTIVO
    eliminado: bool = False
    motivo_eliminado: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    id: Optional[int] = None
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    usuario_actualizado: Optional[str] = None

    def es_activo(self) -> bool:
        return self.estado == EstadoEnum.ACTIVO and not self.eliminado


@dataclass
class QR:
    """Entidad de Código QR"""
    cuenta_id: int
    vivienda_id: int
    hora_inicio_vigencia: datetime
    hora_fin_vigencia: datetime
    token: str
    usuario_creado: str
    visita_id: Optional[int] = None
    estado: EstadoQREnum = EstadoQREnum.VIGENTE
    eliminado: bool = False
    motivo_eliminado: Optional[str] = None
    hora_usado: Optional[datetime] = None
    id: Optional[int] = None
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    usuario_actualizado: Optional[str] = None

    def es_vigente(self) -> bool:
        return (
            self.estado == EstadoQREnum.VIGENTE
            and datetime.utcnow() < self.hora_fin_vigencia
            and not self.eliminado
        )

    def ha_expirado(self) -> bool:
        return datetime.utcnow() >= self.hora_fin_vigencia


@dataclass
class Acceso:
    """Entidad de Registro de Acceso"""
    tipo: TipoAccesoEnum
    vivienda_id: int
    resultado: ResultadoAccesoEnum
    usuario_creado: str
    motivo: Optional[str] = None
    persona_guardia_id: Optional[int] = None
    persona_residente_autoriza_id: Optional[int] = None
    visita_id: Optional[int] = None
    vehiculo_id: Optional[int] = None
    placa_detectada: Optional[str] = None
    biometria_ok: Optional[bool] = None
    placa_ok: Optional[bool] = None
    intentos: int = 0
    observacion: Optional[str] = None
    eliminado: bool = False
    motivo_eliminado: Optional[str] = None
    id: Optional[int] = None
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    usuario_actualizado: Optional[str] = None

    def es_autorizado(self) -> bool:
        return self.resultado == ResultadoAccesoEnum.AUTORIZADO


@dataclass
class Notificacion:
    """Entidad de Notificación"""
    tipo: str
    mensaje: str
    usuario_creado: str
    persona_emisor_id: Optional[int] = None
    eliminado: bool = False
    motivo_eliminado: Optional[str] = None
    id: Optional[int] = None
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    usuario_actualizado: Optional[str] = None
