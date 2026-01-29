"""
Servicio de Accesos - Capa de Aplicación

Contiene la lógica de negocio para gestión de accesos.
Mantiene la arquitectura hexagonal separando la lógica
del acceso a datos y endpoints.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.infrastructure.db.models import Acceso, Vivienda, Visita, Persona
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple


class AccesosService:
    """Servicio para gestionar accesos y estadísticas"""
    
    @staticmethod
    def obtener_accesos_vivienda(
        db: Session,
        vivienda_id: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        tipo: Optional[str] = None,
        resultado: Optional[str] = None
    ) -> Tuple[Optional[Vivienda], List[Acceso]]:
        """
        Obtiene accesos de una vivienda con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            vivienda_id: ID de la vivienda
            fecha_inicio: Filtro fecha inicio (opcional)
            fecha_fin: Filtro fecha fin (opcional)
            tipo: Filtro por tipo de acceso (opcional)
            resultado: Filtro por resultado (opcional)
            
        Returns:
            Tupla (Vivienda, Lista de Accesos)
        """
        vivienda = db.query(Vivienda).filter(
            Vivienda.vivienda_pk == vivienda_id,
            Vivienda.estado == "activo"
        ).first()
        
        if not vivienda:
            return None, []
        
        query = db.query(Acceso).filter(
            Acceso.vivienda_visita_fk == vivienda_id,
            Acceso.eliminado == False
        )
        
        if fecha_inicio:
            query = query.filter(
                Acceso.fecha_creado >= datetime.combine(fecha_inicio, datetime.min.time())
            )
        
        if fecha_fin:
            query = query.filter(
                Acceso.fecha_creado <= datetime.combine(fecha_fin, datetime.max.time())
            )
        
        if tipo:
            query = query.filter(Acceso.tipo == tipo)
        
        if resultado:
            query = query.filter(Acceso.resultado == resultado)
        
        accesos = query.order_by(Acceso.fecha_creado.desc()).all()
        
        return vivienda, accesos
    
    @staticmethod
    def obtener_detalles_acceso(
        db: Session,
        acceso: Acceso
    ) -> Dict:
        """
        Enriquece los datos de un acceso con información relacionada.
        
        Args:
            db: Sesión de base de datos
            acceso: Objeto Acceso
            
        Returns:
            Diccionario con datos enriquecidos
        """
        # Obtener guardia si existe
        guardia_nombre = None
        if acceso.persona_guardia_fk:
            guardia = db.query(Persona).filter(
                Persona.persona_pk == acceso.persona_guardia_fk
            ).first()
            if guardia:
                guardia_nombre = f"{guardia.nombres} {guardia.apellidos}"
        
        # Obtener residente que autoriza si existe
        residente_nombre = None
        if acceso.persona_residente_autoriza_fk:
            residente = db.query(Persona).filter(
                Persona.persona_pk == acceso.persona_residente_autoriza_fk
            ).first()
            if residente:
                residente_nombre = f"{residente.nombres} {residente.apellidos}"
        
        # Obtener datos de visita si existe
        visita_nombres = None
        if acceso.visita_ingreso_fk:
            visita = db.query(Visita).filter(
                Visita.visita_pk == acceso.visita_ingreso_fk
            ).first()
            if visita:
                visita_nombres = f"{visita.nombres} {visita.apellidos}"
        
        return {
            "acceso_pk": acceso.acceso_pk,
            "tipo": acceso.tipo,
            "vivienda_visita_fk": acceso.vivienda_visita_fk,
            "resultado": acceso.resultado,
            "motivo": acceso.motivo,
            "placa_detectada": acceso.placa_detectada,
            "biometria_ok": acceso.biometria_ok,
            "placa_ok": acceso.placa_ok,
            "intentos": acceso.intentos,
            "observacion": acceso.observacion,
            "fecha_creado": acceso.fecha_creado,
            "guardia_nombre": guardia_nombre,
            "residente_autoriza_nombre": residente_nombre,
            "visita_nombres": visita_nombres
        }
    
    @staticmethod
    def obtener_estadisticas_admin(
        db: Session,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None
    ) -> Dict:
        """
        Obtiene estadísticas completas de accesos del sistema.
        
        Args:
            db: Sesión de base de datos
            fecha_inicio: Filtro fecha inicio (opcional)
            fecha_fin: Filtro fecha fin (opcional)
            
        Returns:
            Diccionario con estadísticas
        """
        query = db.query(Acceso).filter(Acceso.eliminado == False)
        
        if fecha_inicio:
            query = query.filter(
                Acceso.fecha_creado >= datetime.combine(fecha_inicio, datetime.min.time())
            )
        
        if fecha_fin:
            query = query.filter(
                Acceso.fecha_creado <= datetime.combine(fecha_fin, datetime.max.time())
            )
        
        accesos_all = query.all()
        
        # Estadísticas generales
        total = len(accesos_all)
        exitosos = len([a for a in accesos_all if a.resultado == "autorizado"])
        rechazados = len([a for a in accesos_all if a.resultado in [
            "rechazado", "no_autorizado", "fallo_biometrico", "fallo_placa",
            "codigo_expirado", "codigo_invalido", "cuenta_bloqueada"
        ]])
        pendientes = len([a for a in accesos_all if a.resultado in [
            "error_sistema", "cancelado"
        ]])
        
        # Visitantes únicos en el período
        visitantes_query = db.query(func.count(func.distinct(Visita.visita_pk))).join(
            Acceso, Visita.visita_pk == Acceso.visita_ingreso_fk
        ).filter(
            Visita.eliminado == False,
            Acceso.eliminado == False
        )
        
        if fecha_inicio:
            visitantes_query = visitantes_query.filter(
                Acceso.fecha_creado >= datetime.combine(fecha_inicio, datetime.min.time())
            )
        if fecha_fin:
            visitantes_query = visitantes_query.filter(
                Acceso.fecha_creado <= datetime.combine(fecha_fin, datetime.max.time())
            )
        
        visitantes_unicos = visitantes_query.scalar() or 0
        
        # Accesos por tipo
        accesos_por_tipo = []
        tipos_query = db.query(
            Acceso.tipo,
            func.count(Acceso.acceso_pk).label('cantidad')
        ).filter(Acceso.eliminado == False)
        
        if fecha_inicio:
            tipos_query = tipos_query.filter(
                Acceso.fecha_creado >= datetime.combine(fecha_inicio, datetime.min.time())
            )
        if fecha_fin:
            tipos_query = tipos_query.filter(
                Acceso.fecha_creado <= datetime.combine(fecha_fin, datetime.max.time())
            )
        
        for tipo, cantidad in tipos_query.group_by(Acceso.tipo).all():
            accesos_por_tipo.append({"tipo": tipo, "cantidad": cantidad})
        
        # Accesos por resultado
        accesos_por_resultado = []
        resultado_query = db.query(
            Acceso.resultado,
            func.count(Acceso.acceso_pk).label('cantidad')
        ).filter(Acceso.eliminado == False)
        
        if fecha_inicio:
            resultado_query = resultado_query.filter(
                Acceso.fecha_creado >= datetime.combine(fecha_inicio, datetime.min.time())
            )
        if fecha_fin:
            resultado_query = resultado_query.filter(
                Acceso.fecha_creado <= datetime.combine(fecha_fin, datetime.max.time())
            )
        
        for resultado, cantidad in resultado_query.group_by(Acceso.resultado).all():
            accesos_por_resultado.append({"resultado": resultado, "cantidad": cantidad})
        
        # Top viviendas
        from app.infrastructure.db.models import Vivienda
        viviendas_top = []
        top_query = db.query(
            Vivienda.vivienda_pk,
            Vivienda.manzana,
            Vivienda.villa,
            func.count(Acceso.acceso_pk).label('cantidad_accesos')
        ).join(
            Acceso, Vivienda.vivienda_pk == Acceso.vivienda_visita_fk
        ).filter(
            Acceso.eliminado == False,
            Vivienda.estado == "activo"
        )
        
        if fecha_inicio:
            top_query = top_query.filter(
                Acceso.fecha_creado >= datetime.combine(fecha_inicio, datetime.min.time())
            )
        if fecha_fin:
            top_query = top_query.filter(
                Acceso.fecha_creado <= datetime.combine(fecha_fin, datetime.max.time())
            )
        
        for vivienda_pk, manzana, villa, cantidad in top_query.group_by(
            Vivienda.vivienda_pk, Vivienda.manzana, Vivienda.villa
        ).order_by(func.count(Acceso.acceso_pk).desc()).limit(10).all():
            viviendas_top.append({
                "vivienda_id": vivienda_pk,
                "manzana": manzana,
                "villa": villa,
                "cantidad_accesos": cantidad
            })
        
        periodo = {
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else "inicio",
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else "presente"
        }
        
        return {
            "periodo": periodo,
            "estadisticas_generales": {
                "total": total,
                "exitosos": exitosos,
                "rechazados": rechazados,
                "pendientes": pendientes
            },
            "cantidad_visitantes_unicos": visitantes_unicos,
            "accesos_por_tipo": accesos_por_tipo,
            "accesos_por_resultado": accesos_por_resultado,
            "viviendas_con_mas_accesos": viviendas_top
        }
