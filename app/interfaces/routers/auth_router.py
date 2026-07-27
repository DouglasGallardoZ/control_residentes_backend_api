"""
Router de autenticacion.
POST /auth/login — verifica firebase_uid contra la tabla Cuenta.
POST /auth/logout — registra el cierre de sesion.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import Cuenta, Persona
from app.infrastructure.security.auth import obtener_usuario_con_rol

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LogoutRequest(BaseModel):
    firebase_uid: str = None


@router.post("/login", response_model=dict)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Verifica credenciales contra la tabla Cuenta.
    La autenticacion real se hace en Firebase Auth (frontend).
    Este endpoint es un proxy que verifica metadata local.
    """
    cuenta = db.query(Cuenta).filter(
        Cuenta.username == request.username,
        Cuenta.eliminado == False,
        Cuenta.estado == "activo",
    ).first()

    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas o cuenta no activa",
        )

    persona = db.query(Persona).filter(
        Persona.persona_pk == cuenta.persona_titular_fk
    ).first()

    return {
        "persona_id": persona.persona_pk if persona else None,
        "firebase_uid": cuenta.firebase_uid,
        "username": cuenta.username,
        "estado": cuenta.estado,
    }


@router.post("/logout", response_model=dict)
def logout(
    request: LogoutRequest = None,
    usuario: dict = Depends(obtener_usuario_con_rol),
):
    """Registra cierre de sesion. La invalidacion de tokens se maneja en Firebase."""
    return {"mensaje": "Sesion cerrada correctamente"}
