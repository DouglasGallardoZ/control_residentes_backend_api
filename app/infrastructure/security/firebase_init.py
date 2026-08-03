"""
Inicializacion centralizada de Firebase Admin SDK.

Evita el error 'The default Firebase app already exists'
al tener un unico punto de inicializacion.

Soporta credenciales desde:
1. Variable de entorno FIREBASE_CREDENTIALS_JSON (contenido JSON completo)
2. Variable de entorno FIREBASE_CREDENTIALS_PATH (ruta al archivo)
3. Archivos en disco (busqueda en rutas conocidas)
"""
import json
import os
import tempfile
import firebase_admin
from firebase_admin import credentials
from app.config import get_settings

_initialized = False


def _credenciales_desde_env() -> str:
    """
    Si FIREBASE_CREDENTIALS_JSON esta definida, escribe el JSON a un
    archivo temporal y retorna su ruta. Retorna None si no esta definida.
    """
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not cred_json or not cred_json.strip():
        return None

    try:
        data = json.loads(cred_json)
    except json.JSONDecodeError as e:
        raise ValueError(
            "FIREBASE_CREDENTIALS_JSON no es un JSON valido. "
            "Verifica que el contenido este en una sola linea."
        ) from e

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", prefix="firebase-", delete=False
    )
    json.dump(data, tmp)
    tmp.close()
    return tmp.name


def inicializar_firebase():
    """Inicializa Firebase Admin SDK una sola vez (idempotente)"""
    global _initialized

    if _initialized:
        return

    settings = get_settings()
    credenciales_path = settings.FIREBASE_CREDENTIALS_PATH

    posibles_rutas = [
        credenciales_path,
        "../../firebase-credentials.json",
        "firebase-credentials.json",
        "serviceAccountKey.json",
        os.path.join(os.path.dirname(__file__), "..", "..", "firebase-credentials.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "firebase-credentials.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "serviceAccountKey.json"),
    ]

    # 1. Intentar credencial desde variable de entorno FIREBASE_CREDENTIALS_JSON
    ruta_encontrada = _credenciales_desde_env()

    # 2. Fallback: buscar archivo en disco
    if not ruta_encontrada:
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                ruta_encontrada = ruta
                break

    if not ruta_encontrada:
        raise FileNotFoundError(
            f"No se encontro el archivo de credenciales de Firebase.\n"
            f"Buscado en: {posibles_rutas}\n"
            f"Verifica FIREBASE_CREDENTIALS_PATH o FIREBASE_CREDENTIALS_JSON en .env"
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
