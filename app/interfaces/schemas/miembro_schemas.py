from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional, List

from app.domain.validators import (
    validar_identificacion,
    validar_edad_minima,
    validar_celular,
)


class SolicitarMiembroRequest(BaseModel):
    """Schema para POST /miembros/solicitar"""
    identificacion_residente: str = Field(
        ..., description="Cedula del residente titular"
    )
    manzana: str
    villa: str
    identificacion: str = Field(..., max_length=20)
    tipo_identificacion: str = Field(default="Cedula")
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = Field(default="Ecuador")
    correo: Optional[str] = None
    celular: Optional[str] = None
    direccion_alternativa: Optional[str] = None
    parentesco: str = Field(
        ..., description="padre|madre|esposo|esposa|hijo|hija|otro"
    )
    parentesco_otro_desc: Optional[str] = None
    usuario_creado: str = Field(default="api_system")
    token_fcm: Optional[str] = Field(
        None,
        description="Token FCM del dispositivo del miembro (opcional, para recibir push al aprobar/rechazar)",
    )
    plataforma: str = Field(
        "android",
        description="Plataforma del dispositivo: android, ios, web",
    )

    @field_validator("identificacion")
    @classmethod
    def validar_id(cls, v, info):
        tipo = info.data.get("tipo_identificacion", "Cedula")
        error = validar_identificacion(v, tipo)
        if error:
            raise ValueError(error)
        return v

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha(cls, v):
        error = validar_edad_minima(v)
        if error:
            raise ValueError(error)
        return v

    @field_validator("celular")
    @classmethod
    def validar_tel(cls, v):
        error = validar_celular(v)
        if error:
            raise ValueError(error)
        return v


class SolicitudPendienteResponse(BaseModel):
    """Schema para respuesta individual en GET /miembros/solicitudes/pendientes"""
    notificacion_id: int
    nombres: str
    apellidos: str
    identificacion: str
    parentesco: str
    parentesco_otro_desc: Optional[str] = None
    manzana: str
    villa: str
    fecha_solicitud: Optional[str] = None


class SolicitudesPendientesResponse(BaseModel):
    """Schema para GET /miembros/solicitudes/pendientes"""
    total: int
    solicitudes: list[SolicitudPendienteResponse]


class AprobarRechazarRequest(BaseModel):
    """Schema para PUT /miembros/solicitudes/{id}/aprobar y .../rechazar"""
    usuario_actualizado: str = Field(default="")
    motivo: Optional[str] = None
    fecha_actualizado: Optional[str] = None


class SolicitudAprobadaResponse(BaseModel):
    """Schema para respuesta de PUT /miembros/solicitudes/{id}/aprobar"""
    success: bool
    persona_id: int
    miembro_id: int
    mensaje: str


class SolicitudRechazadaResponse(BaseModel):
    """Schema para respuesta de PUT /miembros/solicitudes/{id}/rechazar"""
    success: bool
    mensaje: str


class EstadoSolicitudResponse(BaseModel):
    """Schema para GET /miembros/solicitudes/estado/{identificacion}"""
    estado: str
    persona_id: Optional[int] = None
    miembro_id: Optional[int] = None
    motivo: Optional[str] = None
    notificacion_id: Optional[int] = None
    mensaje: Optional[str] = None
