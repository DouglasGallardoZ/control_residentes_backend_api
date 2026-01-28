from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.interfaces.schemas.schemas import (
    PersonaCreate, PersonaResponse
)
from app.infrastructure.db.models import Persona, PropietarioVivienda, ResidenteVivienda, Vivienda
from datetime import datetime, date
from pydantic import BaseModel
from app.infrastructure.utils.time_utils import ahora_sin_tz

router = APIRouter(prefix="/api/v1/propietarios", tags=["Propietarios"])


class RegistrarPropietarioRequest(BaseModel):
    """Schema para registrar propietario"""
    # Datos de la persona
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = "Ecuador"
    correo: str
    celular: str
    direccion_alternativa: str = None
    
    # Ubicación de la vivienda
    manzana: str
    villa: str
    
    # Auditoría
    usuario_creado: str = "api_user"


class RegistrarConyyugeRequest(BaseModel):
    """Schema para registrar cónyuge como copropietario"""
    # Datos de la persona
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = "Ecuador"
    correo: str
    celular: str
    direccion_alternativa: str = None
    
    # Auditoría
    usuario_creado: str = "api_user"


class BajaRequest(BaseModel):
    """Schema para baja de propietario"""
    motivo: str
    usuario_actualizado: str = "api_user"


class CambioPropiedadRequest(BaseModel):
    """Schema para cambio de propietario"""
    vivienda_id: int
    nuevo_propietario_id: int
    motivo_cambio: str
    usuario_actualizado: str = "api_user"


class ActualizarPropietarioRequest(BaseModel):
    """Schema para actualizar propietario"""
    correo_nuevo: str = None
    celular_nuevo: str = None
    direccion_alternativa: str = None
    usuario_actualizado: str = "api_user"


