from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.infrastructure.db.models import Cuenta, Persona, MiembroVivienda, EventoCuenta, ResidenteVivienda
from app.interfaces.schemas.schemas import PerfilUsuarioResponse, ViviendaInfo
from datetime import datetime
from pydantic import BaseModel
from app.infrastructure.utils.time_utils import ahora_sin_tz

router = APIRouter(prefix="/api/v1/cuentas", tags=["Cuentas"])


class CuentaFirebaseCreate(BaseModel):
    """Schema para crear cuenta con Firebase UID"""
    persona_id: int
    firebase_uid: str
    username: str
    usuario_creado: str = "api_user"


@router.post("/residente/firebase", response_model=dict)
def crear_cuenta_residente_firebase(
    request: CuentaFirebaseCreate,
    db: Session = Depends(get_db)
):
    """
    Crea cuenta para residente después de registrarse en Firebase
    RF-C01: Crear cuenta de residente
    
    Flujo:
    1. Usuario se registra en Firebase Auth (email/password)
    2. Firebase devuelve firebase_uid
    3. Flutter llama este endpoint
    4. API crea metadata local
    """
    try:
        # Validar que persona existe y es residente activo
        persona = db.query(Persona).filter(Persona.persona_pk == request.persona_id).first()
        if not persona or persona.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Residente no encontrado o inactivo"
            )
        
        # Validar que es residente (existe en ResidenteVivienda)
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == request.persona_id,
            ResidenteVivienda.estado == "activo"
        ).first()
        
        if not residente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Persona no es residente activo"
            )
        
        # Validar que no exista cuenta previa
        cuenta_existente = db.query(Cuenta).filter(
            Cuenta.persona_titular_fk == request.persona_id
        ).first()
        if cuenta_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cuenta ya existe para este residente"
            )
        
        # Validar firebase_uid único
        firebase_existente = db.query(Cuenta).filter(
            Cuenta.firebase_uid == request.firebase_uid
        ).first()
        if firebase_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Firebase UID ya está registrado en otra cuenta"
            )
        
        # Crear cuenta
        cuenta = Cuenta(
            persona_titular_fk=request.persona_id,
            username=request.username,
            firebase_uid=request.firebase_uid,
            estado="activo",
            usuario_creado=request.usuario_creado
        )
        
        db.add(cuenta)
        db.flush()
        
        # Registrar evento
        evento = EventoCuenta(
            cuenta_afectada_fk=cuenta.cuenta_pk,
            tipo_evento="cuenta_creada",
            usuario_creado=request.usuario_creado
        )
        db.add(evento)
        
        db.commit()
        db.refresh(cuenta)
        
        return {
            "id": cuenta.cuenta_pk,
            "firebase_uid": cuenta.firebase_uid,
            "persona_id": persona.persona_pk,
            "nombres": f"{persona.nombres} {persona.apellidos}",
            "mensaje": "Cuenta de residente creada exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/miembro/firebase", response_model=dict)
def crear_cuenta_miembro_familia_firebase(
    request: CuentaFirebaseCreate,
    db: Session = Depends(get_db)
):
    """
    Crea cuenta para miembro de familia después de registrarse en Firebase
    RF-C01 (extensión para miembros)
    
    Flujo:
    1. Usuario (miembro de familia) se registra en Firebase Auth
    2. Firebase devuelve firebase_uid
    3. Flutter llama este endpoint
    4. API crea metadata local
    """
    try:
        # Validar que persona existe
        persona = db.query(Persona).filter(Persona.persona_pk == request.persona_id).first()
        if not persona or persona.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona no encontrada o inactiva"
            )
        
        # Validar que es miembro de familia activo
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.persona_miembro_fk == request.persona_id,
            MiembroVivienda.estado == "activo",
            MiembroVivienda.eliminado == False
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Persona no es miembro de familia activo"
            )
        
        # Validar que no exista cuenta previa
        cuenta_existente = db.query(Cuenta).filter(
            Cuenta.persona_titular_fk == request.persona_id
        ).first()
        if cuenta_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cuenta ya existe para este miembro"
            )
        
        # Validar firebase_uid único
        firebase_existente = db.query(Cuenta).filter(
            Cuenta.firebase_uid == request.firebase_uid
        ).first()
        if firebase_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Firebase UID ya está registrado en otra cuenta"
            )
        
        # Crear cuenta
        cuenta = Cuenta(
            persona_titular_fk=request.persona_id,
            username=request.username,
            firebase_uid=request.firebase_uid,
            estado="activo",
            usuario_creado=request.usuario_creado
        )
        
        db.add(cuenta)
        db.flush()
        
        # Registrar evento
        evento = EventoCuenta(
            cuenta_afectada_fk=cuenta.cuenta_pk,
            tipo_evento="cuenta_creada",
            usuario_creado=request.usuario_creado
        )
        db.add(evento)
        
        db.commit()
        db.refresh(cuenta)
        
        return {
            "id": cuenta.cuenta_pk,
            "firebase_uid": cuenta.firebase_uid,
            "persona_id": persona.persona_pk,
            "nombres": f"{persona.nombres} {persona.apellidos}",
            "mensaje": "Cuenta de miembro de familia creada exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{cuenta_id}/bloquear", response_model=dict)
