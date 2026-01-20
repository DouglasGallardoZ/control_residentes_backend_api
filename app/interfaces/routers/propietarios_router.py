from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.interfaces.schemas.schemas import (
    PersonaCreate, PersonaResponse
)
from app.infrastructure.db.models import Persona, PropietarioVivienda, ResidenteVivienda, Vivienda
from datetime import datetime
from app.infrastructure.utils.time_utils import ahora_sin_tz

router = APIRouter(prefix="/api/v1/propietarios", tags=["Propietarios"])


@router.post("", response_model=dict)
def registrar_propietario(
    persona_data: PersonaCreate,
    vivienda_id: int,
    usuario_creado: str,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo propietario y lo asigna a una vivienda
    RF-P01: Registrar propietario
    """
    try:
        # Validar vivienda
        vivienda = db.query(Vivienda).filter(Vivienda.vivienda_pk == vivienda_id).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        # Validar que no exista persona con mismo documento
        persona_existe = db.query(Persona).filter(
            Persona.identificacion == persona_data.identificacion
        ).first()
        if persona_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una persona con identificación {persona_data.identificacion}"
            )
        
        # Crear persona
        persona = Persona(
            identificacion=persona_data.identificacion,
            tipo_identificacion=persona_data.tipo_identificacion,
            nacionalidad=persona_data.nacionalidad or "Ecuador",
            nombres=persona_data.nombres,
            apellidos=persona_data.apellidos,
            fecha_nacimiento=persona_data.fecha_nacimiento,
            correo=persona_data.correo,
            celular=persona_data.celular,
            direccion_alternativa=persona_data.direccion_alternativa,
            usuario_creado=usuario_creado
        )
        
        db.add(persona)
        db.flush()
        
        # Crear relación propietario-vivienda
        propietario = PropietarioVivienda(
            vivienda_propiedad_fk=vivienda_id,
            persona_propietario_fk=persona.persona_pk,
            usuario_creado=usuario_creado
        )
        
        db.add(propietario)
        db.flush()
        
        # Registrar propietario también como residente
        residente = ResidenteVivienda(
            vivienda_reside_fk=vivienda_id,
            persona_residente_fk=persona.persona_pk,
            estado='activo',
            usuario_creado=usuario_creado
        )
        db.add(residente)
        db.commit()
        db.refresh(persona)
        
        return {
            "success": True,
            "persona_id": persona.persona_pk,
            "propietario_id": propietario.propietario_vivienda_pk,
            "residente_id": residente.residente_vivienda_pk,
            "mensaje": "Propietario registrado y automáticamente registrado como residente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{propietario_id}/conyuge", response_model=dict)
def registrar_conyuge_propietario(
    propietario_id: int,
    persona_data: PersonaCreate,
    usuario_creado: str,
    db: Session = Depends(get_db)
):
    """
    Registra un cónyuge como copropietario
    RF-P02: Registrar cónyuge
    """
    try:
        # Validar propietario existe
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id
        ).first()
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        vivienda_id = propietario.vivienda_propiedad_fk
        
        # Validar que no exista persona con mismo documento
        persona_existe = db.query(Persona).filter(
            Persona.identificacion == persona_data.identificacion
        ).first()
        if persona_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una persona con identificación {persona_data.identificacion}"
            )
        
        # Crear persona (cónyuge)
        persona = Persona(
            identificacion=persona_data.identificacion,
            tipo_identificacion=persona_data.tipo_identificacion,
            nacionalidad=persona_data.nacionalidad or "Ecuador",
            nombres=persona_data.nombres,
            apellidos=persona_data.apellidos,
            fecha_nacimiento=persona_data.fecha_nacimiento,
            correo=persona_data.correo,
            celular=persona_data.celular,
            direccion_alternativa=persona_data.direccion_alternativa,
            usuario_creado=usuario_creado
        )
        
        db.add(persona)
        db.flush()
        
        # Crear relación cónyuge-vivienda
        conyuge = PropietarioVivienda(
            vivienda_propiedad_fk=vivienda_id,
            persona_propietario_fk=persona.persona_pk,
            usuario_creado=usuario_creado
        )
        
        db.add(conyuge)
        db.commit()
        
        return {
            "success": True,
            "persona_id": persona.persona_pk,
            "conyuge_id": conyuge.propietario_vivienda_pk,
            "mensaje": "Cónyuge registrado exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{vivienda_id}", response_model=dict)
def obtener_propietarios_vivienda(
    vivienda_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los propietarios de una vivienda
    """
    try:
        vivienda = db.query(Vivienda).filter(Vivienda.vivienda_pk == vivienda_id).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        propietarios = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.eliminado == False
        ).all()
        
        propietarios_data = []
        for prop in propietarios:
            persona = prop.persona
            propietarios_data.append({
                "propietario_id": prop.propietario_vivienda_pk,
                "persona_id": persona.persona_pk,
                "nombres": f"{persona.nombres} {persona.apellidos}",
                "identificacion": persona.identificacion,
                "correo": persona.correo,
                "celular": persona.celular
            })
        
        return {
            "vivienda_id": vivienda_id,
            "total_propietarios": len(propietarios_data),
            "propietarios": propietarios_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{propietario_id}", response_model=dict)
def eliminar_propietario(
    propietario_id: int,
    motivo_eliminado: str = "Cambio de propietario",
    usuario_actualizado: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Elimina un propietario (soft delete)
    """
    try:
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id
        ).first()
        
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        propietario.eliminado = True
        propietario.motivo_eliminado = motivo_eliminado
        propietario.fecha_actualizado = ahora_sin_tz()
        propietario.usuario_actualizado = usuario_actualizado
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Propietario eliminado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
