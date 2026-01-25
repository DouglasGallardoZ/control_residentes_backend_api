import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación - todas las variables se leen de variables de entorno (.env)"""
    
    # ========== BASE DE DATOS ==========
    DB_USER: str = os.getenv("DB_USER", "admin")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password123")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "urbanizacion_db")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construye la URL de base de datos desde variables de entorno"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    
    # ========== FIRESTORE ==========
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "tu-proyecto-firebase")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    
    # ========== FIREBASE AUTH ==========
    FIREBASE_API_KEY: str = os.getenv("FIREBASE_API_KEY", "tu-api-key")
    
    # ========== FCM (FIREBASE CLOUD MESSAGING) ==========
    FCM_SENDER_ID: str = os.getenv("FCM_SENDER_ID", "tu-sender-id")
    
    # ========== JWT (PARA PLAN DE MIGRACIÓN) ==========
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "tu-secret-key-muy-segura-cambia-en-produccion")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # ========== BIOMETRÍA (MICROSERVICIO EXTERNO) ==========
    BIOMETRIA_SERVICE_URL: str = os.getenv("BIOMETRIA_SERVICE_URL", "http://localhost:8001")
    BIOMETRIA_SERVICE_KEY: str = os.getenv("BIOMETRIA_SERVICE_KEY", "biometria-api-key")
    
    # ========== API ==========
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    API_TITLE: str = os.getenv("API_TITLE", "API Control de Acceso Residencial")
    API_DESCRIPTION: str = os.getenv("API_DESCRIPTION", "Backend para sistema de control de acceso y gestión de residentes")
    
    # ========== ZONA HORARIA ==========
    # Ejemplos: 'America/Bogota', 'America/Quito', 'America/Lima', 'UTC', etc.
    TIMEZONE: str = os.getenv("TIMEZONE", "America/Bogota")
    
    # ========== PAGINACIÓN ==========
    PAGINATION_DEFAULT_PAGE: int = int(os.getenv("PAGINATION_DEFAULT_PAGE", "1"))
    PAGINATION_DEFAULT_PAGE_SIZE: int = int(os.getenv("PAGINATION_DEFAULT_PAGE_SIZE", "10"))
    PAGINATION_MAX_PAGE_SIZE: int = int(os.getenv("PAGINATION_MAX_PAGE_SIZE", "100"))
    
    # ========== SEGURIDAD - CONTRASEÑAS ==========
    # Política de validación de contraseñas (CV-20)
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_MAX_BYTES: int = int(os.getenv("PASSWORD_MAX_BYTES", "72"))
    PASSWORD_SPECIAL_CHARS: str = os.getenv("PASSWORD_SPECIAL_CHARS", "!@#$%^&*()_+-=[]{}|;:,.<>?")
    PASSWORD_MUST_HAVE_UPPER: bool = os.getenv("PASSWORD_MUST_HAVE_UPPER", "True").lower() == "true"
    PASSWORD_MUST_HAVE_DIGIT: bool = os.getenv("PASSWORD_MUST_HAVE_DIGIT", "True").lower() == "true"
    PASSWORD_MUST_HAVE_SPECIAL: bool = os.getenv("PASSWORD_MUST_HAVE_SPECIAL", "False").lower() == "true"
    
    # ========== SEGURIDAD - BIOMETRÍA ==========
    MAX_BIOMETRIC_FAILED_ATTEMPTS: int = int(os.getenv("MAX_BIOMETRIC_FAILED_ATTEMPTS", "2"))
    PHONE_RESPONSE_TIMEOUT_SECONDS: int = int(os.getenv("PHONE_RESPONSE_TIMEOUT_SECONDS", "30"))
    
    # ========== CÓDIGOS QR ==========
    QR_TOKEN_LENGTH: int = int(os.getenv("QR_TOKEN_LENGTH", "32"))
    QR_CODE_VALIDITY_MINUTES: int = int(os.getenv("QR_CODE_VALIDITY_MINUTES", "3"))
    
    # ========== LONGITUDES DE CAMPOS ==========
    FIELD_LENGTHS: dict = {
        'identification': 20,
        'phone': 15,
        'email': 100,
        'address': 120,
        'username': 50,
        'user_action': 20,
        'manzana': 10,
        'villa': 10,
    }
    
    # ========== CORS ==========
    CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
    ]
    
    # ========== LOGGING ==========
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    
    # ========== SERVER CONFIGURATION ==========
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_RELOAD: bool = os.getenv("APP_RELOAD", "True").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la instancia de configuración (con caché)"""
    return Settings()
