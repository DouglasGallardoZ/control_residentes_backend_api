import firebase_admin
from firebase_admin import credentials, firestore
from app.config import get_settings
from typing import Dict, Any, Optional

settings = get_settings()


class FirestoreClient:
    """Cliente para Firestore"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirestoreClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        try:
            # Inicializar Firebase
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID
            })
            self.db = firestore.client()
            self._initialized = True
        except Exception as e:
            print(f"Error inicializando Firestore: {e}")
            raise
    
    def crear_documento(
        self,
        coleccion: str,
        documento_id: str,
        datos: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea un documento en Firestore"""
        try:
            self.db.collection(coleccion).document(documento_id).set(datos)
            return {"exito": True, "documento_id": documento_id}
        except Exception as e:
            print(f"Error creando documento en Firestore: {e}")
            raise
    
    def actualizar_documento(
        self,
        coleccion: str,
        documento_id: str,
        datos: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Actualiza un documento en Firestore"""
        try:
            self.db.collection(coleccion).document(documento_id).update(datos)
            return {"exito": True, "documento_id": documento_id}
        except Exception as e:
            print(f"Error actualizando documento en Firestore: {e}")
            raise
    
    def obtener_documento(
        self,
        coleccion: str,
        documento_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene un documento de Firestore"""
        try:
            doc = self.db.collection(coleccion).document(documento_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error obteniendo documento de Firestore: {e}")
            raise
    
    def eliminar_documento(
        self,
        coleccion: str,
        documento_id: str
    ) -> Dict[str, Any]:
        """Elimina un documento de Firestore"""
        try:
            self.db.collection(coleccion).document(documento_id).delete()
            return {"exito": True, "documento_id": documento_id}
        except Exception as e:
            print(f"Error eliminando documento de Firestore: {e}")
            raise
    
    def obtener_coleccion(self, coleccion: str) -> list:
        """Obtiene todos los documentos de una colección"""
        try:
            docs = self.db.collection(coleccion).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error obteniendo colección de Firestore: {e}")
            raise


def get_firestore_client() -> FirestoreClient:
    """Obtiene instancia singleton de FirestoreClient"""
    return FirestoreClient()
