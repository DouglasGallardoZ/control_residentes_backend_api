#!/usr/bin/env python3
"""
Script para validar la configuración de variables de entorno
Ejecutar: python validate_config.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings


def main():
    """Valida y muestra la configuración actual"""
    print("=" * 70)
    print("VALIDACIÓN DE CONFIGURACIÓN - VARIABLES DE ENTORNO")
    print("=" * 70)
    
    try:
        settings = get_settings()
        
        print("\n✓ Configuración cargada correctamente\n")
        
        # Database
        print("DATABASE:")
        print(f"  Host: {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"  User: {settings.DB_USER}")
        print(f"  Database: {settings.DB_NAME}")
        print(f"  URL: {settings.DATABASE_URL[:50]}..." if len(settings.DATABASE_URL) > 50 else f"  URL: {settings.DATABASE_URL}")
        
        # API
        print("\nAPI:")
        print(f"  Title: {settings.API_TITLE}")
        print(f"  Version: {settings.API_VERSION}")
        print(f"  Host: {settings.APP_HOST}")
        print(f"  Port: {settings.APP_PORT}")
        print(f"  Reload: {settings.APP_RELOAD}")
        
        # Firebase
        print("\nFIREBASE:")
        print(f"  Project ID: {settings.FIREBASE_PROJECT_ID}")
        print(f"  Credentials Path: {settings.FIREBASE_CREDENTIALS_PATH}")
        
        # Security
        print("\nSEGURIDAD:")
        print(f"  Password Min Length: {settings.PASSWORD_MIN_LENGTH}")
        print(f"  Password Must Have Upper: {settings.PASSWORD_MUST_HAVE_UPPER}")
        print(f"  Password Must Have Digit: {settings.PASSWORD_MUST_HAVE_DIGIT}")
        print(f"  Max Biometric Attempts: {settings.MAX_BIOMETRIC_FAILED_ATTEMPTS}")
        
        # Paginación
        print("\nPAGINACIÓN:")
        print(f"  Default Page Size: {settings.PAGINATION_DEFAULT_PAGE_SIZE}")
        print(f"  Max Page Size: {settings.PAGINATION_MAX_PAGE_SIZE}")
        
        # CORS
        print("\nCORS ORIGINS:")
        for origin in settings.CORS_ORIGINS:
            print(f"  - {origin}")
        
        # Timezone
        print("\nTIMEZONE:")
        print(f"  {settings.TIMEZONE}")
        
        # QR
        print("\nQR:")
        print(f"  Token Length: {settings.QR_TOKEN_LENGTH}")
        print(f"  Validity Minutes: {settings.QR_CODE_VALIDITY_MINUTES}")
        
        # Logging
        print("\nLOGGING:")
        print(f"  Level: {settings.LOG_LEVEL}")
        print(f"  SQLAlchemy Echo: {settings.SQLALCHEMY_ECHO}")
        
        print("\n" + "=" * 70)
        print("✓ TODAS LAS CONFIGURACIONES VÁLIDAS")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("✗ ERROR EN LA CONFIGURACIÓN")
        print("=" * 70)
        print(f"\n❌ {type(e).__name__}: {str(e)}\n")
        print("Asegúrate de que:")
        print("  1. El archivo .env existe en la raíz del proyecto")
        print("  2. Todas las variables están correctamente formateadas")
        print("  3. Las variables enteras están en formato numérico")
        print("  4. Las variables booleanas son 'True' o 'False' (case-sensitive)")
        print("\nEjemplo de .env:")
        print("  DB_HOST=localhost")
        print("  DB_PORT=5432")
        print("  PASSWORD_MUST_HAVE_UPPER=True")
        print("  CORS_ORIGINS=http://localhost:3000,http://localhost:8080")
        print("\n" + "=" * 70)
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
