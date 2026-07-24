"""
Servicio de bitácora para auditoría de operaciones.
Registra CREAR, ACTUALIZAR, ELIMINAR, ACTIVAR, DESACTIVAR, BLOQUEAR, DESBLOQUEAR.
"""
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.infrastructure.db.models import Bitacora


class BitacoraService:

    def __init__(self, db: Session):
        self.db = db

    def registrar(
        self,
        persona_id: int,
        entidad: str,
        entidad_id: int,
        operacion: str,
        valor_anterior: any = None,
        valor_nuevo: any = None,
        descripcion: str = None,
    ) -> None:
        try:
            registro = Bitacora(
                entidad=entidad,
                entidad_id=str(entidad_id),
                operacion=operacion,
                persona_actor_fk=persona_id,
                valor_anterior=(
                    json.dumps(valor_anterior, default=str)
                    if valor_anterior is not None
                    else None
                ),
                valor_nuevo=(
                    json.dumps(valor_nuevo, default=str)
                    if valor_nuevo is not None
                    else None
                ),
                descripcion=descripcion,
            )
            self.db.add(registro)
        except Exception as e:
            print(f"Error registrando bitacora: {e}")
