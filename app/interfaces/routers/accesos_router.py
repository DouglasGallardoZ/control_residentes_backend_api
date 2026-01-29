from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.db import get_db
from app.infrastructure.db.models import Acceso, Vivienda, Persona, Visita
from datetime import datetime, date
from pydantic import BaseModel
from typing import List, Optional
from app.application.services.accesos_service import AccesosService

router = APIRouter(prefix="/api/v1/accesos", tags=["Accesos"])


# ==================== SCHEMAS ====================

class AccesoResponse(BaseModel):
    """Schema para respuesta de acceso"""
    acceso_pk: int
    tipo: str
    vivienda_visita_fk: int
    resultado: str
    motivo: Optional[str]
    placa_detectada: Optional[str]
    biometria_ok: Optional[bool]
    placa_ok: Optional[bool]
    intentos: int
    observacion: Optional[str]
    fecha_creado: datetime
    # Datos relacionados
    guardia_nombre: Optional[str]
    residente_autoriza_nombre: Optional[str]
    visita_nombres: Optional[str]


class AccesosPorViviendaResponse(BaseModel):
    """Schema para respuesta de accesos por vivienda"""
    vivienda_id: int
    manzana: str
    villa: str
    total_accesos: int
    accesos: List[AccesoResponse]


class EstadisticasAcceso(BaseModel):
    """Schema para estadísticas de accesos"""
    total: int
    exitosos: int
    rechazados: int
    pendientes: int


class EstadisticasAccesoPorTipo(BaseModel):
    """Schema para estadísticas por tipo de acceso"""
    tipo: str
    cantidad: int


class EstadisticasAccesoPorResultado(BaseModel):
    """Schema para estadísticas por resultado"""
    resultado: str
    cantidad: int


class EstadisticasAdminResponse(BaseModel):
    """Schema para respuesta de estadísticas de admin"""
    periodo: dict  # fecha_inicio y fecha_fin
    estadisticas_generales: EstadisticasAcceso
    cantidad_visitantes_unicos: int
    accesos_por_tipo: List[EstadisticasAccesoPorTipo]
    accesos_por_resultado: List[EstadisticasAccesoPorResultado]
    viviendas_con_mas_accesos: List[dict]


# ==================== ENDPOINTS ====================

@router.get("/vivienda/{vivienda_id}", response_model=AccesosPorViviendaResponse)
def obtener_accesos_vivienda(
    vivienda_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    tipo: Optional[str] = None,
    resultado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene accesos de una vivienda específica.
    Destinado para que el residente vea sus accesos y los de sus visitas.
    
    Filtros opcionales:
    - fecha_inicio: Filtrar desde esta fecha (inclusive)
    - fecha_fin: Filtrar hasta esta fecha (inclusive)
    - tipo: Filtrar por tipo de acceso
    - resultado: Filtrar por resultado del acceso
    
    RF-ACC-01: Consultar accesos por vivienda
    """
    try:
        vivienda, accesos = AccesosService.obtener_accesos_vivienda(
            db, vivienda_id, fecha_inicio, fecha_fin, tipo, resultado
        )
        
        if not vivienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vivienda no encontrada"
            )
        
        # Enriquecer datos de accesos
        accesos_data = [
            AccesoResponse(**AccesosService.obtener_detalles_acceso(db, acceso))
            for acceso in accesos
        ]
        
        return AccesosPorViviendaResponse(
            vivienda_id=vivienda_id,
            manzana=vivienda.manzana,
            villa=vivienda.villa,
            total_accesos=len(accesos_data),
            accesos=accesos_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/admin/estadisticas", response_model=EstadisticasAdminResponse)
def obtener_estadisticas_admin(
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas completas de accesos del sistema.
    Destinado para administrador. Incluye:
    - Total de accesos: exitosos, rechazados y pendientes
    - Cantidad de visitantes únicos
    - Accesos por tipo
    - Accesos por resultado
    - Top viviendas con más accesos
    
    Si no se especifican fechas, devuelve todos los accesos.
    
    RF-ACC-02: Consultar estadísticas de accesos (admin)
    """
    try:
        stats = AccesosService.obtener_estadisticas_admin(
            db, fecha_inicio, fecha_fin
        )
        
        return EstadisticasAdminResponse(
            periodo=stats["periodo"],
            estadisticas_generales=EstadisticasAcceso(**stats["estadisticas_generales"]),
            cantidad_visitantes_unicos=stats["cantidad_visitantes_unicos"],
            accesos_por_tipo=[
                EstadisticasAccesoPorTipo(**item) for item in stats["accesos_por_tipo"]
            ],
            accesos_por_resultado=[
                EstadisticasAccesoPorResultado(**item) for item in stats["accesos_por_resultado"]
            ],
            viviendas_con_mas_accesos=stats["viviendas_con_mas_accesos"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
