from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import math
from app.infrastructure.utils.auditoria_helpers import registrar_bitacora

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import (
    Vivienda, ResidenteVivienda, MiembroVivienda, PropietarioVivienda, Persona,
)
from app.infrastructure.security.auth import requerir_rol
from app.interfaces.schemas.schemas import (
    ViviendaCreate,
    ViviendaUpdate,
    ViviendaResponse,
    ViviendaListResponse,
    ViviendaEstadoUpdate,
    ViviendaCambioPropietarioRequest,
    ViviendaCambioPropietarioResponse,
    ViviendaDetalleResponse,
)
from pydantic import BaseModel, Field

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
        propietarios_query = (
            db.query(PropietarioVivienda, Persona)
            .join(
                Persona,
                PropietarioVivienda.persona_propietario_fk
                == Persona.persona_pk,
            )
            .filter(
                PropietarioVivienda.vivienda_propiedad_fk == v.vivienda_pk,
                PropietarioVivienda.eliminado == False,
                Persona.eliminado == False,
            )
            .all()
        )

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
                propietarios=[
                    {
                        "persona_id": prop[1].persona_pk,
                        "nombres": prop[1].nombres,
                        "apellidos": prop[1].apellidos,
                        "identificacion": prop[1].identificacion,
                        "correo": prop[1].correo,
                        "celular": prop[1].celular,
                        "tipo": prop[0].tipo_propietario,
                        "estado": prop[0].estado,
                    }
                    for prop in propietarios_query
                ],
                residentes_count=total_residentes,
                miembros_count=total_miembros,
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

    propietarios_query = (
        db.query(PropietarioVivienda, Persona)
        .join(
            Persona,
            PropietarioVivienda.persona_propietario_fk
            == Persona.persona_pk,
        )
        .filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.eliminado == False,
            Persona.eliminado == False,
        )
        .all()
    )

    return ViviendaResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        estado=vivienda.estado,
        total_residentes=total_residentes,
        total_miembros=total_miembros,
        propietarios=[
            {
                "persona_id": prop[1].persona_pk,
                "nombres": prop[1].nombres,
                "apellidos": prop[1].apellidos,
                "identificacion": prop[1].identificacion,
                "correo": prop[1].correo,
                "celular": prop[1].celular,
                "tipo": prop[0].tipo_propietario,
                "estado": prop[0].estado,
            }
            for prop in propietarios_query
        ],
        residentes_count=total_residentes,
        miembros_count=total_miembros,
        fecha_creado=vivienda.fecha_creado,
        fecha_actualizado=vivienda.fecha_actualizado,
    )


