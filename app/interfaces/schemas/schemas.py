from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, date

from app.domain.validators import (
    validar_identificacion,
    validar_edad_minima,
    validar_celular,
)


# ============ PERSONA ============
class PersonaBase(BaseModel):
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = "Ecuador"
    correo: Optional[EmailStr] = None
    celular: Optional[str] = None
    direccion_alternativa: Optional[str] = None

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


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    correo: Optional[EmailStr] = None
    celular: Optional[str] = None
    direccion_alternativa: Optional[str] = None


class PersonaResponse(PersonaBase):
    id: int
    estado: str
    eliminado: bool
    fecha_creado: datetime
    fecha_actualizado: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ VIVIENDA ============
class ViviendaBase(BaseModel):
    manzana: str
    villa: str


class ViviendaCreate(ViviendaBase):
    pass


class ViviendaResponse(ViviendaBase):
    id: int
    estado: str
    fecha_creado: datetime

    class Config:
        from_attributes = True


# ============ PROPIETARIO ============
class PropietarioCreate(PersonaBase):
    manzana: str
    villa: str
    documento_propiedad_url: str
    fotos_rostro: List[str]  # URLs de fotos


class PropietarioResponse(PersonaResponse):
    vivienda_id: int
    estado: str


class ConyugeCreate(PersonaBase):
    propietario_id: int
    foto_rostro: str


# ============ RESIDENTE ============
class ResidenteCreate(PersonaBase):
    manzana: str
    villa: str
    doc_autorizacion_pdf: str


class ResidenteUpdate(BaseModel):
    pass


class ResidenteResponse(PersonaResponse):
    vivienda_id: int
    estado: str
    doc_autorizacion_pdf: Optional[str] = None


class ResidenteDesactivar(BaseModel):
    motivo: str
    fecha_actualizado: Optional[str] = None


class EliminarResidenteRequest(BaseModel):
    """Schema para eliminar residente (body del DELETE)"""
    motivo: str = "Residente eliminado"


class AgregarFotoRequest(BaseModel):
    """Schema para agregar foto a residente"""
    ruta_imagen: str
    formato: str


class ResidenteReactivar(BaseModel):
    motivo: str
    fecha_actualizado: Optional[str] = None


# ============ MIEMBRO DE FAMILIA ============
class MiembroFamiliaCreate(PersonaBase):
    vivienda_id: int
    residente_id: int
    parentesco: str
    parentesco_otro_desc: Optional[str] = None
    foto_rostro: str


class MiembroFamiliaResponse(PersonaResponse):
    vivienda_id: int
    residente_id: int
    parentesco: str
    parentesco_otro_desc: Optional[str] = None
    estado: str


# ============ CUENTA ============
class CuentaCreate(BaseModel):
    persona_id: int
    username: str
    password: str


class CuentaResponse(BaseModel):
    id: int
    persona_id: int
    username: str
    estado: str
    fecha_creado: datetime
    ultimo_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class CuentaBloquear(BaseModel):
    motivo: str


class CuentaDesbloquear(BaseModel):
    motivo: str


class CuentaEliminar(BaseModel):
    motivo: str


# ============ QR ============
class QRGenerarPropio(BaseModel):
    duracion_horas: int = Field(..., gt=0)
    fecha_acceso: date = None  # Opcional, si no viene usa fecha actual
    hora_inicio: str = None  # HH:MM (opcional, si no viene usa hora actual)


class QRGenerarVisita(BaseModel):
    visita_identificacion: str
    visita_nombres: str
    visita_apellidos: str
    motivo_visita: str
    duracion_horas: int = Field(..., gt=0)
    fecha_acceso: date = None  # Opcional, si no viene usa fecha actual
    hora_inicio: str = None  # HH:MM (opcional, si no viene usa hora actual)


class QRResponse(BaseModel):
    id: int
    token: str
    hora_inicio_vigencia: datetime
    hora_fin_vigencia: datetime
    estado: str
    fecha_creado: datetime

    class Config:
        from_attributes = True


class QRListResponse(BaseModel):
    """Response para listar QRs de una cuenta"""
    qr_pk: int
    token: str
    estado: str
    tipo_ingreso: str  # "propio" o "visita"
    autorizado_por_nombre: str  # Nombre de quien autoriza (titular de cuenta)
    autorizado_para: str  # Nombre de quien es autorizado (visitante o titular)
    hora_inicio_vigencia: datetime
    hora_fin_vigencia: datetime
    fecha_creado: datetime

    class Config:
        from_attributes = True


