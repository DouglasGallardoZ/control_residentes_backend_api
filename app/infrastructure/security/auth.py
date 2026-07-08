"""
Modulo de autenticacion centralizado.
Usa Firebase Auth para validar tokens y obtener roles desde la BD.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth

from app.infrastructure.security.firebase_init import inicializar_firebase
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.models import Cuenta, Admin, ResidenteVivienda, MiembroVivienda, Persona

try:
    inicializar_firebase()
except Exception as e:
    print(f"ADVERTENCIA: No se pudo inicializar Firebase: {e}")
    print("  Los endpoints protegidos fallaran sin credenciales validas.")

security = HTTPBearer()


async def obtener_usuario_firebase(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Valida el token de Firebase y retorna los datos del usuario.
    """
    token = credentials.credentials

    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "firebase_uid": decoded_token.get("uid"),
        }
    except firebase_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except firebase_auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )
    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error autenticando con Firebase: {str(e)}",
        )


async def obtener_usuario_con_rol(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Obtiene el usuario autenticado con su rol desde la base de datos.

    Retorna:
        {firebase_uid, email, persona_id, rol, nombres, cuenta_id}
    """
    usuario_firebase = await obtener_usuario_firebase(credentials)
    firebase_uid = usuario_firebase.get("firebase_uid")

    db = SessionLocal()
    try:
        cuenta = db.query(Cuenta).filter(
            Cuenta.firebase_uid == firebase_uid,
            Cuenta.eliminado == False,
        ).first()

        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada en el sistema",
            )

        persona_id = cuenta.persona_titular_fk

        rol = "desconocido"
        admin = db.query(Admin).filter(
            Admin.persona_admin_fk == persona_id,
            Admin.estado == "activo",
            Admin.eliminado == False,
        ).first()
        if admin:
            rol = "admin"

        if rol == "desconocido":
            residente = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.persona_residente_fk == persona_id,
                ResidenteVivienda.estado == "activo",
                ResidenteVivienda.eliminado == False,
            ).first()
            if residente:
                rol = "residente"

        if rol == "desconocido":
            miembro = db.query(MiembroVivienda).filter(
                MiembroVivienda.persona_miembro_fk == persona_id,
                MiembroVivienda.estado == "activo",
                MiembroVivienda.eliminado == False,
            ).first()
            if miembro:
                rol = "miembro_familia"

        persona = db.query(Persona).filter(
            Persona.persona_pk == persona_id
        ).first()
        nombres = (
            f"{persona.nombres} {persona.apellidos}" if persona else ""
        )

        return {
            "firebase_uid": firebase_uid,
            "email": usuario_firebase.get("email"),
            "persona_id": persona_id,
            "rol": rol,
            "nombres": nombres,
            "cuenta_id": cuenta.cuenta_pk,
        }
    finally:
        db.close()


obtener_usuario_actual = obtener_usuario_con_rol


def requerir_rol(*roles_permitidos: str):
    """
    Dependency factory que verifica que el usuario tenga
    uno de los roles permitidos.

    Uso:
        @router.get("/admin")
        async def ruta_admin(
            usuario: dict = Depends(requerer_rol("admin"))
        ):
            ...
    """

    async def verificador_rol(
        usuario: dict = Depends(obtener_usuario_con_rol),
    ) -> dict:
        rol = usuario.get("rol", "desconocido")
        if rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso denegado. Se requiere rol: {roles_permitidos}. "
                    f"Rol actual: {rol}"
                ),
            )
        return usuario

    return verificador_rol