@router.get(
    "/{vivienda_id}/detalle", response_model=ViviendaDetalleResponse
)
def detalle_vivienda(
    vivienda_id: int,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Retorna el detalle completo de una villa: propietarios, residentes y miembros."""
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

    propietarios_query = (
        db.query(PropietarioVivienda, Persona)
        .join(
            Persona,
            PropietarioVivienda.persona_propietario_fk
            == Persona.persona_pk,
        )
        .filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.eliminado == False,
            Persona.eliminado == False,
        )
        .all()
    )

    residentes_query = (
        db.query(ResidenteVivienda, Persona)
        .join(
            Persona,
            ResidenteVivienda.persona_residente_fk == Persona.persona_pk,
        )
        .filter(
            ResidenteVivienda.vivienda_reside_fk == vivienda_id,
            ResidenteVivienda.eliminado == False,
            Persona.eliminado == False,
        )
        .all()
    )

    miembros_query = (
        db.query(MiembroVivienda, Persona)
        .join(
            Persona,
            MiembroVivienda.persona_miembro_fk == Persona.persona_pk,
        )
        .filter(
            MiembroVivienda.vivienda_familia_fk == vivienda_id,
            MiembroVivienda.eliminado == False,
            Persona.eliminado == False,
        )
        .all()
    )

    miembros_data = []
    for m, p in miembros_query:
        residente = (
            db.query(Persona)
            .filter(
                Persona.persona_pk == m.persona_residente_fk,
                Persona.eliminado == False,
            )
            .first()
        )
        miembros_data.append({
            "persona_id": p.persona_pk,
            "nombres": p.nombres,
            "apellidos": p.apellidos,
            "identificacion": p.identificacion,
            "parentesco": m.parentesco,
            "estado": m.estado,
            "residente_id": m.persona_residente_fk,
            "residente_nombre": (
                f"{residente.nombres} {residente.apellidos}"
                if residente
                else "Desconocido"
            ),
        })

    return ViviendaDetalleResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        estado=vivienda.estado,
        propietarios=[
            {
                "persona_id": prop[1].persona_pk,
                "nombres": prop[1].nombres,
                "apellidos": prop[1].apellidos,
                "identificacion": prop[1].identificacion,
                "correo": prop[1].correo,
                "celular": prop[1].celular,
                "tipo": prop[0].tipo_propietario,
                "estado": prop[0].estado,
            }
            for prop in propietarios_query
        ],
        residentes=[
            {
                "persona_id": r[1].persona_pk,
                "nombres": r[1].nombres,
                "apellidos": r[1].apellidos,
                "identificacion": r[1].identificacion,
                "correo": r[1].correo,
                "celular": r[1].celular,
                "estado": r[0].estado,
            }
            for r in residentes_query
        ],
        miembros=miembros_data,
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

    registrar_bitacora(db, usuario, "vivienda", vivienda.vivienda_pk, "crear",
                           f"Vivienda Mz {vivienda.manzana}, Villa {vivienda.villa} creada")
    
    
    return ViviendaResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        estado=vivienda.estado,
        total_residentes=0,
        total_miembros=0,
        propietarios=[],
        residentes_count=0,
        miembros_count=0,
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

    registrar_bitacora(db, usuario, "vivienda", vivienda_id, "actualizar",
                       f"Vivienda Mz {vivienda.manzana}, Villa {vivienda.villa} actualizada")

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

    propietarios_query = (
        db.query(PropietarioVivienda, Persona)
        .join(
            Persona,
            PropietarioVivienda.persona_propietario_fk
            == Persona.persona_pk,
        )
        .filter(
            PropietarioVivienda.vivienda_propiedad_fk == vivienda_id,
            PropietarioVivienda.eliminado == False,
            Persona.eliminado == False,
        )
        .all()
    )

    return ViviendaResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        estado=vivienda.estado,
        total_residentes=total_residentes,
        total_miembros=total_miembros,
        propietarios=[
            {
                "persona_id": prop[1].persona_pk,
                "nombres": prop[1].nombres,
                "apellidos": prop[1].apellidos,
                "identificacion": prop[1].identificacion,
                "correo": prop[1].correo,
                "celular": prop[1].celular,
                "tipo": prop[0].tipo_propietario,
                "estado": prop[0].estado,
            }
            for prop in propietarios_query
        ],
        residentes_count=total_residentes,
        miembros_count=total_miembros,
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

    if request.motivo:
        vivienda.motivo_eliminado = request.motivo

    estado_anterior = vivienda.estado

    vivienda.estado = request.estado
    vivienda.fecha_actualizado = datetime.utcnow()
    vivienda.usuario_actualizado = request.usuario_actualizado

    db.commit()

    registrar_bitacora(db, usuario, "vivienda", vivienda.vivienda_pk,
                       "cambiar_estado",
                       f"Vivienda {vivienda.manzana}-{vivienda.villa} ahora {request.estado}",
                       valor_anterior=estado_anterior, valor_nuevo=request.estado)

    accion = "activada" if request.estado == "activo" else "desactivada"
    return {
        "success": True,
        "vivienda_id": vivienda.vivienda_pk,
        "estado": vivienda.estado,
        "mensaje": f"Vivienda {accion} exitosamente",
    }


class ViviendaMasivaCreate(BaseModel):
    manzana: str = Field(..., min_length=1, max_length=10)
    cantidad: int = Field(..., ge=1, le=50)
    usuario_creado: str = Field(default="")
    fecha_creado: Optional[str] = None


@router.post("/masivo", response_model=dict, status_code=201)
def crear_viviendas_masivo(
    request: ViviendaMasivaCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Crea viviendas en lote para una manzana."""
    mz = request.manzana.strip().upper()
    creadas = 0
    omitidas = []
    nuevas = []

    fecha = (
        datetime.fromisoformat(request.fecha_creado)
        if request.fecha_creado
        else datetime.utcnow()
    )

    for villa_num in range(1, request.cantidad + 1):
        villa = str(villa_num)
        existente = (
            db.query(Vivienda)
            .filter(
                Vivienda.manzana == mz,
                Vivienda.villa == villa,
            )
            .first()
        )
        if existente:
            omitidas.append(f"Villa {villa_num}")
            continue

        v = Vivienda(
            manzana=mz,
            villa=villa,
            estado="activo",
            usuario_creado=request.usuario_creado,
            fecha_creado=fecha,
        )
        nuevas.append(v)

    if nuevas:
        db.add_all(nuevas)
        db.commit()
        creadas = len(nuevas)

    registrar_bitacora(db, usuario, "vivienda", 0, "crear_masivo",
                       f"Manzana {mz}: {creadas} creadas, {len(omitidas)} omitidas")

    return {
        "creadas": creadas,
        "omitidas": omitidas,
        "manzana": mz,
    }


@router.post(
    "/cambio-propietario",
    response_model=ViviendaCambioPropietarioResponse,
)
def cambio_propietario(
    request: ViviendaCambioPropietarioRequest,
    db: Session = Depends(get_db),
    usuario: dict = Depends(requerir_rol("admin")),
):
    """Asigna un nuevo propietario a una vivienda."""
    if not request.motivo or not request.motivo.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El motivo es obligatorio",
        )

    vivienda = (
        db.query(Vivienda)
        .filter(
            Vivienda.vivienda_pk == request.vivienda_id,
            Vivienda.eliminado == False,
        )
        .first()
    )
    if not vivienda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vivienda no encontrada",
        )

    persona = (
        db.query(Persona)
        .filter(
            Persona.persona_pk == request.nuevo_propietario_id,
            Persona.estado == "activo",
        )
        .first()
    )
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propietario no encontrado",
        )

    ya_asignado = (
        db.query(PropietarioVivienda)
        .filter(
            PropietarioVivienda.vivienda_propiedad_fk == request.vivienda_id,
            PropietarioVivienda.persona_propietario_fk == request.nuevo_propietario_id,
        )
        .first()
    )
    if ya_asignado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El propietario ya esta asignado a esta vivienda",
        )

    propietario_anterior_id = None
    if request.tipo == "titular":
        anterior = (
            db.query(PropietarioVivienda)
            .filter(
                PropietarioVivienda.vivienda_propiedad_fk == request.vivienda_id,
                PropietarioVivienda.tipo_propietario == "titular",
                PropietarioVivienda.estado == "activo",
                PropietarioVivienda.eliminado == False,
            )
            .first()
        )
        if anterior:
            propietario_anterior_id = anterior.persona_propietario_fk
            anterior.estado = "inactivo"
            anterior.fecha_actualizado = datetime.utcnow()
            anterior.usuario_actualizado = request.usuario_actualizado

    fecha = (
        datetime.fromisoformat(request.fecha_actualizado)
        if request.fecha_actualizado
        else datetime.utcnow()
    )

    nuevo = PropietarioVivienda(
        vivienda_propiedad_fk=request.vivienda_id,
        persona_propietario_fk=request.nuevo_propietario_id,
        tipo_propietario=request.tipo,
        estado="activo",
        usuario_creado=request.usuario_actualizado,
        fecha_creado=fecha,
    )
    db.add(nuevo)

    residente_reasociado = False
    if propietario_anterior_id:
        ...
        residente_anterior = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.vivienda_reside_fk == request.vivienda_id,
            ResidenteVivienda.persona_residente_fk == propietario_anterior_id,
            ResidenteVivienda.estado == "activo",
            ResidenteVivienda.eliminado == False,
        ).first()
        if residente_anterior:
            residente_anterior.estado = "inactivo"
            residente_anterior.fecha_actualizado = datetime.utcnow()
            residente_existente = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.vivienda_reside_fk == request.vivienda_id,
                ResidenteVivienda.persona_residente_fk == request.nuevo_propietario_id,
                ResidenteVivienda.eliminado == False,
            ).first()
            if residente_existente:
                residente_existente.estado = "activo"
                residente_existente.fecha_actualizado = datetime.utcnow()
            else:
                nuevo_residente = ResidenteVivienda(
                    vivienda_reside_fk=request.vivienda_id,
                    persona_residente_fk=request.nuevo_propietario_id,
                    estado="activo",
                    usuario_creado=request.usuario_actualizado,
                )
                db.add(nuevo_residente)
            residente_reasociado = True

    registrar_bitacora(db, usuario, "propietario_vivienda", request.vivienda_id,
                       "cambiar_propietario",
                       f"Cambio de propietario. Anterior: {propietario_anterior_id or 'ninguno'}. Nuevo: {request.nuevo_propietario_id}",
                       valor_anterior=str(propietario_anterior_id or ''), valor_nuevo=str(request.nuevo_propietario_id))

    db.commit()

    return ViviendaCambioPropietarioResponse(
        mensaje=(
            "Propietario asignado correctamente. "
            "Nuevo propietario asignado como residente de la vivienda."
            if residente_reasociado
            else "Propietario asignado correctamente"
        ),
        vivienda_id=request.vivienda_id,
        propietario_anterior_id=propietario_anterior_id,
        nuevo_propietario_id=request.nuevo_propietario_id,
        tipo=request.tipo,
    )
