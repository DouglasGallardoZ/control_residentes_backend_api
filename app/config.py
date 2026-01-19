import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Base de datos
    DATABASE_URL: str = "postgresql://admin:password123@localhost:5432/urbanizacion_db"
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
