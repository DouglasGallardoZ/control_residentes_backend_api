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


@router.put("/{propietario_id}", response_model=dict)
def actualizar_propietario(
    propietario_id: int,
    correo_nuevo: str = None,
    celular_nuevo: str = None,
    direccion_alternativa: str = None,
    usuario_actualizado: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Actualiza información del propietario
    RF-P03: Permite actualizar email, celular y dirección
    Campos NO modificables: identificación, nombres, apellidos, manzana, villa
    """
    try:
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id,
            PropietarioVivienda.eliminado == False
        ).first()
        
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        # Obtener persona asociada
        persona = db.query(Persona).filter(
            Persona.persona_pk == propietario.persona_propietario_fk
        ).first()
        
        # Actualizar solo campos permitidos
        if correo_nuevo:
            # Validar formato email básico
            if "@" not in correo_nuevo or "." not in correo_nuevo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de email inválido"
                )
            persona.correo_electronico = correo_nuevo
        
        if celular_nuevo:
            # Validar celular ecuatoriano (09XXXXXXXX)
            if not celular_nuevo.startswith("09") or len(celular_nuevo) != 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Celular debe ser ecuatoriano: 09XXXXXXXX"
                )
            persona.numero_celular = celular_nuevo
        
        if direccion_alternativa:
            persona.direccion_alternativa = direccion_alternativa
        
        persona.fecha_actualizado = ahora_sin_tz()
        persona.usuario_actualizado = usuario_actualizado
        
        db.commit()
        
        return {
            "mensaje": "Información del propietario actualizada correctamente",
            "propietario_id": propietario_id,
            "campos_actualizados": {
                "email": correo_nuevo is not None,
                "celular": celular_nuevo is not None,
                "direccion": direccion_alternativa is not None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{propietario_id}/baja", response_model=dict)
def baja_propietario(
    propietario_id: int,
    motivo: str,
    usuario_actualizado: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Baja de propietario (cambiar estado a inactivo)
    RF-P04: Desactiva propietario e inactiva también al cónyuge si existe
    """
    try:
        if not motivo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El motivo de baja es obligatorio"
            )
        
        propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.propietario_vivienda_pk == propietario_id,
            PropietarioVivienda.eliminado == False
        ).first()
        
        if not propietario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Propietario no encontrado"
            )
        
        if propietario.estado == "inactivo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El propietario ya se encuentra inactivo"
            )
        
        # Cambiar propietario a inactivo
        propietario.estado = "inactivo"
        propietario.fecha_actualizado = ahora_sin_tz()
        propietario.usuario_actualizado = usuario_actualizado
        propietario.motivo_eliminado = motivo
        
        # Obtener y desactivar cónyuge si existe
        conyuge_procesado = False
        persona_propietario = db.query(Persona).filter(
            Persona.persona_pk == propietario.persona_propietario_fk
        ).first()
        
        if persona_propietario:
            # Buscar cónyuge en tabla Persona con relación de pareja
            # Se asume que hay una relación establecida
            # Aquí se busca si esta persona es propietario y tiene cónyuge registrado
            conyuge = db.query(Persona).filter(
                Persona.persona_pk != persona_propietario.persona_pk,
                # Buscamos si hay otro propietario en la misma vivienda (cónyuge)
                Persona.estado == "activo"
            ).filter(
                Persona.persona_pk.in_(
                    db.query(PropietarioVivienda.persona_propietario_fk).filter(
                        PropietarioVivienda.vivienda_propiedad_fk == propietario.vivienda_propiedad_fk,
                        PropietarioVivienda.persona_propietario_fk != propietario.persona_propietario_fk,
                        PropietarioVivienda.eliminado == False
                    )
                )
            ).first()
            
            if conyuge:
                conyuge_prop = db.query(PropietarioVivienda).filter(
                    PropietarioVivienda.persona_propietario_fk == conyuge.persona_pk,
                    PropietarioVivienda.vivienda_propiedad_fk == propietario.vivienda_propiedad_fk
                ).first()
                
                if conyuge_prop:
                    conyuge_prop.estado = "inactivo"
                    conyuge_prop.fecha_actualizado = ahora_sin_tz()
                    conyuge_prop.usuario_actualizado = usuario_actualizado
                    conyuge_prop.motivo_eliminado = f"Baja asociada a propietario principal: {motivo}"
                    conyuge_procesado = True
        
        db.commit()
        
        return {
            "mensaje": "Propietario dado de baja correctamente",
            "propietario_id": propietario_id,
            "conyuge_procesado": conyuge_procesado,
            "motivo": motivo
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cambio-propiedad", response_model=dict)
def cambio_propietario_vivienda(
    vivienda_id: int,
    nuevo_propietario_id: int,
    motivo_cambio: str,
    usuario_actualizado: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Cambio de propietario de vivienda (transferencia completa)
    RF-P05: Desactiva propietario actual, activa nuevo y actualiza residente principal
    Si residente actual = propietario anterior, nuevo propietario se registra como residente activo
    """
    try:
        if not motivo_cambio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El motivo del cambio es obligatorio"
            )
        
        # Validar vivienda existe
        vivienda = db.query(Vivienda).filter(
            Vivienda.vivienda_pk == vivienda_id
        ).first()
        
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        # Obtener propietario actual
        propietario_actual = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).first()
        
        if not propietario_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no tiene propietario activo"
            )
        
        # Obtener nuevo propietario
        nueva_persona = db.query(Persona).filter(
            Persona.persona_pk == nuevo_propietario_id,
            Persona.estado == "activo"
        ).first()
        
        if not nueva_persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nueva persona no encontrada o inactiva"
            )
        
        # Obtener residente actual (para saber si es el propietario)
        residente_actual = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.vivienda_reside_fk == vivienda_id,
            ResidenteVivienda.estado == "activo"
        ).first()
        
        propietario_anterior_es_residente = (
            residente_actual and 
            residente_actual.persona_residente_fk == propietario_actual.persona_propietario_fk
        )
        
        # Desactivar propietario actual
        propietario_actual.estado = "inactivo"
        propietario_actual.fecha_actualizado = ahora_sin_tz()
        propietario_actual.usuario_actualizado = usuario_actualizado
        propietario_actual.motivo_eliminado = f"Cambio de propietario: {motivo_cambio}"
        
        # Buscar o crear nuevo propietario
        nuevo_propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.persona_propietario_fk == nuevo_propietario_id,
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id
        ).first()
        
        if nuevo_propietario:
            # Activar si existe pero estaba inactivo
            nuevo_propietario.estado = "activo"
            nuevo_propietario.fecha_actualizado = ahora_sin_tz()
            nuevo_propietario.usuario_actualizado = usuario_actualizado
        else:
            # Crear nuevo registro de propietario
            nuevo_propietario = PropietarioVivienda(
                persona_propietario_fk=nuevo_propietario_id,
                vivienda_propiedad_fk=vivienda_id,
                estado="activo",
                usuario_creado=usuario_actualizado
            )
            db.add(nuevo_propietario)
        
        # Si propietario anterior era residente, registrar nuevo como residente
        residente_nuevo_creado = False
        if propietario_anterior_es_residente:
            # Buscar si nuevo propietario ya es residente
            residente_nuevo = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.persona_residente_fk == nuevo_propietario_id,
                ResidenteVivienda.vivienda_reside_fk == vivienda_id
            ).first()
            
            if residente_nuevo:
                # Activar si existe pero estaba inactivo
                residente_nuevo.estado = "activo"
                residente_nuevo.fecha_actualizado = ahora_sin_tz()
                residente_nuevo.usuario_actualizado = usuario_actualizado
            else:
                # Crear nuevo registro de residente
                residente_nuevo = ResidenteVivienda(
                    persona_residente_fk=nuevo_propietario_id,
                    vivienda_reside_fk=vivienda_id,
                    estado="activo",
                    usuario_creado=usuario_actualizado
                )
                db.add(residente_nuevo)
                residente_nuevo_creado = True
        
        db.commit()
        
        return {
            "mensaje": "Cambio de propietario realizado correctamente",
            "vivienda_id": vivienda_id,
            "propietario_anterior_id": propietario_actual.propietario_vivienda_pk,
            "propietario_nuevo_id": nuevo_propietario_id,
            "propietario_era_residente": propietario_anterior_es_residente,
            "residente_nuevo_creado": residente_nuevo_creado,
            "motivo": motivo_cambio
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
