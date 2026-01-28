from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, Numeric,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, Float, JSON
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infrastructure.utils.time_utils import ahora_sin_tz, fecha_hoy

Base = declarative_base()


class Vivienda(Base):
    """Tabla de viviendas"""
    __tablename__ = "vivienda"
    
    vivienda_pk = Column(Integer, primary_key=True)
    manzana = Column(String(10), nullable=False)
    villa = Column(String(10), nullable=False)
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        UniqueConstraint('manzana', 'villa', name='uq_vivienda'),
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_vivienda_estado'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_vivienda_eliminado_estado'),
    )
    
    propietarios = relationship("PropietarioVivienda", back_populates="vivienda")
    residentes = relationship("ResidenteVivienda", back_populates="vivienda")
    miembros = relationship("MiembroVivienda", back_populates="vivienda")
    visitas = relationship("Visita", back_populates="vivienda")
    accesos = relationship("Acceso", back_populates="vivienda")
    qrs = relationship("QR", back_populates="vivienda")


class Persona(Base):
    """Tabla de personas"""
    __tablename__ = "persona"
    
    persona_pk = Column(Integer, primary_key=True)
    identificacion = Column(String(20), nullable=False)
    tipo_identificacion = Column(String(10), nullable=False)
    nacionalidad = Column(String(50), default='Ecuador')
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    correo = Column(String(100))
    celular = Column(String(10))
    direccion_alternativa = Column(String(120))
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_persona_estado'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_persona_eliminado_estado'),
        Index('uq_persona_identificacion_activa', 'identificacion',
              postgresql_where=(
                  (estado == 'activo') & (eliminado == False)
              )),
    )
    
    fotos = relationship("PersonaFoto", back_populates="persona")
    propietarios = relationship("PropietarioVivienda", back_populates="persona")
    residentes = relationship("ResidenteVivienda", back_populates="persona")
    miembros = relationship(
        "MiembroVivienda",
        back_populates="persona_miembro",
        foreign_keys="[MiembroVivienda.persona_miembro_fk]"
    )
    cuentas = relationship("Cuenta", back_populates="persona")
    guardias = relationship("Guardia", back_populates="persona")
    vehiculos = relationship("Vehiculo", back_populates="persona")
    admin = relationship("Admin", back_populates="persona")


class PersonaFoto(Base):
    """Tabla de fotos de personas"""
    __tablename__ = "persona_foto"
    
    foto_pk = Column(Integer, primary_key=True)
    persona_titular_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    ruta_imagen = Column(Text, nullable=False)
    formato = Column(String(10), nullable=False)
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    rostro_embedding = Column(ARRAY(Float))
    
    persona = relationship("Persona", back_populates="fotos")


class PropietarioVivienda(Base):
    """Tabla de propietarios de vivienda"""
    __tablename__ = "propietario_vivienda"
    
    propietario_vivienda_pk = Column(Integer, primary_key=True)
    vivienda_propiedad_fk = Column(Integer, ForeignKey('vivienda.vivienda_pk'), nullable=False)
    persona_propietario_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    motivo_inactivo = Column(Text)
    fecha_desde = Column(Date, default=lambda: fecha_hoy())
    fecha_hasta = Column(Date)
    motivo = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    tipo_propietario = Column(String(20), nullable=False, default='titular')
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_propietario_estado'),
        CheckConstraint("tipo_propietario IN ('titular','conyuge','copropietario','hijo')", name='chk_propietario_tipo'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_propietario_eliminado_estado'),
        Index('uq_propietario_persona_unica_por_casa', 'vivienda_propiedad_fk', 'persona_propietario_fk', 
              unique=True,
              postgresql_where=(
                  (estado == 'activo') & (eliminado == False)
              )),
        Index('uq_propietario_titular_unico', 'vivienda_propiedad_fk',
              unique=True,
              postgresql_where=(
                  (tipo_propietario == 'titular') & (estado == 'activo') & (eliminado == False)
              )),
    )
    
    vivienda = relationship("Vivienda", back_populates="propietarios")
    persona = relationship("Persona", back_populates="propietarios")


