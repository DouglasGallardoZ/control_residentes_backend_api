from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import Vivienda, ResidenteVivienda, MiembroVivienda
from app.infrastructure.security.auth import requerir_rol
from app.interfaces.schemas.schemas import (
    ViviendaCreate,
    ViviendaUpdate,
    ViviendaResponse,
    ViviendaListResponse,
    ViviendaEstadoUpdate,
)

router = APIRouter(prefix="/api/v1/viviendas", tags=["Viviendas"])

PAGINATION_DEFAULT_PAGE = 1
PAGINATION_DEFAULT_PAGE_SIZE = 20
PAGINATION_MAX_PAGE_SIZE = 100


@router.get("", response_model=ViviendaListResponse)
def listar_viviendas(
    page: int = Query(PAGINATION_DEFAULT_PAGE, ge=1),
    page_size: int = Query(
        PAGINATION_DEFAULT_PAGE_SIZE,
        ge=1,
        le=PAGINATION_MAX_PAGE_SIZE,
    ),
    manzana: Optional[str] = Query(
        None, description="Filtrar por manzana"
    ),
    estado: Optional[str] = Query(
        None, description="Filtrar por estado (activo/inactivo)"
    ),
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Lista todas las viviendas con paginacion y filtros opcionales."""

    query = db.query(Vivienda).filter(Vivienda.eliminado == False)

    if manzana:
        query = query.filter(Vivienda.manzana.ilike(f"%{manzana}%"))
    if estado:
        query = query.filter(Vivienda.estado == estado)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    viviendas = (
        query.order_by(Vivienda.manzana.asc(), Vivienda.villa.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    data = []
    for v in viviendas:
        total_residentes = (
            db.query(ResidenteVivienda)
            .filter(
                ResidenteVivienda.vivienda_reside_fk == v.vivienda_pk,
                ResidenteVivienda.estado == "activo",
                ResidenteVivienda.eliminado == False,
            )
            .count()
        )

        total_miembros = (
            db.query(MiembroVivienda)
            .filter(
                MiembroVivienda.vivienda_familia_fk == v.vivienda_pk,
                MiembroVivienda.estado == "activo",
                MiembroVivienda.eliminado == False,
            )
            .count()
        )

        data.append(
            ViviendaResponse(
                vivienda_id=v.vivienda_pk,
                manzana=v.manzana,
                villa=v.villa,
                estado=v.estado,
                total_residentes=total_residentes,
                total_miembros=total_miembros,
                fecha_creado=v.fecha_creado,
                fecha_actualizado=v.fecha_actualizado,
            )
        )

    return ViviendaListResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
    )


@router.get("/{vivienda_id}", response_model=ViviendaResponse)
def obtener_vivienda(
    vivienda_id: int,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Obtiene el detalle de una vivienda especifica."""

    vivienda = (
        db.query(Vivienda)
        .filter(
            Vivienda.vivienda_pk == vivienda_id,
            Vivienda.eliminado == False,
        )
        .first()
    )

    if not vivienda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vivienda no encontrada",
        )

    total_residentes = (
        db.query(ResidenteVivienda)
        .filter(
            ResidenteVivienda.vivienda_reside_fk == vivienda_id,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False,
        )
        .count()
    )

    total_miembros = (
        db.query(MiembroVivienda)
        .filter(
            MiembroVivienda.vivienda_familia_fk == vivienda_id,
            MiembroVivienda.estado == "activo",
            MiembroVivienda.eliminado == False,
        )
        .count()
    )

    return ViviendaResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        estado=vivienda.estado,
        total_residentes=total_residentes,
        total_miembros=total_miembros,
        fecha_creado=vivienda.fecha_creado,
        fecha_actualizado=vivienda.fecha_actualizado,
    )


@router.post("", response_model=ViviendaResponse, status_code=201)
def crear_vivienda(
    request: ViviendaCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Crea una nueva vivienda."""

    existente = (
        db.query(Vivienda)
        .filter(
            Vivienda.manzana == request.manzana.strip().upper(),
            Vivienda.villa == request.villa.strip().upper(),
            Vivienda.eliminado == False,
        )
        .first()
    )

    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Ya existe una vivienda en Manzana "
                f"{request.manzana}, Villa {request.villa}"
            ),
        )

    vivienda = Vivienda(
        manzana=request.manzana.strip().upper(),
        villa=request.villa.strip().upper(),
        estado=request.estado,
        usuario_creado=request.usuario_creado,
        fecha_creado=datetime.utcnow(),
    )

    db.add(vivienda)
    db.commit()
    db.refresh(vivienda)

    return ViviendaResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        estado=vivienda.estado,
        total_residentes=0,
        total_miembros=0,
        fecha_creado=vivienda.fecha_creado,
        fecha_actualizado=vivienda.fecha_actualizado,
    )


@router.put("/{vivienda_id}", response_model=ViviendaResponse)
def actualizar_vivienda(
    vivienda_id: int,
    request: ViviendaUpdate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Actualiza los datos de una vivienda."""

    vivienda = (
        db.query(Vivienda)
        .filter(
            Vivienda.vivienda_pk == vivienda_id,
            Vivienda.eliminado == False,
        )
        .first()
    )

    if not vivienda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vivienda no encontrada",
        )

    if request.manzana is not None:
        vivienda.manzana = request.manzana.strip().upper()
    if request.villa is not None:
        vivienda.villa = request.villa.strip().upper()
    if request.estado is not None:
        vivienda.estado = request.estado

    vivienda.fecha_actualizado = datetime.utcnow()
    vivienda.usuario_actualizado = request.usuario_actualizado

    db.commit()
    db.refresh(vivienda)

    total_residentes = (
        db.query(ResidenteVivienda)
        .filter(
            ResidenteVivienda.vivienda_reside_fk == vivienda_id,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False,
        )
        .count()
    )

    total_miembros = (
        db.query(MiembroVivienda)
        .filter(
            MiembroVivienda.vivienda_familia_fk == vivienda_id,
            MiembroVivienda.estado == "activo",
            MiembroVivienda.eliminado == False,
        )
        .count()
    )

    return ViviendaResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        estado=vivienda.estado,
        total_residentes=total_residentes,
        total_miembros=total_miembros,
        fecha_creado=vivienda.fecha_creado,
        fecha_actualizado=vivienda.fecha_actualizado,
    )


@router.put("/{vivienda_id}/estado", response_model=dict)
def cambiar_estado_vivienda(
    vivienda_id: int,
    request: ViviendaEstadoUpdate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Activa o desactiva una vivienda."""

    vivienda = (
        db.query(Vivienda)
        .filter(
            Vivienda.vivienda_pk == vivienda_id,
            Vivienda.eliminado == False,
        )
        .first()
    )

    if not vivienda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vivienda no encontrada",
        )

    if request.estado not in ("activo", "inactivo"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado invalido. Use 'activo' o 'inactivo'",
        )

    vivienda.estado = request.estado
    vivienda.fecha_actualizado = datetime.utcnow()
    vivienda.usuario_actualizado = request.usuario_actualizado

    if request.motivo:
        vivienda.motivo_eliminado = request.motivo

    db.commit()

    accion = "activada" if request.estado == "activo" else "desactivada"
    return {
        "success": True,
        "vivienda_id": vivienda.vivienda_pk,
        "estado": vivienda.estado,
        "mensaje": f"Vivienda {accion} exitosamente",
    }
