from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class NotificacionDestino:
    """Entidad de destino/receptor de una notificacion"""
    notificacion_envio_id: int
    persona_receptor_id: int
    usuario_creado: str
    entregada: bool = False
    hora_entregado: Optional[datetime] = None
    error: Optional[str] = None
    eliminado: bool = False
    motivo_eliminado: Optional[str] = None
    id: Optional[int] = None
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None
    usuario_actualizado: Optional[str] = None


@dataclass
class SolicitudNotificacion:
    """Value object para crear una nueva notificacion"""
    titulo: str
    mensaje: str
    tipo: str = "notificacion_personalizada"
    prioridad: str = "normal"
    categoria: str = "general"
    persona_emisor_id: Optional[int] = None
    destinatario_ids: List[int] = field(default_factory=list)
    enviar_a_todos: bool = False
    ruta_accion: Optional[str] = None
    datos_accion: Optional[dict] = None


@dataclass
class RespuestaEnvioNotificacion:
    """Resultado del envio de una notificacion"""
    notificacion_id: int
    total_destinatarios: int
    push_enviados: int
    push_fallidos: int
    errores: List[str] = field(default_factory=list)
    mensaje: str = ""


@dataclass
class NotificacionPersona:
    """Notificacion desde la perspectiva del destinatario"""
    notificacion_id: int
    titulo: str
    mensaje: str
    tipo: str
    prioridad: str
    categoria: str
    leido: bool
    fecha_creacion: datetime
    ruta_accion: Optional[str] = None
    datos_accion: Optional[dict] = None
    nombre_emisor: Optional[str] = None


@dataclass
class DestinatarioInfo:
    """Informacion de un posible destinatario de notificacion"""
    persona_id: int
    nombre_completo: str
    identificacion: str
    manzana: Optional[str] = None
    villa: Optional[str] = None
    tipo: str = "residente"
