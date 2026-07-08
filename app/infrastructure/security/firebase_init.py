"""
Inicializacion centralizada de Firebase Admin SDK.

Evita el error 'The default Firebase app already exists'
al tener un unico punto de inicializacion.
"""
import os
import firebase_admin
from firebase_admin import credentials
from app.config import get_settings

_initialized = False


def inicializar_firebase():
    """Inicializa Firebase Admin SDK una sola vez (idempotente)"""
    global _initialized

    if _initialized:
        return

    settings = get_settings()
    # credenciales_path = settings.FIREBASE_CREDENTIALS_PATH
    credenciales_path = "../../firebase-credentials.json"

    posibles_rutas = [
        credenciales_path,
        "firebase-credentials.json",
        "serviceAccountKey.json",
        os.path.join(os.path.dirname(__file__), "..", "..", "firebase-credentials.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "firebase-credentials.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "serviceAccountKey.json"),
    ]

    ruta_encontrada = None
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            ruta_encontrada = ruta
            break

    if not ruta_encontrada:
        raise FileNotFoundError(
            f"No se encontro el archivo de credenciales de Firebase.\n"
            f"Buscado en: {posibles_rutas}\n"
            f"Verifica FIREBASE_CREDENTIALS_PATH en .env"
        )

    try:
        cred = credentials.Certificate(ruta_encontrada)
        firebase_admin.initialize_app(cred)
        _initialized = True
        print(f"Firebase Admin inicializado con: {ruta_encontrada}")
    except ValueError as e:
        if "already exists" in str(e):
            _initialized = True
            print("Firebase Admin ya estaba inicializado")
        else:
            raise
