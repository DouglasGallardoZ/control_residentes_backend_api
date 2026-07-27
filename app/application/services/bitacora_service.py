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
        valor_anterior: any = " ",
        valor_nuevo: any = " ",
        descripcion: str = None,
    ) -> None:
        try:
            registro = Bitacora(
                entidad=entidad,
                entidad_id=str(entidad_id),
                operacion=operacion,
                persona_actor_fk=persona_id if persona_id else None,
                valor_anterior=(
                    json.dumps(valor_anterior, default=str)
                    if valor_anterior != " "
                    else " "
                ),
                valor_nuevo=(
                    json.dumps(valor_nuevo, default=str)
                    if valor_nuevo != " "
                    else " "
                ),
                descripcion=descripcion,
            )
            self.db.add(registro)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error registrando bitacora: {e}")