def bloquear_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,
    motivo: str = "Cuenta bloqueada",
    db: Session = Depends(get_db)
):
    """
    Bloquea una cuenta individual
    RF-C07
    """
    try:
        cuenta = db.query(Cuenta).filter(Cuenta.cuenta_pk == cuenta_id).first()
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )
        
        if cuenta.estado == "inactivo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta ya se encuentra inactiva"
            )
        
        # Bloquear cuenta
        cuenta.estado = "inactivo"
        cuenta.fecha_actualizado = ahora_sin_tz()
        cuenta.usuario_actualizado = usuario_actualizado
        
        # Registrar evento
        evento = EventoCuenta(
            cuenta_afectada_fk=cuenta.cuenta_pk,
            tipo_evento="cuenta_bloqueada",
            motivo=motivo,
            usuario_creado=usuario_actualizado
        )
        db.add(evento)
        
        db.commit()
        
        return {
            "mensaje": "La cuenta ha sido bloqueada correctamente",
            "cuenta_id": cuenta_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{cuenta_id}/desbloquear", response_model=dict)
def desbloquear_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,
    motivo: str = "Cuenta desbloqueada",
    db: Session = Depends(get_db)
):
    """
    Desbloquea una cuenta individual
    RF-C08
    """
    try:
        cuenta = db.query(Cuenta).filter(Cuenta.cuenta_pk == cuenta_id).first()
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )
        
        if cuenta.estado == "activo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta ya se encuentra activa"
            )
        
        # Desbloquear cuenta
        cuenta.estado = "activo"
        cuenta.fecha_actualizado = ahora_sin_tz()
        cuenta.usuario_actualizado = usuario_actualizado
        
        # Registrar evento
        evento = EventoCuenta(
            cuenta_afectada_fk=cuenta.cuenta_pk,
            tipo_evento="cuenta_desbloqueada",
            motivo=motivo,
            usuario_creado=usuario_actualizado
        )
        db.add(evento)
        
        db.commit()
        
        return {
            "mensaje": "La cuenta ha sido desbloqueada correctamente",
            "cuenta_id": cuenta_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{cuenta_id}", response_model=dict)
def eliminar_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,
    motivo: str = "Cuenta eliminada",
    db: Session = Depends(get_db)
):
    """
    Elimina una cuenta de forma permanente (soft delete)
    RF-C09
    """
    try:
        cuenta = db.query(Cuenta).filter(Cuenta.cuenta_pk == cuenta_id).first()
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )
        
        if cuenta.eliminado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta ya ha sido eliminada"
            )
        
        # Marcar como eliminado (soft delete)
        cuenta.eliminado = True
        cuenta.motivo_eliminado = motivo
        cuenta.fecha_actualizado = ahora_sin_tz()
        cuenta.usuario_actualizado = usuario_actualizado
        
        # Registrar evento
        evento = EventoCuenta(
            cuenta_afectada_fk=cuenta.cuenta_pk,
            tipo_evento="cuenta_eliminada",
            motivo=motivo,
            usuario_creado=usuario_actualizado
        )
        db.add(evento)
        
        db.commit()
        
        return {
            "mensaje": "Cuenta eliminada permanentemente",
            "cuenta_id": cuenta_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/perfil/{firebase_uid}", response_model=PerfilUsuarioResponse)
def obtener_perfil_usuario(
    firebase_uid: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene la información completa del perfil de un usuario basado en su Firebase UID
    
    Retorna:
    - Información personal (nombres, identificación, correo, celular)
    - Rol (Residente o Miembro de Familia)
    - Información de vivienda (manzana y villa)
    - Parentesco (si es miembro de familia)
    - Estado y fecha de creación
    """
    try:
        # Obtener cuenta por Firebase UID
        cuenta = db.query(Cuenta).filter(
            Cuenta.firebase_uid == firebase_uid,
            Cuenta.estado == "activo",
            Cuenta.eliminado == False
        ).first()
        
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )
        
        # Obtener persona
        persona = db.query(Persona).filter(
            Persona.persona_pk == cuenta.persona_titular_fk
        ).first()
        
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Persona no encontrada en BD"
            )
        
        # Determinar rol y obtener información de vivienda
        rol = None
        parentesco = None
        vivienda = None
        
        # Verificar si es residente
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == persona.persona_pk,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).first()
        
        if residente:
            rol = "residente"
            vivienda = residente.vivienda
        else:
            # Verificar si es miembro de familia
            miembro = db.query(MiembroVivienda).filter(
                MiembroVivienda.persona_miembro_fk == persona.persona_pk,
                MiembroVivienda.estado == "activo",
                MiembroVivienda.eliminado == False
            ).first()
            
            if miembro:
                rol = "miembro_familia"
                parentesco = miembro.parentesco
                vivienda = miembro.vivienda
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no es residente ni miembro de familia activo"
                )
        
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vivienda no encontrada"
            )
        
        return PerfilUsuarioResponse(
            persona_id=persona.persona_pk,
            identificacion=persona.identificacion,
            nombres=persona.nombres,
            apellidos=persona.apellidos,
            correo=persona.correo,
            celular=persona.celular,
            estado=persona.estado,
            rol=rol,
            vivienda=ViviendaInfo(
                manzana=vivienda.manzana,
                villa=vivienda.villa
            ),
            parentesco=parentesco,
            fecha_creado=persona.fecha_creado
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
