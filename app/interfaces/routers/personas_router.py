from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.infrastructure.db.models import Persona
from app.infrastructure.security.auth import requerir_rol

router = APIRouter(prefix="/api/v1/personas", tags=["Personas"])


@router.get("/buscar/{identificacion}", response_model=dict)
def buscar_persona(
    identificacion: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """
    Busca una persona por su numero de identificacion.
    No retorna 404 si no existe: retorna 200 con encontrada=false.
    """
    persona = db.query(Persona).filter(
        Persona.identificacion == identificacion,
        Persona.eliminado == False,
    ).first()

    if persona:
        return {
            "encontrada": True,
            "persona": {
                "persona_id": persona.persona_pk,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "identificacion": persona.identificacion,
                "correo": persona.correo,
                "celular": persona.celular,
            },
        }
    return {"encontrada": False, "persona": None}
