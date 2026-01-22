from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.interfaces.schemas.schemas import (
    ResidenteCreate, ResidenteResponse, ResidenteDesactivar, ResidenteReactivar, AgregarFotoRequest
)
from app.infrastructure.db.models import Persona, ResidenteVivienda, Vivienda
from datetime import datetime
from app.infrastructure.utils.time_utils import ahora_sin_tz

router = APIRouter(prefix="/api/v1/residentes", tags=["Residentes"])


@router.post("", response_model=dict)
def registrar_residente(
    request: ResidenteCreate,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo residente
    RF-R01
    """
    try:
        # Validar vivienda por manzana y villa
        vivienda = db.query(Vivienda).filter(
            Vivienda.manzana == request.manzana,
            Vivienda.villa == request.villa,
            Vivienda.estado == "activo"
        ).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada o inactiva"
            )
        
        # Validar que no exista residente activo en esa vivienda
        residente_existente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.vivienda_reside_fk == vivienda.vivienda_pk,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).first()
        if residente_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un residente activo registrado en esta vivienda"
            )
        
        # Validar que no exista persona con mismo documento
        persona_existente = db.query(Persona).filter(
            Persona.identificacion == request.identificacion
        ).first()
        if persona_existente and persona_existente.estado == "activo":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El identificación ya está registrada"
            )
        
        # TODO: Validar documento de autorización PDF
        
        # Crear persona
        persona = Persona(
            identificacion=request.identificacion,
            tipo_identificacion=request.tipo_identificacion,
            nombres=request.nombres,
            apellidos=request.apellidos,
            fecha_nacimiento=request.fecha_nacimiento,
            nacionalidad=request.nacionalidad,
            correo=request.correo,
            celular=request.celular,
            direccion_alternativa=request.direccion_alternativa,
            estado="activo",
            usuario_creado=request.usuario_creado
        )
        
        db.add(persona)
        db.flush()
        
        # Crear residente
        residente = ResidenteVivienda(
            vivienda_reside_fk=vivienda.vivienda_pk,
            persona_residente_fk=persona.persona_pk,
            doc_autorizacion_pdf=request.doc_autorizacion_pdf,
            estado="activo",
            usuario_creado=request.usuario_creado
        )
        
        db.add(residente)
        db.commit()
        
        return {
            "id": residente.residente_vivienda_pk,
            "persona_id": persona.persona_pk,
            "mensaje": "Residente registrado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{residente_id}/desactivar", response_model=dict)
def desactivar_residente(
    residente_id: int,
    request: ResidenteDesactivar,
    db: Session = Depends(get_db)
):
    """
    Desactiva un residente
    RF-R03
    """
    try:
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.residente_vivienda_pk == residente_id
        ).first()
        
        if not residente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Residente no encontrado"
            )
        
        if residente.estado == "inactivo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El residente ya se encuentra inactivo"
            )
        
        # Desactivar residente
        residente.estado = "inactivo"
        residente.motivo = request.motivo
        residente.fecha_actualizado = ahora_sin_tz()
        residente.usuario_actualizado = request.usuario_actualizado
        
        # TODO: Desactivar automáticamente miembros de familia asociados
        
        db.commit()
        
        return {
            "mensaje": "Residente desactivado correctamente",
            "residente_id": residente_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{residente_id}/reactivar", response_model=dict)
def reactivar_residente(
    residente_id: int,
    request: ResidenteReactivar,
    db: Session = Depends(get_db)
):
    """
    Reactiva un residente previamente desactivado
    RF-R05
    """
    try:
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.residente_vivienda_pk == residente_id
        ).first()
        
        if not residente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Residente no encontrado"
            )
        
        if residente.estado == "activo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El residente ya está activo"
            )
        
        # Reactivar residente
        residente.estado = "activo"
        residente.fecha_hasta = None
        residente.fecha_actualizado = ahora_sin_tz()
        residente.usuario_actualizado = request.usuario_actualizado
        
        db.commit()
        
        return {
            "mensaje": "Residente reactivado correctamente",
            "residente_id": residente_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{persona_id}/foto", response_model=dict)
def agregar_foto_residente(
    persona_id: int,
    request: AgregarFotoRequest,
    db: Session = Depends(get_db)
):
    """
    Agrega una foto al residente
    Tabla: persona_foto
    """
    try:
        from app.infrastructure.db.models import PersonaFoto
        
        # Validar persona existe y es residente
        persona = db.query(Persona).filter(Persona.persona_pk == persona_id).first()
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona no encontrada"
            )
        
        # Verificar que es residente
        es_residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_titular_fk == persona_id
        ).first()
        if not es_residente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La persona no es un residente registrado"
            )
        
        # Crear foto
        foto = PersonaFoto(
            persona_titular_fk=persona_id,
            ruta_imagen=request.ruta_imagen,
            formato=request.formato,
            usuario_creado=request.usuario_creado
        )
        
        db.add(foto)
        db.commit()
        db.refresh(foto)
        
        return {
            "success": True,
            "foto_id": foto.foto_pk,
            "mensaje": "Foto agregada exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{persona_id}/fotos", response_model=dict)
def obtener_fotos_residente(
    persona_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las fotos del residente
    """
    try:
        from app.infrastructure.db.models import PersonaFoto
        
        persona = db.query(Persona).filter(Persona.persona_pk == persona_id).first()
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona no encontrada"
            )
        
        fotos = db.query(PersonaFoto).filter(
            PersonaFoto.persona_titular_fk == persona_id,
            PersonaFoto.eliminado == False
        ).all()
        
        return {
            "persona_id": persona_id,
            "total_fotos": len(fotos),
            "fotos": [
                {
                    "foto_id": f.foto_pk,
                    "ruta_imagen": f.ruta_imagen,
                    "formato": f.formato,
                    "fecha_creado": f.fecha_creado.isoformat()
                }
                for f in fotos
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/manzana-villa/{manzana}/{villa}", response_model=dict)
def obtener_residentes_por_ubicacion(
    manzana: str,
    villa: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los residentes de una vivienda por manzana y villa
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
        
        # Obtener residentes activos
        residentes = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.vivienda_reside_fk == vivienda.vivienda_pk,
            # ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False
        ).all()
        
        residentes_data = []
        for residente in residentes:
            persona = residente.persona
            residentes_data.append({
                "residente_id": residente.residente_vivienda_pk,
                "persona_id": persona.persona_pk,
                "identificacion": persona.identificacion,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "correo": persona.correo,
                "celular": persona.celular,
                "estado": residente.estado
            })
        
        return {
            "vivienda_id": vivienda.vivienda_pk,
            "manzana": vivienda.manzana,
            "villa": vivienda.villa,
            "total_residentes": len(residentes_data),
            "residentes": residentes_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
