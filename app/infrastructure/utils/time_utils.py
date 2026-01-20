"""
Utilidades para manejo de fechas y horarios con soporte configurable para zonas horarias.

Este módulo proporciona un conjunto de funciones genéricas para trabajar con fechas
y horarios, permitiendo configurar la zona horaria desde settings de la aplicación.

Zona horaria por defecto: America/Bogota (UTC-5, Colombia)
Configurable mediante: settings.TIMEZONE

Ejemplos de zonas horarias válidas:
  - 'America/Bogota'      # Colombia
  - 'America/Quito'       # Ecuador
  - 'America/Lima'        # Perú
  - 'America/New_York'    # Nueva York (UTC-5/-4 con DST)
  - 'Europe/Madrid'       # Madrid (UTC+1/+2 con DST)
  - 'Asia/Tokyo'          # Tokio (UTC+9)
  - 'UTC'                 # UTC
  
Ver lista completa: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
"""
from datetime import datetime, timedelta
from typing import Optional
import pytz


def obtener_zona_horaria():
    """
    Obtiene la zona horaria configurada en settings.
    
    Returns:
        pytz.timezone: Objeto zona horaria configurada
        
    Raises:
        ValueError: Si la zona horaria configurada no es válida
        
    Example:
        >>> tz = obtener_zona_horaria()
        >>> print(tz)
        # <DstTzInfo 'America/Bogota' LMT-1 day, 19:04:00 STD>
    """
    from app.config import get_settings
    
    settings = get_settings()
    try:
        return pytz.timezone(settings.TIMEZONE)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(
            f"Zona horaria inválida configurada: '{settings.TIMEZONE}'. "
            f"Ver: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        )


def ahora() -> datetime:
    """
    Obtiene la hora actual en la zona horaria configurada (timezone-aware).
    
    Returns:
        datetime: Hora actual con información de zona horaria
        
    Example:
        >>> ahora_tz = ahora()
        >>> print(ahora_tz)
        # 2026-01-19 14:30:45.123456-05:00 (en Bogotá)
    """
    return datetime.now(obtener_zona_horaria())


def ahora_sin_tz() -> datetime:
    """
    Obtiene la hora actual en la zona horaria configurada sin timezone info.
    Recomendado para SQLAlchemy y compatibilidad con bases de datos.
    
    Returns:
        datetime: Hora actual sin información de zona horaria
        
    Example:
        >>> ahora_local = ahora_sin_tz()
        >>> print(ahora_local)
        # 2026-01-19 14:30:45.123456
    """
    return datetime.now(obtener_zona_horaria()).replace(tzinfo=None)


def ahora_utc() -> datetime:
    """
    Obtiene la hora actual en UTC (solo si es necesario).
    
    Returns:
        datetime: Hora actual en UTC con información de zona horaria
        
    Example:
        >>> ahora_u = ahora_utc()
        >>> print(ahora_u)
        # 2026-01-19 19:30:45.123456+00:00
    """
    return datetime.now(pytz.UTC)


def convertir_a_local(dt_utc: datetime) -> datetime:
    """
    Convierte un datetime en UTC a la zona horaria configurada.
    
    Args:
        dt_utc: datetime en UTC (debe tener timezone info)
        
    Returns:
        datetime: datetime convertido a la zona horaria local
        
    Example:
        >>> dt_utc = datetime.now(pytz.UTC)
        >>> dt_local = convertir_a_local(dt_utc)
        >>> print(dt_local)
        # 2026-01-19 14:30:45-05:00 (en Bogotá desde UTC)
    """
    if dt_utc.tzinfo is None:
        dt_utc = pytz.UTC.localize(dt_utc)
    
    return dt_utc.astimezone(obtener_zona_horaria())


def convertir_de_local_a_utc(dt_local: datetime) -> datetime:
    """
    Convierte un datetime en zona horaria configurada a UTC.
    
    Args:
        dt_local: datetime en zona horaria local
        
    Returns:
        datetime: datetime convertido a UTC
        
    Example:
        >>> dt_local = ahora()
        >>> dt_utc = convertir_de_local_a_utc(dt_local)
        >>> print(dt_utc)
        # 2026-01-19 19:30:45+00:00
    """
    if dt_local.tzinfo is None:
        dt_local = obtener_zona_horaria().localize(dt_local)
    
    return dt_local.astimezone(pytz.UTC)


def fecha_hoy() -> datetime:
    """
    Obtiene la fecha actual (a las 00:00:00) en zona horaria configurada.
    
    Returns:
        datetime: Fecha de hoy a medianoche (sin tz info)
        
    Example:
        >>> hoy = fecha_hoy()
        >>> print(hoy)
        # 2026-01-19 00:00:00
    """
    now = ahora_sin_tz()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def es_vigente(inicio: datetime, fin: datetime, ahora_actual: Optional[datetime] = None) -> bool:
    """
    Verifica si un rango de tiempo es vigente en el momento actual.
    
    Args:
        inicio: Datetime de inicio de vigencia
        fin: Datetime de fin de vigencia
        ahora_actual: Datetime de comparación (default: ahora_sin_tz())
        
    Returns:
        bool: True si está vigente (inicio <= ahora < fin), False en caso contrario
        
    Example:
        >>> inicio = ahora_sin_tz()
        >>> fin = inicio + timedelta(hours=2)
        >>> print(es_vigente(inicio, fin))
        # True
    """
    if ahora_actual is None:
        ahora_actual = ahora_sin_tz()
    
    return inicio <= ahora_actual < fin


def ha_expirado(fin: datetime, ahora_actual: Optional[datetime] = None) -> bool:
    """
    Verifica si una fecha/tiempo ha expirado.
    
    Args:
        fin: Datetime de expiración
        ahora_actual: Datetime de comparación (default: ahora_sin_tz())
        
    Returns:
        bool: True si ha expirado (ahora >= fin), False en caso contrario
        
    Example:
        >>> fin = ahora_sin_tz() - timedelta(hours=1)
        >>> print(ha_expirado(fin))
        # True
    """
    if ahora_actual is None:
        ahora_actual = ahora_sin_tz()
    
    return ahora_actual >= fin
