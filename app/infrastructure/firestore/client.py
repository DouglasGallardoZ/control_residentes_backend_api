"""
Cliente de Firestore para el modulo de notificaciones.
Maneja tokens FCM y estado de lectura en tiempo real.
"""
import os
from typing import Optional, List, Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore

from app.infrastructure.security.firebase_init import inicializar_firebase


class FirestoreClient:
    """Singleton para manejar la conexion a Firestore"""

    _instance = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._db is not None:
            return
        try:
            inicializar_firebase()
            self._db = firestore.client()
            print("Firestore inicializado correctamente")
        except Exception as e:
            print(f"Error inicializando Firestore: {e}")
            self._db = None

    @property
    def db(self):
        if self._db is None:
            raise RuntimeError("Firestore no esta inicializado")
        return self._db

    async def guardar_documento(
        self, coleccion: str, doc_id: str, datos: dict
    ) -> None:
        """Guarda o actualiza un documento en Firestore"""
        try:
            self.db.collection(coleccion).document(doc_id).set(datos, merge=True)
        except Exception as e:
            print(f"Firestore: error guardando {coleccion}/{doc_id}: {e}")

    async def obtener_documento(
        self, coleccion: str, doc_id: str
    ) -> Optional[dict]:
        """Obtiene un documento de Firestore"""
        try:
            doc = self.db.collection(coleccion).document(doc_id).get()
            if doc.exists:
                return {"id": doc.id, **doc.to_dict()}
            return None
        except Exception as e:
            print(f"Firestore: error obteniendo {coleccion}/{doc_id}: {e}")
            return None

    async def guardar_subdocumento(
        self,
        coleccion: str,
        doc_id: str,
        subcoleccion: str,
        subdoc_id: str,
        datos: dict,
    ) -> None:
        """Guarda un documento en una subcoleccion"""
        try:
            ref = (
                self.db.collection(coleccion)
                .document(doc_id)
                .collection(subcoleccion)
                .document(subdoc_id)
            )
            ref.set(datos, merge=True)
        except Exception as e:
            print(
                f"Firestore: error guardando "
                f"{coleccion}/{doc_id}/{subcoleccion}/{subdoc_id}: {e}"
            )

    async def obtener_subcoleccion(
        self, coleccion: str, doc_id: str, subcoleccion: str
    ) -> List[dict]:
        """Obtiene todos los documentos de una subcoleccion"""
        try:
            docs = (
                self.db.collection(coleccion)
                .document(doc_id)
                .collection(subcoleccion)
                .stream()
            )
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(
                f"Firestore: error obteniendo "
                f"{coleccion}/{doc_id}/{subcoleccion}: {e}"
            )
            return []

    async def eliminar_documento(self, coleccion: str, doc_id: str) -> None:
        """Elimina un documento de Firestore"""
        try:
            self.db.collection(coleccion).document(doc_id).delete()
        except Exception as e:
            print(f"Firestore: error eliminando {coleccion}/{doc_id}: {e}")

    def obtener_coleccion(self, coleccion: str) -> list:
        """Obtiene todos los documentos de una coleccion (sync, para compatibilidad)"""
        try:
            docs = self.db.collection(coleccion).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Firestore: error obteniendo coleccion {coleccion}: {e}")
            return []

    def crear_documento(
        self, coleccion: str, documento_id: str, datos: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea un documento en Firestore (sync, compatibilidad)"""
        try:
            self.db.collection(coleccion).document(documento_id).set(datos)
            return {"exito": True, "documento_id": documento_id}
        except Exception as e:
            print(f"Firestore: error creando {coleccion}/{documento_id}: {e}")
            raise
