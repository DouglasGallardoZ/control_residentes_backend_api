from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TokenFCMRequest(BaseModel):
    token_fcm: str = Field(..., description="Token FCM del dispositivo")
    plataforma: str = Field("android", description="Plataforma: android, ios, web")


class EliminarTokenFCMRequest(BaseModel):
    token_fcm: str = Field(..., description="Token FCM a eliminar")


class SolicitudNotificacionRequest(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    mensaje: str = Field(..., min_length=1, max_length=2000)
    prioridad: str = Field("normal", pattern=r"^(alta|normal|baja)$")
    categoria: str = Field("general", pattern=r"^(general|visita|seguridad|pago|evento)$")
    destinatario_ids: Optional[List[int]] = None
    enviar_a_todos: bool = False
    ruta_accion: Optional[str] = None
    datos_accion: Optional[dict] = None


class MarcarLeidaRequest(BaseModel):
    persona_id: int


class NotificacionItemResponse(BaseModel):
    notificacion_id: int
    titulo: str
    cuerpo: str
    tipo: str
    prioridad: str
    categoria: str
    leido: bool
    fecha_creacion: Optional[str] = None
    ruta_accion: Optional[str] = None
    datos_accion: Optional[dict] = None


class NotificacionPaginadaResponse(BaseModel):
    data: List[NotificacionItemResponse]
    total: int
    no_leidas: int
    pagina: int
    tamano_pagina: int
    total_paginas: int
    tiene_mas: bool


class ConteoNoLeidasResponse(BaseModel):
    no_leidas: int


class RespuestaEnvioNotificacionResponse(BaseModel):
    notificacion_id: int
    total_destinatarios: int
    push_enviados: int
    push_fallidos: int
    errores: List[str] = []
    mensaje: str


class DestinatarioResponse(BaseModel):
    persona_id: int
    nombre_completo: str
    identificacion: str
    manzana: Optional[str] = None
    villa: Optional[str] = None
    tipo: str


class MensajeResponse(BaseModel):
    mensaje: str