class ResidenteVivienda(Base):
    """Tabla de residentes de vivienda"""
    __tablename__ = "residente_vivienda"
    
    residente_vivienda_pk = Column(Integer, primary_key=True)
    vivienda_reside_fk = Column(Integer, ForeignKey('vivienda.vivienda_pk'), nullable=False)
    persona_residente_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    doc_autorizacion_pdf = Column(Text)
    fecha_desde = Column(Date, default=lambda: fecha_hoy())
    fecha_hasta = Column(Date)
    motivo = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_residente_estado'),
        CheckConstraint("estado <> 'activo' OR fecha_hasta IS NULL", name='chk_residente_activo_sin_fecha_hasta'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_residente_eliminado_estado'),
        Index('uq_residente_activo_vivienda', 'vivienda_reside_fk',
              postgresql_where=(
                  (estado == 'activo') & (eliminado == False)
              )),
    )
    
    vivienda = relationship("Vivienda", back_populates="residentes")
    persona = relationship("Persona", back_populates="residentes")


class MiembroVivienda(Base):
    """Tabla de miembros de familia en vivienda"""
    __tablename__ = "miembro_vivienda"
    
    miembro_vivienda_pk = Column(Integer, primary_key=True)
    vivienda_familia_fk = Column(Integer, ForeignKey('vivienda.vivienda_pk'), nullable=False)
    persona_residente_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    persona_miembro_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    parentesco = Column(String(20), nullable=False)
    parentesco_otro_desc = Column(String(100))
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_miembro_vivienda_estado'),
        CheckConstraint(
            "parentesco IN ('padre','madre','esposo','esposa','hijo','hija','otro')",
            name='chk_miembro_vivienda_parentesco'
        ),
        CheckConstraint(
            "parentesco <> 'otro' OR (parentesco_otro_desc IS NOT NULL AND length(trim(parentesco_otro_desc)) > 0)",
            name='chk_miembro_vivienda_parentesco_otro'
        ),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_miembro_vivienda_eliminado_estado'),
        Index('uq_miembro_vivienda_activo_unico', 'vivienda_familia_fk', 'persona_miembro_fk',
              postgresql_where=(
                  (estado == 'activo') & (eliminado == False)
              )),
        Index('uq_miembro_vivienda_parentesco_unico', 'vivienda_familia_fk', 'parentesco',
              postgresql_where=(
                  (parentesco.in_(['padre','madre','esposo','esposa'])) &
                  (estado == 'activo') &
                  (eliminado == False)
              )),
    )
    
    vivienda = relationship("Vivienda", back_populates="miembros")
    persona_residente = relationship("Persona", foreign_keys=[persona_residente_fk])
    persona_miembro = relationship("Persona", foreign_keys=[persona_miembro_fk], back_populates="miembros")


class Cuenta(Base):
    """Tabla de cuentas de usuario (Firebase Auth)"""
    __tablename__ = "cuenta"
    
    cuenta_pk = Column(Integer, primary_key=True)
    persona_titular_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(Text, nullable=True)
    firebase_uid = Column(String(128), nullable=False, unique=True)
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    ultimo_login = Column(DateTime)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_cuenta_estado'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_cuenta_eliminado_estado'),
    )
    
    persona = relationship("Persona", back_populates="cuentas")
    eventos = relationship("EventoCuenta", back_populates="cuenta")
    qrs = relationship("QR", back_populates="cuenta")


class Admin(Base):
    """Tabla de administradores del sistema"""
    __tablename__ = "admin"
    
    admin_pk = Column(Integer, primary_key=True)
    persona_admin_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_admin_estado'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_admin_eliminado_estado'),
    )
    
    persona = relationship("Persona", back_populates="admin")


class Guardia(Base):
    """Tabla de guardias de seguridad"""
    __tablename__ = "guardia"
    
    guardia_pk = Column(Integer, primary_key=True)
    persona_guardia_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    codigo_guardia = Column(String(20), nullable=False, unique=True)
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_guardia_estado'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_guardia_eliminado_estado'),
        Index('uq_guardia_persona_activa', 'persona_guardia_fk',
              postgresql_where=(
                  (estado == 'activo') & (eliminado == False)
              )),
    )
    
    persona = relationship("Persona", back_populates="guardias")