class QRPaginatedResponse(BaseModel):
    """Response paginada para listar QRs de una cuenta"""
    data: list[QRListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool

    class Config:
        from_attributes = True


# ============ ACCESO ============
class AccesoValidarRequest(BaseModel):
    token_qr: Optional[str] = None
    tipo_acceso: str


class AccesoResponse(BaseModel):
    id: int
    tipo: str
    vivienda_id: int
    resultado: str
    fecha_creado: datetime

    class Config:
        from_attributes = True


class AccesoManualRequest(BaseModel):
    visitante_identificacion: str
    visitante_nombres: str
    visitante_apellidos: str
    manzana: str
    villa: str
    motivo: str
    placa: Optional[str] = None
    autorizado: bool
    usuario_guardia: str


class AccesoAutomaticoPeatonalRequest(BaseModel):
    visitante_identificacion: str
    visitante_nombres: str
    visitante_apellidos: str
    manzana: str
    villa: str
    motivo: str
    foto_rostro: str  # URL o base64


class AccesoSalidaVisitanteRequest(BaseModel):
    visitante_identificacion: str
    manzana: str
    villa: str
    observacion: Optional[str] = None
    usuario_guardia: str


# ============ NOTIFICACIÓN ============
class NotificacionMasivaResidentes(BaseModel):
    mensaje: str
    tipo: str
    usuario_emisor: str


class NotificacionMasivaPropietarios(BaseModel):
    mensaje: str
    tipo: str
    usuario_emisor: str


class NotificacionIndividualResidente(BaseModel):
    persona_id: int
    mensaje: str
    tipo: str
    usuario_emisor: str


class NotificacionIndividualPropietario(BaseModel):
    persona_id: int
    mensaje: str
    tipo: str
    usuario_emisor: str


class NotificacionResponse(BaseModel):
    id: int
    tipo: str
    mensaje: str
    fecha_creado: datetime

    class Config:
        from_attributes = True


# ============ AUTENTICACIÓN ============
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario_id: int
    username: str


class FirebaseLoginRequest(BaseModel):
    id_token: str


# ============ AUTORIZACIÓN DE CÓDIGO ============
class SolicitudAutorizacionCodigoRequest(BaseModel):
    persona_miembro_id: int
    residente_id: int


class AceptarSolicitudCodigoRequest(BaseModel):
    solicitud_id: int
    usuario: str


class RechazarSolicitudCodigoRequest(BaseModel):
    solicitud_id: int
    usuario: str


class UtilizarCodigoAutorizacionRequest(BaseModel):
    codigo: str


# ============ PERFIL DE USUARIO ============
class ViviendaInfo(BaseModel):
    """Información de vivienda para perfil"""
    vivienda_id: int
    manzana: str
    villa: str


class VisitaResponse(BaseModel):
    """Response con información de visitante para reutilización"""
    visita_id: int
    identificacion: str
    nombres: str
    apellidos: str
    fecha_creado: datetime

    class Config:
        from_attributes = True


class ViviendaVisitasResponse(BaseModel):
    """Response con lista de visitantes de una vivienda"""
    vivienda_id: int
    manzana: str
    villa: str
    visitantes: List[VisitaResponse]
    total: int

    class Config:
        from_attributes = True


class PerfilUsuarioResponse(BaseModel):
    """Response con información completa del perfil de usuario"""
    persona_id: int
    identificacion: str
    nombres: str
    apellidos: str
    correo: Optional[EmailStr] = None
    celular: Optional[str] = None
    estado: str
    rol: str  # "residente" o "miembro_familia"
    vivienda: ViviendaInfo
    parentesco: Optional[str] = None  # Solo si rol es "miembro_familia"
    fecha_creado: datetime

    class Config:
        from_attributes = True


# ============ VIVIENDA (CRUD ADMIN) ============


class ViviendaCreate(BaseModel):
    manzana: str = Field(
        ..., min_length=1, max_length=10, description="Numero o letra de manzana"
    )
    villa: str = Field(
        ..., min_length=1, max_length=10, description="Numero de villa"
    )
    estado: str = Field(
        default="activo", pattern=r"^(activo|inactivo)$"
    )


class ViviendaUpdate(BaseModel):
    manzana: Optional[str] = Field(None, min_length=1, max_length=10)
    villa: Optional[str] = Field(None, min_length=1, max_length=10)
    estado: Optional[str] = Field(
        None, pattern=r"^(activo|inactivo)$"
    )
    fecha_actualizado: Optional[str] = None


class ViviendaResponse(BaseModel):
    vivienda_id: int
    manzana: str
    villa: str
    estado: str
    total_residentes: int = 0
    total_miembros: int = 0
    propietarios: list = Field(default_factory=list)
    residentes_count: int = 0
    miembros_count: int = 0
    fecha_creado: Optional[datetime] = None
    fecha_actualizado: Optional[datetime] = None

    class Config:
        from_attributes = True


class ViviendaListResponse(BaseModel):
    data: List[ViviendaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool


class ViviendaEstadoUpdate(BaseModel):
    estado: str = Field(
        ..., pattern=r"^(activo|inactivo)$"
    )
    motivo: Optional[str] = None
    fecha_actualizado: Optional[str] = None


class ViviendaCambioPropietarioRequest(BaseModel):
    vivienda_id: int = Field(..., ge=1)
    nuevo_propietario_id: int = Field(..., ge=1)
    tipo: str = Field(
        default="titular", pattern=r"^(titular|copropietario)$"
    )
    motivo: str = Field(..., min_length=1)
    fecha_actualizado: Optional[str] = None


class ViviendaCambioPropietarioResponse(BaseModel):
    mensaje: str
    vivienda_id: int
    propietario_anterior_id: Optional[int] = None
    nuevo_propietario_id: int
    tipo: str


class PropietarioEnVivienda(BaseModel):
    persona_id: int
    nombres: str
    apellidos: str
    identificacion: str
    correo: Optional[str] = None
    celular: Optional[str] = None
    tipo: str
    estado: str


class ResidenteEnVivienda(BaseModel):
    persona_id: int
    nombres: str
    apellidos: str
    identificacion: str
    correo: Optional[str] = None
    celular: Optional[str] = None
    estado: str


class MiembroEnVivienda(BaseModel):
    persona_id: int
    nombres: str
    apellidos: str
    identificacion: str
    parentesco: str
    estado: str
    residente_id: int
    residente_nombre: str


class ViviendaDetalleResponse(BaseModel):
    vivienda_id: int
    manzana: str
    villa: str
    estado: str
    propietarios: list = Field(default_factory=list)
    residentes: list = Field(default_factory=list)
    miembros: list = Field(default_factory=list)
