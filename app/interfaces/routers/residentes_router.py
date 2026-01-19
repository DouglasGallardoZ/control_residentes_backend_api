from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.interfaces.schemas.schemas import (
    ResidenteCreate, ResidenteResponse, ResidenteDesactivar, ResidenteReactivar
)
from app.infrastructure.db.models import Persona, ResidenteVivienda, Vivienda
from datetime import datetime

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
        # Validar vivienda
        vivienda = db.query(Vivienda).filter(Vivienda.vivienda_pk == request.vivienda_id).first()
        if not vivienda or not vivienda.estado == "activo":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada o inactiva"
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
            vivienda_reside_fk=request.vivienda_id,
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
        residente.fecha_actualizado = datetime.utcnow()
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
        residente.fecha_actualizado = datetime.utcnow()
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
    ruta_imagen: str,
    formato: str,
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
            ruta_imagen=ruta_imagen,
            formato=formato,
            usuario_creado="api_user"
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
