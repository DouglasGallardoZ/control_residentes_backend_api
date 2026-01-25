from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.infrastructure.db.models import Cuenta, Persona, MiembroVivienda, EventoCuenta, ResidenteVivienda, Vivienda, PropietarioVivienda, Admin
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


class BloquearDesbloquearRequest(BaseModel):
    """Schema para bloquear/desbloquear cuenta"""
    usuario_actualizado: str
    motivo: str = "Cuenta modificada"
    cascada: bool = True  # True = bloquea/desbloquea miembros si es residente, False = solo esa cuenta


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
    request: BloquearDesbloquearRequest,
    db: Session = Depends(get_db)
):
    """
    Bloquea una cuenta individual (RFC-C07)
    Si es residente y cascada=true, también bloquea miembros de familia (RFC-C05)
    Si cascada=false, bloquea SOLO esa cuenta sin cascada
    """
    try:
        cuenta_principal = db.query(Cuenta).filter(Cuenta.persona_titular_fk == cuenta_id).first()
        if not cuenta_principal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )
        
        if cuenta_principal.estado == "inactivo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta ya se encuentra inactiva"
            )
        
        cuentas_a_bloquear = [cuenta_principal]
        vivienda_id = None
        es_residente = False
        cascada_aplicada = False
        
        # Si cascada=true, verificar si es residente y obtener miembros
        if request.cascada:
            # Obtener persona titular
            persona = db.query(Persona).filter(
                Persona.persona_pk == cuenta_principal.persona_titular_fk
            ).first()
            
            # Verificar si es residente activo
            residente = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.persona_residente_fk == persona.persona_pk,
                ResidenteVivienda.estado == "activo"
            ).first()
            
            if residente:
                es_residente = True
                vivienda_id = residente.vivienda_reside_fk
                cascada_aplicada = True
                
                # Obtener todos los miembros de esa vivienda
                miembros = db.query(MiembroVivienda).filter(
                    MiembroVivienda.vivienda_familia_fk == vivienda_id,
                    MiembroVivienda.estado == "activo"
                ).all()
                
                # Obtener cuentas de cada miembro
                for miembro in miembros:
                    cuenta_miembro = db.query(Cuenta).filter(
                        Cuenta.persona_titular_fk == miembro.persona_miembro_fk,
                        Cuenta.estado == "activo"
                    ).first()
                    
                    if cuenta_miembro:
                        cuentas_a_bloquear.append(cuenta_miembro)
        
        # Bloquear todas las cuentas
        for cuenta in cuentas_a_bloquear:
            cuenta.estado = "inactivo"
            cuenta.fecha_actualizado = ahora_sin_tz()
            cuenta.usuario_actualizado = request.usuario_actualizado
            
            evento = EventoCuenta(
                cuenta_afectada_fk=cuenta.cuenta_pk,
                tipo_evento="cuenta_bloqueada",
                motivo=request.motivo,
                usuario_creado=request.usuario_actualizado
            )
            db.add(evento)
        
        db.commit()
        
        return {
            "mensaje": f"Se han bloqueado {len(cuentas_a_bloquear)} cuenta(s)",
            "cuentas_bloqueadas": len(cuentas_a_bloquear),
            "cuenta_principal_id": cuenta_id,
            "es_residente": es_residente,
            "cascada_solicitada": request.cascada,
            "cascada_aplicada": cascada_aplicada,
            "vivienda_id": vivienda_id
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
    request: BloquearDesbloquearRequest,
    db: Session = Depends(get_db)
):
    """
    Desbloquea una cuenta individual (RFC-C08)
    Si es residente y cascada=true, también desbloquea miembros de familia (RFC-C06)
    Si cascada=false, desbloquea SOLO esa cuenta sin cascada
    """
    try:
        cuenta_principal = db.query(Cuenta).filter(Cuenta.persona_titular_fk == cuenta_id).first()
        if not cuenta_principal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta no encontrada"
            )
        
        if cuenta_principal.estado == "activo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta ya se encuentra activa"
            )
        
        cuentas_a_desbloquear = [cuenta_principal]
        vivienda_id = None
        es_residente = False
        cascada_aplicada = False
        
        # Si cascada=true, verificar si es residente y obtener miembros
        if request.cascada:
            # Obtener persona titular
            persona = db.query(Persona).filter(
                Persona.persona_pk == cuenta_principal.persona_titular_fk
            ).first()
            
            # Verificar si es residente activo
            residente = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.persona_residente_fk == persona.persona_pk,
                ResidenteVivienda.estado == "activo"
            ).first()
            
            if residente:
                es_residente = True
                vivienda_id = residente.vivienda_reside_fk
                cascada_aplicada = True
                
                # Obtener todos los miembros de esa vivienda
                miembros = db.query(MiembroVivienda).filter(
                    MiembroVivienda.vivienda_familia_fk == vivienda_id,
                    MiembroVivienda.estado == "activo"
                ).all()
                
                # Obtener cuentas de cada miembro
                for miembro in miembros:
                    cuenta_miembro = db.query(Cuenta).filter(
                        Cuenta.persona_titular_fk == miembro.persona_miembro_fk,
                        Cuenta.estado == "inactivo"
                    ).first()
                    
                    if cuenta_miembro:
                        cuentas_a_desbloquear.append(cuenta_miembro)
        
        # Desbloquear todas las cuentas
        for cuenta in cuentas_a_desbloquear:
            cuenta.estado = "activo"
            cuenta.fecha_actualizado = ahora_sin_tz()
            cuenta.usuario_actualizado = request.usuario_actualizado
            
            evento = EventoCuenta(
                cuenta_afectada_fk=cuenta.cuenta_pk,
                tipo_evento="cuenta_desbloqueada",
                motivo=request.motivo,
                usuario_creado=request.usuario_actualizado
            )
            db.add(evento)
        
        db.commit()
        
        return {
            "mensaje": f"Se han desbloqueado {len(cuentas_a_desbloquear)} cuenta(s)",
            "cuentas_desbloqueadas": len(cuentas_a_desbloquear),
            "cuenta_principal_id": cuenta_id,
            "es_residente": es_residente,
            "cascada_solicitada": request.cascada,
            "cascada_aplicada": cascada_aplicada,
            "vivienda_id": vivienda_id
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


@router.get("/perfil/{firebase_uid}", response_model=dict)
def obtener_perfil_usuario(
    firebase_uid: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene la información completa del perfil de un usuario basado en su Firebase UID
    
    Retorna:
    - Información personal (nombres, identificación, correo, celular)
    - Rol (Residente, Miembro de Familia, o Admin)
    - Información de vivienda (manzana y villa) - si aplica
    - Parentesco (si es miembro de familia)
    - Estado y fecha de creación
    
    Soporta:
    - Residentes con vivienda
    - Miembros de familia con vivienda
    - Admins/Usuarios con solo cuenta+persona (sin vivienda)
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
        vivienda_info = None
        
        # Verificar si es residente
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == persona.persona_pk,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).first()
        
        if residente:
            rol = "residente"
            vivienda = residente.vivienda
            if vivienda:
                vivienda_info = {
                    "vivienda_id": vivienda.vivienda_pk,
                    "manzana": vivienda.manzana,
                    "villa": vivienda.villa
                }
        else:
            # Verificar si es propietario (también tiene rol residente)
            propietario = db.query(PropietarioVivienda).filter(
                PropietarioVivienda.persona_propietario_fk == persona.persona_pk,
                PropietarioVivienda.estado == "activo",
                PropietarioVivienda.eliminado == False
            ).first()
            
            if propietario:
                rol = "residente"
                vivienda = propietario.vivienda
                if vivienda:
                    vivienda_info = {
                        "vivienda_id": vivienda.vivienda_pk,
                        "manzana": vivienda.manzana,
                        "villa": vivienda.villa
                    }
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
                    if vivienda:
                        vivienda_info = {
                            "vivienda_id": vivienda.vivienda_pk,
                            "manzana": vivienda.manzana,
                            "villa": vivienda.villa
                        }
                else:
                    # Verificar si es admin
                    admin = db.query(Admin).filter(
                        Admin.persona_admin_fk == persona.persona_pk,
                        Admin.estado == "activo",
                        Admin.eliminado == False
                    ).first()
                    
                    if admin:
                        rol = "admin"
                    else:
                        # No tiene rol válido
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Usuario no tiene un rol válido (residente, propietario, miembro de familia o admin)"
                        )
        
        # Construir respuesta
        respuesta = {
            "persona_id": persona.persona_pk,
            "identificacion": persona.identificacion,
            "nombres": persona.nombres,
            "apellidos": persona.apellidos,
            "correo": persona.correo,
            "celular": persona.celular,
            "estado": persona.estado,
            "rol": rol,
            "vivienda": vivienda_info,
            "parentesco": parentesco,
            "fecha_creado": persona.fecha_creado.isoformat() if persona.fecha_creado else None
        }
        
        return respuesta
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.get("/usuario/por-correo/{correo}", response_model=dict)
def obtener_usuario_por_correo(
    correo: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene la información de un usuario por su correo electrónico
    Busca en personas que tengan cuenta activa
    """
    try:
        # Obtener persona por correo
        persona = db.query(Persona).filter(
            Persona.correo == correo,
            Persona.estado == "activo"
        ).first()
        
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado con ese correo"
            )
        
        # Obtener cuenta asociada
        cuenta = db.query(Cuenta).filter(
            Cuenta.persona_titular_fk == persona.persona_pk,
            # Cuenta.estado == "activo",
            Cuenta.eliminado == False
        ).first()
        
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no tiene una cuenta activa"
            )
        
        # Determinar rol
        rol = None
        parentesco = None
        vivienda_info = None
        
        # Verificar si es residente
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == persona.persona_pk,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).first()
        
        if residente:
            rol = "residente"
            vivienda = residente.vivienda
            if vivienda:
                vivienda_info = {
                    "vivienda_id": vivienda.vivienda_pk,
                    "manzana": vivienda.manzana,
                    "villa": vivienda.villa
                }
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
                if vivienda:
                    vivienda_info = {
                        "vivienda_id": vivienda.vivienda_pk,
                        "manzana": vivienda.manzana,
                        "villa": vivienda.villa
                    }
            else:
                rol = "admin"
        
        resultado = {
            "usuario_id": cuenta.cuenta_pk,
            "persona_id": persona.persona_pk,
            "identificacion": persona.identificacion,
            "nombres": persona.nombres,
            "apellidos": persona.apellidos,
            "correo": persona.correo,
            "celular": persona.celular,
            "tipo": rol,
            "estado": cuenta.estado
        }
        
        # Agregar parentesco si es miembro de familia
        if parentesco:
            resultado["parentesco"] = parentesco
        
        return resultado
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/vivienda/{manzana}/{villa}/usuarios", response_model=dict)
def obtener_usuarios_vivienda(
    manzana: str,
    villa: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los usuarios (residentes y miembros con cuenta) de una vivienda por manzana y villa
    """
    try:
        # Obtener vivienda
        vivienda = db.query(Vivienda).filter(
            Vivienda.manzana == manzana,
            Vivienda.villa == villa,
            Vivienda.estado == "activo"
        ).first()
        
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        usuarios = []
        
        # Obtener residentes con cuenta
        residentes = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.vivienda_reside_fk == vivienda.vivienda_pk,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).all()
        
        for residente in residentes:
            cuenta = db.query(Cuenta).filter(
                Cuenta.persona_titular_fk == residente.persona_residente_fk,
                # Cuenta.estado == "activo",
                Cuenta.eliminado == False
            ).first()
            
            if cuenta:
                persona = residente.persona
                usuarios.append({
                    "usuario_id": cuenta.cuenta_pk,
                    "persona_id": persona.persona_pk,
                    "identificacion": persona.identificacion,
                    "nombres": persona.nombres,
                    "apellidos": persona.apellidos,
                    "correo": persona.correo,
                    "celular": persona.celular,
                    "tipo": "residente",
                    "estado": cuenta.estado
                })
        
        # Obtener miembros de familia con cuenta
        miembros = db.query(MiembroVivienda).filter(
            MiembroVivienda.vivienda_familia_fk == vivienda.vivienda_pk,
            MiembroVivienda.estado == "activo",
            MiembroVivienda.eliminado == False
        ).all()
        
        for miembro in miembros:
            cuenta = db.query(Cuenta).filter(
                Cuenta.persona_titular_fk == miembro.persona_miembro_fk,
                # Cuenta.estado == "activo",
                Cuenta.eliminado == False
            ).first()
            
            if cuenta:
                persona = miembro.persona_miembro
                usuario_info = {
                    "usuario_id": cuenta.cuenta_pk,
                    "persona_id": persona.persona_pk,
                    "identificacion": persona.identificacion,
                    "nombres": persona.nombres,
                    "apellidos": persona.apellidos,
                    "correo": persona.correo,
                    "celular": persona.celular,
                    "tipo": "miembro_familia",
                    "estado": cuenta.estado
                }
                if miembro.parentesco:
                    usuario_info["parentesco"] = miembro.parentesco
                usuarios.append(usuario_info)
        
        return {
            "vivienda_id": vivienda.vivienda_pk,
            "manzana": vivienda.manzana,
            "villa": vivienda.villa,
            "total_usuarios": len(usuarios),
            "usuarios": usuarios
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