@router.post("", response_model=dict)
def registrar_propietario(
    request: RegistrarPropietarioRequest,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo propietario y lo asigna a una vivienda
    RF-P01: Registrar propietario
    """
    try:
        # Validar vivienda por manzana y villa
        vivienda = db.query(Vivienda).filter(
            Vivienda.manzana == request.manzana,
            Vivienda.villa == request.villa
        ).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vivienda no encontrada para manzana '{request.manzana}' y villa '{request.villa}'"
            )
        
        vivienda_id = vivienda.vivienda_pk
        
        # Validar que no exista persona con mismo documento
        persona_existe = db.query(Persona).filter(
            Persona.identificacion == request.identificacion
        ).first()
        if persona_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una persona con identificación {request.identificacion}"
            )
        
        # Crear persona
        persona = Persona(
            identificacion=request.identificacion,
            tipo_identificacion=request.tipo_identificacion,
            nacionalidad=request.nacionalidad,
            nombres=request.nombres,
            apellidos=request.apellidos,
            fecha_nacimiento=request.fecha_nacimiento,
            correo=request.correo,
            celular=request.celular,
            direccion_alternativa=request.direccion_alternativa,
            usuario_creado=request.usuario_creado
        )
        
        db.add(persona)
        db.flush()
        
        # Validar que no exista un propietario titular activo en esta vivienda
        propietario_titular_existente = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.tipo_propietario == "titular",
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).first()
        
        if propietario_titular_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta vivienda ya tiene un propietario titular registrado"
            )
        
        # Crear relación propietario-vivienda con tipo_propietario="titular"
        propietario = PropietarioVivienda(
            vivienda_propiedad_fk=vivienda_id,
            persona_propietario_fk=persona.persona_pk,
            tipo_propietario="titular",
            estado="activo",
            usuario_creado=request.usuario_creado
        )
        
        db.add(propietario)
        # db.flush()
        
        # # Registrar propietario también como residente
        # residente = ResidenteVivienda(
        #     vivienda_reside_fk=vivienda_id,
        #     persona_residente_fk=persona.persona_pk,
        #     estado='activo',
        #     usuario_creado=request.usuario_creado
        # )
        # db.add(residente)
        db.commit()
        db.refresh(persona)
        
        return {
            "success": True,
            "persona_id": persona.persona_pk,
            "propietario_id": propietario.propietario_vivienda_pk,
            "vivienda_id": vivienda_id,
            "mensaje": "Propietario registrado con exito"
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
    request: RegistrarConyyugeRequest,
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
            Persona.identificacion == request.identificacion
        ).first()
        if persona_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una persona con identificación {request.identificacion}"
            )
        
        # Crear persona (cónyuge)
        persona = Persona(
            identificacion=request.identificacion,
            tipo_identificacion=request.tipo_identificacion,
            nacionalidad=request.nacionalidad,
            nombres=request.nombres,
            apellidos=request.apellidos,
            fecha_nacimiento=request.fecha_nacimiento,
            correo=request.correo,
            celular=request.celular,
            direccion_alternativa=request.direccion_alternativa,
            usuario_creado=request.usuario_creado
        )
        
        db.add(persona)
        db.flush()
        
        # Validar que solo exista un cónyuge por propiedad
        conyuge_existente = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.tipo_propietario == "conyuge",
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).first()
        
        if conyuge_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta vivienda ya tiene un cónyuge registrado"
            )
        
        # Crear relación cónyuge-vivienda con tipo_propietario="conyuge"
        conyuge = PropietarioVivienda(
            vivienda_propiedad_fk=vivienda_id,
            persona_propietario_fk=persona.persona_pk,
            tipo_propietario="conyuge",
            estado="activo",
            usuario_creado=request.usuario_creado
        )
        
        db.add(conyuge)
        db.commit()
        
        return {
            "success": True,
            "persona_id": persona.persona_pk,
            "conyuge_id": conyuge.propietario_vivienda_pk,
            "vivienda_id": vivienda_id,
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
    request: ActualizarPropietarioRequest,
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
        if request.correo_nuevo:
            # Validar formato email básico
            if "@" not in request.correo_nuevo or "." not in request.correo_nuevo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Formato de email inválido"
                )
            persona.correo = request.correo_nuevo
        
        if request.celular_nuevo:
            # Validar celular
            if len(request.celular_nuevo) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Celular inválido"
                )
            persona.celular = request.celular_nuevo
        
        if request.direccion_alternativa:
            persona.direccion_alternativa = request.direccion_alternativa
        
        persona.fecha_actualizado = ahora_sin_tz()
        persona.usuario_actualizado = request.usuario_actualizado
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Información del propietario actualizada correctamente",
            "propietario_id": propietario_id,
            "campos_actualizados": {
                "email": request.correo_nuevo is not None,
                "celular": request.celular_nuevo is not None,
                "direccion": request.direccion_alternativa is not None
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
    request: BajaRequest,
    db: Session = Depends(get_db)
):
    """
    Baja de propietario (cambiar estado a inactivo)
    RF-P04: Desactiva propietario e inactiva también al cónyuge si existe
    """
    try:
        if not request.motivo:
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
        propietario.usuario_actualizado = request.usuario_actualizado
        propietario.motivo_eliminado = request.motivo
        
        # Obtener y desactivar cónyuge si existe
        conyuge_procesado = False
        
        # Buscar cónyuge directo por tipo_propietario
        conyuge_prop = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == propietario.vivienda_propiedad_fk,
            PropietarioVivienda.tipo_propietario == "conyuge",
            PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).first()
        
        if conyuge_prop:
            conyuge_prop.estado = "inactivo"
            conyuge_prop.fecha_actualizado = ahora_sin_tz()
            conyuge_prop.usuario_actualizado = request.usuario_actualizado
            conyuge_prop.motivo_eliminado = f"Baja asociada a propietario titular: {request.motivo}"
            conyuge_procesado = True
        
        db.commit()
        
        return {
            "mensaje": "Propietario dado de baja correctamente",
            "propietario_id": propietario_id,
            "conyuge_procesado": conyuge_procesado,
            "motivo": request.motivo
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
    request: CambioPropiedadRequest,
    db: Session = Depends(get_db)
):
    """
    Cambio de propietario de vivienda (transferencia completa)
    RF-P05: Desactiva propietario actual, activa nuevo y actualiza residente principal
    Si residente actual = propietario anterior, nuevo propietario se registra como residente activo
    """
    try:
        if not request.motivo_cambio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El motivo del cambio es obligatorio"
            )
        
        # Validar vivienda existe
        vivienda = db.query(Vivienda).filter(
            Vivienda.vivienda_pk == request.vivienda_id
        ).first()
        
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        # Obtener propietario actual
        propietario_actual = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == request.vivienda_id,
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
            Persona.persona_pk == request.nuevo_propietario_id,
            Persona.estado == "activo"
        ).first()
        
        if not nueva_persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nueva persona no encontrada o inactiva"
            )
        
        # Obtener residente actual (para saber si es el propietario)
        residente_actual = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.vivienda_reside_fk == request.vivienda_id,
            ResidenteVivienda.estado == "activo"
        ).first()
        
        propietario_anterior_es_residente = (
            residente_actual and 
            residente_actual.persona_residente_fk == propietario_actual.persona_propietario_fk
        )
        
        # Desactivar propietario actual
        propietario_actual.estado = "inactivo"
        propietario_actual.fecha_actualizado = ahora_sin_tz()
        propietario_actual.usuario_actualizado = request.usuario_actualizado
        propietario_actual.motivo_eliminado = f"Cambio de propietario: {request.motivo_cambio}"
        
        # Buscar o crear nuevo propietario
        nuevo_propietario = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.persona_propietario_fk == request.nuevo_propietario_id,
            PropietarioVivienda.vivienda_propiedad_fk == request.vivienda_id
        ).first()
        
        if nuevo_propietario:
            # Activar si existe pero estaba inactivo
            nuevo_propietario.estado = "activo"
            nuevo_propietario.fecha_actualizado = ahora_sin_tz()
            nuevo_propietario.usuario_actualizado = request.usuario_actualizado
        else:
            # Crear nuevo registro de propietario
            nuevo_propietario = PropietarioVivienda(
                persona_propietario_fk=request.nuevo_propietario_id,
                vivienda_propiedad_fk=request.vivienda_id,
                estado="activo",
                usuario_creado=request.usuario_actualizado
            )
            db.add(nuevo_propietario)
        
        # Si propietario anterior era residente, registrar nuevo como residente
        residente_nuevo_creado = False
        if propietario_anterior_es_residente:
            # Buscar si nuevo propietario ya es residente
            residente_nuevo = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.persona_residente_fk == request.nuevo_propietario_id,
                ResidenteVivienda.vivienda_reside_fk == request.vivienda_id
            ).first()
            
            if residente_nuevo:
                # Activar si existe pero estaba inactivo
                residente_nuevo.estado = "activo"
                residente_nuevo.fecha_actualizado = ahora_sin_tz()
                residente_nuevo.usuario_actualizado = request.usuario_actualizado
            else:
                # Crear nuevo registro de residente
                residente_nuevo = ResidenteVivienda(
                    persona_residente_fk=request.nuevo_propietario_id,
                    vivienda_reside_fk=request.vivienda_id,
                    estado="activo",
                    usuario_creado=request.usuario_actualizado
                )
                db.add(residente_nuevo)
                residente_nuevo_creado = True
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Cambio de propietario realizado correctamente",
            "vivienda_id": request.vivienda_id,
            "propietario_anterior_id": propietario_actual.propietario_vivienda_pk,
            "propietario_nuevo_id": request.nuevo_propietario_id,
            "propietario_era_residente": propietario_anterior_es_residente,
            "residente_nuevo_creado": residente_nuevo_creado,
            "motivo": request.motivo_cambio
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/manzana-villa/{manzana}/{villa}", response_model=dict)
def obtener_propietarios_por_ubicacion(
    manzana: str,
    villa: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los propietarios de una vivienda por manzana y villa
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
        
        # Obtener propietarios activos
        propietarios = db.query(PropietarioVivienda).filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda.vivienda_pk,
            # PropietarioVivienda.estado == "activo",
            PropietarioVivienda.eliminado == False
        ).all()
        
        propietarios_data = []
        for propietario in propietarios:
            persona = propietario.persona
            propietarios_data.append({
                "propietario_id": propietario.propietario_vivienda_pk,
                "persona_id": persona.persona_pk,
                "identificacion": persona.identificacion,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "correo": persona.correo,
                "celular": persona.celular,
                "estado": propietario.estado,
                "tipo_propietario": propietario.tipo_propietario
            })
        
        return {
            "vivienda_id": vivienda.vivienda_pk,
            "manzana": vivienda.manzana,
            "villa": vivienda.villa,
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
