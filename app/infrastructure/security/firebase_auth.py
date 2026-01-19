"""
Autenticación con Firebase Auth
Middleware para validar JWT tokens de Firebase
"""

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.infrastructure.db.models import Cuenta, Persona
from typing import Optional
import os

# Simulación de Firebase (cambiar a importar firebase_admin cuando se configure)
class FirebaseAuth:
    """Placeholder para Firebase Auth"""
    
    @staticmethod
    def verify_id_token(token: str) -> dict:
        """
        Verifica un token JWT de Firebase
        En producción, usar firebase_admin
        """
        try:
            # Placeholder - implementar con firebase_admin
            # decoded = auth.verify_id_token(token)
            # return decoded
            
            # Por ahora retornar estructura esperada para testing
            if not token:
                raise ValueError("Token vacío")
            
            # En producción:
            # import firebase_admin
            # from firebase_admin import auth
            # decoded = auth.verify_id_token(token)
            # return decoded
            
            return {"uid": token, "email": f"user_{token}@example.com"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: {str(e)}"
            )


def obtener_usuario_autenticado(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency que valida el token JWT y retorna datos del usuario
    
    Uso:
        @router.get("/perfil")
        def get_perfil(usuario: dict = Depends(obtener_usuario_autenticado)):
            return {"usuario": usuario}
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere header Authorization"
        )
    
    # Formato esperado: "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Esquema debe ser Bearer")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato inválido. Use: Authorization: Bearer <token>"
        )
    
    # Verificar token
    firebase_auth = FirebaseAuth()
    decoded = firebase_auth.verify_id_token(token)
    firebase_uid = decoded.get("uid")
    
    # Obtener cuenta desde BD
    cuenta = db.query(Cuenta).filter(
        Cuenta.firebase_uid == firebase_uid,
        Cuenta.eliminado == False,
        Cuenta.estado == "activo"
    ).first()
    
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no tiene cuenta activa en el sistema"
        )
    
    # Obtener persona asociada
    persona = db.query(Persona).filter(Persona.persona_pk == cuenta.persona_titular_fk).first()
    
    return {
        "firebase_uid": firebase_uid,
        "cuenta_id": cuenta.cuenta_pk,
        "persona_id": persona.persona_pk,
        "nombres": f"{persona.nombres} {persona.apellidos}",
        "email": decoded.get("email"),
        "estado": cuenta.estado
    }


# Para testing sin Firebase configurado
def obtener_usuario_mock(
    usuario_id: Optional[int] = Header(None),
    db: Session = Depends(get_db)
) -> dict:
    """
    Mock para testing sin Firebase
    Uso en testing: Header(usuario_id=1)
    """
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere header usuario_id para testing"
        )
    
    cuenta = db.query(Cuenta).filter(Cuenta.cuenta_pk == usuario_id).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    persona = db.query(Persona).filter(Persona.persona_pk == cuenta.persona_titular_fk).first()
    
    return {
        "firebase_uid": cuenta.firebase_uid,
        "cuenta_id": cuenta.cuenta_pk,
        "persona_id": persona.persona_pk,
        "nombres": f"{persona.nombres} {persona.apellidos}",
        "estado": cuenta.estado
    }
