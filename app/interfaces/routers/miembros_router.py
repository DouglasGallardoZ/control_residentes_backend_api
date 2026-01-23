from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.interfaces.schemas.schemas import PersonaCreate
from app.infrastructure.db.models import Persona, ResidenteVivienda, MiembroVivienda, Vivienda
from datetime import datetime, date
from app.infrastructure.utils.time_utils import ahora_sin_tz
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/miembros", tags=["Miembros de Familia"])


class AgregarMiembroFamiliaRequest(BaseModel):
    """Schema para agregar miembro de familia"""
    # Ubicación de la vivienda
    manzana: str
    villa: str
    
    # Datos de la persona
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    nacionalidad: str = "Ecuador"
    correo: str = None
    celular: str = None
    direccion_alternativa: str = None
    
    # Parentesco
    parentesco: str
    parentesco_otro_desc: str = None
    
    # Auditoría
    usuario_creado: str = "api_user"


class DesactivarMiembroRequest(BaseModel):
    """Schema para desactivar miembro de familia"""
    usuario_actualizado: str = "api_user"


class ReactivarMiembroRequest(BaseModel):
    """Schema para reactivar miembro de familia"""
    usuario_actualizado: str = "api_user"


@router.post("/{residente_id}/agregar", response_model=dict)
def agregar_miembro_familia(
    residente_id: int,
    request: AgregarMiembroFamiliaRequest,
    db: Session = Depends(get_db)
):
    """
    Agrega un miembro de familia a un residente
    RF-R02: Agregar miembro de familia
    """
    try:
        # Validar parentescos válidos
        parentescos_validos = ['padre', 'madre', 'esposo', 'esposa', 'hijo', 'hija', 'otro']
        if request.parentesco not in parentescos_validos:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parentesco inválido. Válidos: {', '.join(parentescos_validos)}"
            )
        
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
        
        # Validar residente existe
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.residente_vivienda_pk == residente_id,
            ResidenteVivienda.vivienda_reside_fk == vivienda_id
        ).first()
        if not residente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Residente no encontrado en esta vivienda"
            )
        
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
        
        # Crear miembro familia
        miembro = MiembroVivienda(
            vivienda_familia_fk=vivienda_id,
            persona_residente_fk=residente.persona_residente_fk,
            persona_miembro_fk=persona.persona_pk,
            parentesco=request.parentesco,
            parentesco_otro_desc=request.parentesco_otro_desc if request.parentesco == 'otro' else None,
            usuario_creado=request.usuario_creado
        )
        
        db.add(miembro)
        db.flush()
        db.commit()
        db.refresh(miembro)
        
        return {
            "success": True,
            "miembro_id": miembro.miembro_vivienda_pk,
            "persona_id": persona.persona_pk,
            "vivienda_id": vivienda_id,
            "mensaje": "Miembro de familia agregado exitosamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/{vivienda_id}", response_model=dict)
def obtener_miembros_familia(
    vivienda_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los miembros de familia de una vivienda
    """
    try:
        vivienda = db.query(Vivienda).filter(Vivienda.vivienda_pk == vivienda_id).first()
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        miembros = db.query(MiembroVivienda).filter(
            MiembroVivienda.vivienda_familia_fk == vivienda_id,
            MiembroVivienda.eliminado == False,
            MiembroVivienda.estado == "activo"
        ).all()
        
        miembros_data = []
        for miembro in miembros:
            persona = miembro.persona_miembro
            residente = db.query(Persona).filter(
                Persona.persona_pk == miembro.persona_residente_fk
            ).first()
            
            miembros_data.append({
                "miembro_id": miembro.miembro_vivienda_pk,
                "persona_id": persona.persona_pk,
                "residente_titula": f"{residente.nombres} {residente.apellidos}" if residente else "N/A",
                "nombres": f"{persona.nombres} {persona.apellidos}",
                "identificacion": persona.identificacion,
                "parentesco": miembro.parentesco,
                "correo": persona.correo,
                "celular": persona.celular
            })
        
        return {
            "vivienda_id": vivienda_id,
            "total_miembros": len(miembros_data),
            "miembros": miembros_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{miembro_id}/desactivar", response_model=dict)
def desactivar_miembro(
    miembro_id: int,
    request: DesactivarMiembroRequest,
    db: Session = Depends(get_db)
):
    """
    Desactiva un miembro de familia
    RF-R04: Desactivar miembro
    """
    try:
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.miembro_vivienda_pk == miembro_id
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro no encontrado"
            )
        
        miembro.estado = "inactivo"
        miembro.fecha_actualizado = ahora_sin_tz()
        miembro.usuario_actualizado = request.usuario_actualizado
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Miembro desactivado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{miembro_id}/reactivar", response_model=dict)
def reactivar_miembro(
    miembro_id: int,
    request: ReactivarMiembroRequest,
    db: Session = Depends(get_db)
):
    """
    Reactiva un miembro de familia
    RF-R06: Reactivar miembro
    """
    try:
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.miembro_vivienda_pk == miembro_id
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro no encontrado"
            )
        
        miembro.estado = "activo"
        miembro.fecha_actualizado = ahora_sin_tz()
        miembro.usuario_actualizado = request.usuario_actualizado
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Miembro reactivado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{miembro_id}", response_model=dict)
def eliminar_miembro(
    miembro_id: int,
    motivo_eliminado: str = "Eliminación de miembro",
    usuario_actualizado: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Elimina un miembro de familia (soft delete)
    """
    try:
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.miembro_vivienda_pk == miembro_id
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro no encontrado"
            )
        
        miembro.eliminado = True
        miembro.motivo_eliminado = motivo_eliminado
        miembro.fecha_actualizado = ahora_sin_tz()
        miembro.usuario_actualizado = usuario_actualizado
        
        db.commit()
        
        return {
            "success": True,
            "mensaje": "Miembro eliminado correctamente"
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
def obtener_miembros_por_ubicacion(
    manzana: str,
    villa: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los miembros de familia de una vivienda por manzana y villa
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
        
        # Obtener miembros de familia activos
        miembros = db.query(MiembroVivienda).filter(
            MiembroVivienda.vivienda_familia_fk == vivienda.vivienda_pk,
            # MiembroVivienda.estado == "activo",
            MiembroVivienda.eliminado == False
        ).all()
        
        miembros_data = []
        for miembro in miembros:
            persona = miembro.persona_miembro
            miembros_data.append({
                "miembro_id": miembro.miembro_vivienda_pk,
                "persona_id": persona.persona_pk,
                "identificacion": persona.identificacion,
                "nombres": persona.nombres,
                "apellidos": persona.apellidos,
                "correo": persona.correo,
                "celular": persona.celular,
                "parentesco": miembro.parentesco,
                "estado": miembro.estado
            })
        
        return {
            "vivienda_id": vivienda.vivienda_pk,
            "manzana": vivienda.manzana,
            "villa": vivienda.villa,
            "total_miembros": len(miembros_data),
            "miembros": miembros_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