class EventoCuenta(Base):
    """Tabla de eventos de cuenta"""
    __tablename__ = "evento_cuenta"
    
    evento_cuenta_pk = Column(Integer, primary_key=True)
    cuenta_afectada_fk = Column(Integer, ForeignKey('cuenta.cuenta_pk'), nullable=False)
    tipo_evento = Column(String(30), nullable=False)
    motivo = Column(Text)
    persona_actor_fk = Column(Integer, ForeignKey('persona.persona_pk'))
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint(
            """tipo_evento IN (
                'login_exitoso','login_fallido','logout','sesion_expirada',
                'cuenta_bloqueada','cuenta_desbloqueada','intentos_excedidos',
                'credenciales_invalidas','actividad_sospechosa',
                'cuenta_creada','cuenta_activada','cuenta_inactivada',
                'cuenta_eliminada','cuenta_reactivada',
                'password_cambiado','password_restablecido','password_expirado',
                'cambio_username','cambio_rol','asignacion_guardia','revocacion_guardia'
            )""",
            name='chk_evento_cuenta_tipo'
        ),
    )
    
    cuenta = relationship("Cuenta", back_populates="eventos")


class Vehiculo(Base):
    """Tabla de vehículos"""
    __tablename__ = "vehiculo"
    
    vehiculo_pk = Column(Integer, primary_key=True)
    persona_residente_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    placa = Column(String(10), nullable=False, unique=True)
    estado = Column(String(10), nullable=False, default='activo')
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint("estado IN ('activo','inactivo')", name='chk_vehiculo_estado'),
        CheckConstraint("eliminado = FALSE OR estado = 'inactivo'", name='chk_vehiculo_eliminado_estado'),
    )
    
    persona = relationship("Persona", back_populates="vehiculos")


class Visita(Base):
    """Tabla de visitas"""
    __tablename__ = "visita"
    
    visita_pk = Column(Integer, primary_key=True)
    vivienda_visita_fk = Column(Integer, ForeignKey('vivienda.vivienda_pk'), nullable=False)
    identificacion = Column(String(20))
    nombres = Column(String(100))
    apellidos = Column(String(100))
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    vivienda = relationship("Vivienda", back_populates="visitas")


class Acceso(Base):
    """Tabla de registros de acceso"""
    __tablename__ = "acceso"
    
    acceso_pk = Column(Integer, primary_key=True)
    tipo = Column(String(30), nullable=False)
    vivienda_visita_fk = Column(Integer, ForeignKey('vivienda.vivienda_pk'), nullable=False)
    resultado = Column(String(30), nullable=False)
    motivo = Column(String(30))
    persona_guardia_fk = Column(Integer, ForeignKey('persona.persona_pk'))
    persona_residente_autoriza_fk = Column(Integer, ForeignKey('persona.persona_pk'))
    visita_ingreso_fk = Column(Integer, ForeignKey('visita.visita_pk'))
    vehiculo_ingreso_fk = Column(Integer, ForeignKey('vehiculo.vehiculo_pk'))
    placa_detectada = Column(String(10))
    biometria_ok = Column(Boolean)
    placa_ok = Column(Boolean)
    intentos = Column(Integer, nullable=False, default=0)
    observacion = Column(Text)
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint(
            """tipo IN (
                'qr_residente','qr_visita','visita_sin_qr',
                'visita_peatonal','residente_automatico','manual_guardia'
            )""",
            name='chk_acceso_tipo'
        ),
        CheckConstraint(
            """resultado IN (
                'autorizado','rechazado','no_autorizado','fallo_biometrico',
                'fallo_placa','codigo_expirado','codigo_invalido',
                'cuenta_bloqueada','error_sistema','cancelado'
            )""",
            name='chk_acceso_resultado'
        ),
    )
    
    vivienda = relationship("Vivienda", back_populates="accesos")


class AutorizacionTelefonica(Base):
    """Tabla de autorizaciones telefónicas"""
    __tablename__ = "autorizacion_telefonica"
    
    autorizacion_tel_pk = Column(Integer, primary_key=True)
    acceso_ingreso_fk = Column(Integer, ForeignKey('acceso.acceso_pk'), nullable=False)
    telefono = Column(String(15))
    respuesta = Column(String(20))
    numero_intentos = Column(Integer)
    hora_inicio = Column(DateTime)
    hora_fin = Column(DateTime)
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint(
            """respuesta IN (
                'aceptado','rechazado','sin_respuesta',
                'numero_invalido','fallo_proveedor'
            )""",
            name='chk_respuesta_tel'
        ),
    )


