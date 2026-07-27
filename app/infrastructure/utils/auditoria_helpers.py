"""
Helper universal para registrar bitácora desde cualquier endpoint.
Uso:
    from app.infrastructure.utils.auditoria_helpers import registrar_bitacora
    registrar_bitacora(db, usuario, "entidad", entidad_id, "operacion", descripcion)
"""
from sqlalchemy.orm import Session
from typing import Optional


def obtener_email_auditoria(current_user=None, usuario: Optional[dict] = None) -> str:
    if current_user and hasattr(current_user, "persona") and current_user.persona:
        return current_user.persona.correo or "admin@gmail.com"
    if current_user and hasattr(current_user, "correo"):
        return current_user.correo or "admin@gmail.com"
    if usuario and isinstance(usuario, dict):
        return usuario.get("email", "") or "admin@gmail.com"
    return "admin@gmail.com"


def obtener_usuario_auditoria(current_user=None, usuario: Optional[dict] = None) -> str:
    return obtener_email_auditoria(current_user, usuario)


def registrar_bitacora(
    db: Session,
    usuario: dict,
    entidad: str,
    entidad_id: int,
    operacion: str,
    descripcion: Optional[str] = None,
    valor_anterior: Optional[str] = " ",
    valor_nuevo: Optional[str] = " ",
) -> None:
    """Registra en bitácora sin lanzar excepciones. NUNCA rompe el flujo."""
    try:
        from app.application.services.bitacora_service import BitacoraService

        persona_id = usuario.get("persona_id", 0) if usuario else 0
        email = obtener_email_auditoria(usuario=usuario)
        desc = descripcion or f"{operacion} en {entidad}/{entidad_id} por {email}"

        BitacoraService(db).registrar(
            persona_id=persona_id,
            entidad=entidad,
            entidad_id=entidad_id,
            operacion=operacion,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            descripcion=desc,
        )
    except Exception as e:
        print(f"Error bitacora {entidad}/{operacion}: {e}")
