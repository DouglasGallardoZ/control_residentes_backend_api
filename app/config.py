import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Base de datos
    DB_USER: str = "admin"
    DB_PASSWORD: str = "password123"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "urbanizacion_db"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construye la URL de base de datos desde variables de entorno"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    SQLALCHEMY_ECHO: bool = False
    
    # Firestore
    FIREBASE_PROJECT_ID: str = "tu-proyecto-firebase"
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"
    
    # Firebase Auth
    FIREBASE_API_KEY: str = "tu-api-key"
    
    # FCM (Firebase Cloud Messaging)
    FCM_SENDER_ID: str = "tu-sender-id"
    
    # JWT (para plan de migración)
    JWT_SECRET_KEY: str = "tu-secret-key-muy-segura-cambia-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Biometría (microservicio externo)
    BIOMETRIA_SERVICE_URL: str = "http://localhost:8001"
    BIOMETRIA_SERVICE_KEY: str = "biometria-api-key"
    
    # API
    API_VERSION: str = "v1"
    API_TITLE: str = "API Control de Acceso Residencial"
    API_DESCRIPTION: str = "Backend para sistema de control de acceso y gestión de residentes"
    
    # Zona Horaria (configurable por ambiente)
    # Ejemplos: 'America/Bogota', 'America/Quito', 'America/Lima', 'UTC', etc.
    # Lista completa: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    TIMEZONE: str = "America/Bogota"  # UTC-5 (Colombia, Quito)
    
    # ========== PAGINACIÓN ==========
    # Valores por defecto y límites para endpoints que retornan listas
    PAGINATION_DEFAULT_PAGE: int = 1
    PAGINATION_DEFAULT_PAGE_SIZE: int = 10
    PAGINATION_MAX_PAGE_SIZE: int = 100
    
    # ========== SEGURIDAD - CONTRASEÑAS ==========
    # Política de validación de contraseñas (CV-20)
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_BYTES: int = 72  # Límite de bcrypt/UTF-8
    PASSWORD_SPECIAL_CHARS: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    PASSWORD_MUST_HAVE_UPPER: bool = True
    PASSWORD_MUST_HAVE_DIGIT: bool = True
    PASSWORD_MUST_HAVE_SPECIAL: bool = False
    
    # ========== SEGURIDAD - BIOMETRÍA ==========
    # Límites para intentos fallidos
    MAX_BIOMETRIC_FAILED_ATTEMPTS: int = 2  # RF-AQ02
    PHONE_RESPONSE_TIMEOUT_SECONDS: int = 30  # Tiempo máximo espera telefónica
    
    # ========== CÓDIGOS QR ==========
    QR_TOKEN_LENGTH: int = 32  # Caracteres del token
    QR_CODE_VALIDITY_MINUTES: int = 3  # Validez de código QR (RF-AQ01)
    
    # ========== LONGITUDES DE CAMPOS ==========
    # Límites de longitud para campos de base de datos
    # Requerimientos de datos: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    FIELD_LENGTHS: dict = {
        'identification': 20,      # CV-01: Identificación (10 dígitos, 20 chars)
        'phone': 15,               # CV-06: Celular (10 dígitos, 15 chars)
        'email': 100,              # CV-07: Correo electrónico
        'address': 120,            # CV-08: Dirección alternativa
        'username': 50,            # Usuario del sistema
        'user_action': 20,         # usuario_creado/usuario_actualizado
        'manzana': 10,             # Identificador manzana
        'villa': 10,               # Identificador villa
    }
    
    # Seguridad
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la instancia de configuración (con caché)"""
    return Settings()