class AutorizacionCodigo(Base):
    """Tabla de códigos de autorización"""
    __tablename__ = "autorizacion_codigo"
    
    autorizacion_codigo_pk = Column(Integer, primary_key=True)
    persona_residente_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    codigo_hash = Column(Text, nullable=False)
    hora_generado = Column(DateTime, nullable=False)
    hora_expira = Column(DateTime, nullable=False)
    hora_usado = Column(DateTime)
    estado = Column(String(20), nullable=False)
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint(
            "estado IN ('vigente','expirado','usado','anulado')",
            name='chk_estado_codigo'
        ),
    )


class QR(Base):
    """Tabla de códigos QR"""
    __tablename__ = "qr"
    
    qr_pk = Column(Integer, primary_key=True)
    cuenta_autoriza_fk = Column(Integer, ForeignKey('cuenta.cuenta_pk'), nullable=False)
    vivienda_visita_fk = Column(Integer, ForeignKey('vivienda.vivienda_pk'), nullable=False)
    visita_ingreso_fk = Column(Integer, ForeignKey('visita.visita_pk'))
    hora_inicio_vigencia = Column(DateTime, nullable=False)
    hora_fin_vigencia = Column(DateTime, nullable=False)
    hora_usado = Column(DateTime)
    estado = Column(String(20), nullable=False)
    token = Column(Text, nullable=False)
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint(
            "estado IN ('vigente','expirado','usado','anulado')",
            name='chk_estado_qr'
        ),
    )
    
    cuenta = relationship("Cuenta", back_populates="qrs")
    vivienda = relationship("Vivienda", back_populates="qrs")


class Notificacion(Base):
    """Tabla de notificaciones"""
    __tablename__ = "notificacion"
    
    notificacion_pk = Column(Integer, primary_key=True)
    tipo = Column(String(30), nullable=False)
    mensaje = Column(Text, nullable=False)
    persona_emisor_fk = Column(Integer, ForeignKey('persona.persona_pk'))
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    __table_args__ = (
        CheckConstraint(
            """tipo IN (
                'solicitud_autorizacion','ingreso_autorizado','ingreso_rechazado',
                'intento_fallido','qr_generado','qr_expirado',
                'codigo_generado','codigo_usado','alerta_seguridad',
                'cuenta_bloqueada','acceso_manual',
                'alta_usuario','baja_usuario',
                'cambio_estado','actualizacion_datos'
            )""",
            name='chk_notificacion_tipo'
        ),
    )
    
    destinos = relationship("NotificacionDestino", back_populates="notificacion")


class NotificacionDestino(Base):
    """Tabla de destinos de notificaciones"""
    __tablename__ = "notificacion_destino"
    
    notificacion_destino_pk = Column(Integer, primary_key=True)
    notificacion_envio_fk = Column(Integer, ForeignKey('notificacion.notificacion_pk'), nullable=False)
    persona_receptor_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    entregada = Column(Boolean, nullable=False, default=False)
    hora_entregado = Column(DateTime)
    error = Column(Text)
    eliminado = Column(Boolean, nullable=False, default=False)
    motivo_eliminado = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
    usuario_creado = Column(String(20), nullable=False)
    fecha_actualizado = Column(DateTime)
    usuario_actualizado = Column(String(20))
    
    notificacion = relationship("Notificacion", back_populates="destinos")


class Bitacora(Base):
    """Tabla de bitácora de auditoría"""
    __tablename__ = "bitacora"
    
    bitacora_pk = Column(Integer, primary_key=True)
    entidad = Column(String(50), nullable=False)
    entidad_id = Column(String(50), nullable=False)
    operacion = Column(String(20), nullable=False)
    persona_actor_fk = Column(Integer, ForeignKey('persona.persona_pk'))
    valor_anterior = Column(JSONB)
    valor_nuevo = Column(JSONB)
    descripcion = Column(Text)
    fecha_creado = Column(DateTime, default=lambda: ahora_sin_tz())
