# Archivo __init__ para db
from app.infrastructure.db.database import SessionLocal, get_db, engine
from app.infrastructure.db.models import (
    Base, Vivienda, Persona, PersonaFoto, PropietarioVivienda, ResidenteVivienda,
    MiembroVivienda, Cuenta, Guardia, EventoCuenta, Vehiculo, Visita, Acceso,
    AutorizacionTelefonica, AutorizacionCodigo, QR, Notificacion, NotificacionDestino,
    Bitacora
)

__all__ = [
    'SessionLocal', 'get_db', 'engine', 'Base',
    'Vivienda', 'Persona', 'PersonaFoto', 'PropietarioVivienda', 'ResidenteVivienda',
    'MiembroVivienda', 'Cuenta', 'Guardia', 'EventoCuenta', 'Vehiculo', 'Visita',
    'Acceso', 'AutorizacionTelefonica', 'AutorizacionCodigo', 'QR', 'Notificacion',
    'NotificacionDestino', 'Bitacora'
]
