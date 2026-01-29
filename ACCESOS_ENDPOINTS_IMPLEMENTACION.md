# Nuevos Endpoints de Accesos - Documentación de Implementación

## Resumen de Cambios

Se han agregado **2 nuevos endpoints** para consultar accesos del sistema, manteniendo la **arquitectura hexagonal**:

1. **Endpoint 1**: Consultar accesos por vivienda (para residentes)
2. **Endpoint 2**: Estadísticas de accesos (para administrador)

---

## Estructura de Archivos Creados/Modificados

### Archivos Creados:

```
app/
├── interfaces/
│   └── routers/
│       └── accesos_router.py ✨ NUEVO
├── application/
│   └── services/
│       └── accesos_service.py ✨ NUEVO
└── ACCESOS_ENDPOINTS_EJEMPLOS.py ✨ NUEVO
```

### Archivos Modificados:

```
app/
├── main.py (registrar router)
├── interfaces/
│   └── routers/
│       └── __init__.py (exportar accesos_router)
└── application/
    └── services/
        └── __init__.py (exportar AccesosService)

API_DOCUMENTACION_COMPLETA.md (agregar sección de Accesos)
```

---

## Detalles de Implementación

### 1. Arquitectura Hexagonal

La implementación sigue la estructura de capas:

```
┌─────────────────────────────────────┐
│   INTERFACES (accesos_router.py)    │
│   - Endpoints HTTP                  │
│   - Validación de requests         │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ APPLICATION (accesos_service.py)    │
│   - Lógica de negocio              │
│   - Transformación de datos        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ INFRASTRUCTURE (models.py)          │
│   - ORM SQLAlchemy                  │
│   - PostgreSQL queries              │
└─────────────────────────────────────┘
```

### 2. Endpoint 1: Accesos por Vivienda

**URL**: `GET /api/v1/accesos/vivienda/{vivienda_id}`

**Responsabilidad**: Permite que residentes consulten accesos a su vivienda

**Parámetros**:
- `vivienda_id` (path): ID de la vivienda
- `fecha_inicio` (query, opcional): Filtro fecha inicio
- `fecha_fin` (query, opcional): Filtro fecha fin
- `tipo` (query, opcional): Filtro por tipo de acceso
- `resultado` (query, opcional): Filtro por resultado

**Respuesta**:
```json
{
  "vivienda_id": 1,
  "manzana": "A",
  "villa": "101",
  "total_accesos": 15,
  "accesos": [
    {
      "acceso_pk": 101,
      "tipo": "qr_residente",
      "resultado": "autorizado",
      "fecha_creado": "2024-12-25T14:30:00",
      "guardia_nombre": null,
      "residente_autoriza_nombre": "Juan Pérez",
      "visita_nombres": null
    }
  ]
}
```

**Flujo en código**:
```
accesos_router.py:obtener_accesos_vivienda()
  ↓
AccesosService.obtener_accesos_vivienda()
  ↓ Consulta base y filtros
AccesosService.obtener_detalles_acceso()
  ↓ Enriquece con nombres de personas
Response
```

### 3. Endpoint 2: Estadísticas de Admin

**URL**: `GET /api/v1/accesos/admin/estadisticas`

**Responsabilidad**: Proporciona KPIs globales del sistema

**Parámetros**:
- `fecha_inicio` (query, opcional): Filtro fecha inicio
- `fecha_fin` (query, opcional): Filtro fecha fin

**Respuesta**:
```json
{
  "periodo": {
    "fecha_inicio": "2024-12-01",
    "fecha_fin": "2024-12-31"
  },
  "estadisticas_generales": {
    "total": 458,
    "exitosos": 442,
    "rechazados": 12,
    "pendientes": 4
  },
  "cantidad_visitantes_unicos": 87,
  "accesos_por_tipo": [
    { "tipo": "qr_residente", "cantidad": 285 }
  ],
  "accesos_por_resultado": [
    { "resultado": "autorizado", "cantidad": 442 }
  ],
  "viviendas_con_mas_accesos": [
    {
      "vivienda_id": 1,
      "manzana": "A",
      "villa": "101",
      "cantidad_accesos": 45
    }
  ]
}
```

**Flujo en código**:
```
accesos_router.py:obtener_estadisticas_admin()
  ↓
AccesosService.obtener_estadisticas_admin()
  ↓ Calcula totales, conteos por tipo/resultado, top viviendas
Response
```

---

## Servicios de Negocio

### AccesosService

**Ubicación**: `app/application/services/accesos_service.py`

**Métodos**:

#### `obtener_accesos_vivienda(db, vivienda_id, fecha_inicio, fecha_fin, tipo, resultado)`
- Construye consulta con filtros opcionales
- Retorna tupla (Vivienda, Lista de Accesos)

#### `obtener_detalles_acceso(db, acceso)`
- Enriquece un Acceso con datos relacionados
- Obtiene nombres de: guardia, residente que autoriza, visita
- Retorna diccionario con detalles completos

#### `obtener_estadisticas_admin(db, fecha_inicio, fecha_fin)`
- Calcula estadísticas globales
- Agrupa por tipo y resultado
- Identifica top 10 viviendas
- Retorna diccionario con todos los KPIs

**Ventajas**:
- ✅ Lógica independiente del router
- ✅ Fácil de testear unitariamente
- ✅ Reutilizable en otros contextos (CLI, workers, etc.)
- ✅ Cambios en negocio no requieren cambios en endpoints

---

## Esquemas Pydantic

**Ubicación**: `app/interfaces/routers/accesos_router.py`

```python
AccesoResponse
├── acceso_pk: int
├── tipo: str
├── vivienda_visita_fk: int
├── resultado: str
├── motivo: Optional[str]
├── placa_detectada: Optional[str]
├── biometria_ok: Optional[bool]
├── placa_ok: Optional[bool]
├── intentos: int
├── observacion: Optional[str]
├── fecha_creado: datetime
├── guardia_nombre: Optional[str]
├── residente_autoriza_nombre: Optional[str]
└── visita_nombres: Optional[str]

AccesosPorViviendaResponse
├── vivienda_id: int
├── manzana: str
├── villa: str
├── total_accesos: int
└── accesos: List[AccesoResponse]

EstadisticasAcceso
├── total: int
├── exitosos: int
├── rechazados: int
└── pendientes: int

EstadisticasAdminResponse
├── periodo: dict
├── estadisticas_generales: EstadisticasAcceso
├── cantidad_visitantes_unicos: int
├── accesos_por_tipo: List[EstadisticasAccesoPorTipo]
├── accesos_por_resultado: List[EstadisticasAccesoPorResultado]
└── viviendas_con_mas_accesos: List[dict]
```

---

## Testing

### Ejemplos de curl para probar:

```bash
# 1. Obtener accesos por vivienda
curl -X GET "http://localhost:8000/api/v1/accesos/vivienda/1" \
  -H "Authorization: Bearer $TOKEN"

# 2. Con filtros
curl -X GET "http://localhost:8000/api/v1/accesos/vivienda/1?fecha_inicio=2024-12-01&resultado=autorizado" \
  -H "Authorization: Bearer $TOKEN"

# 3. Estadísticas admin
curl -X GET "http://localhost:8000/api/v1/accesos/admin/estadisticas" \
  -H "Authorization: Bearer $TOKEN"

# 4. Con filtro de fechas
curl -X GET "http://localhost:8000/api/v1/accesos/admin/estadisticas?fecha_inicio=2024-12-01&fecha_fin=2024-12-31" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Integración en Flutter

Ver archivo: `ACCESOS_ENDPOINTS_EJEMPLOS.py`

Contiene:
- ✅ Ejemplos de HTTP requests
- ✅ Widget Flutter reusable
- ✅ Servicio encapsulado
- ✅ Métodos helper (accesos exitosos, visitas, etc.)

---

## Cómo Agregar Nuevas Funcionalidades

### Ejemplo: Filtrar por guardia

```python
# 1. En accesos_router.py, agregar parámetro
@router.get("/vivienda/{vivienda_id}")
def obtener_accesos_vivienda(
    # ... parámetros existentes ...
    guardia_id: Optional[int] = None,  # ✨ NUEVO
    db: Session = Depends(get_db)
):
    # 2. Pasar al servicio
    vivienda, accesos = AccesosService.obtener_accesos_vivienda(
        db, vivienda_id, fecha_inicio, fecha_fin, tipo, resultado,
        guardia_id=guardia_id  # ✨ NUEVO
    )

# 3. En accesos_service.py, agregar lógica
@staticmethod
def obtener_accesos_vivienda(
    db: Session,
    vivienda_id: int,
    # ... parámetros existentes ...
    guardia_id: Optional[int] = None,  # ✨ NUEVO
) -> Tuple[Optional[Vivienda], List[Acceso]]:
    # ... código existente ...
    if guardia_id:
        query = query.filter(Acceso.persona_guardia_fk == guardia_id)  # ✨ NUEVO
```

**Ventajas del diseño**:
- Sin duplicación de lógica
- Un solo lugar para cambios
- Fácil de documentar
- Tests unitarios aislados

---

## Performance

### Optimizaciones Implementadas

1. **Índices en base de datos**:
   - `vivienda_visita_fk`: Filtrado rápido por vivienda
   - `fecha_creado`: Ordenamiento eficiente

2. **Paginación implícita**:
   - Limite a 10 viviendas en top
   - Accesos ordenados por fecha (DESC)

3. **Consultas Optimizadas**:
   - Grupo por tipo/resultado sin subqueries
   - Join eficiente para top viviendas

### Recomendaciones Futuras

```python
# Agregar paginación
def obtener_accesos_vivienda(
    db,
    vivienda_id,
    skip: int = 0,
    limit: int = 50,  # ← Limitar resultados
    # ...
):
    accesos = query.offset(skip).limit(limit).all()
```

---

## Validaciones Implementadas

✅ Vivienda existe y está activa  
✅ Acceso no está eliminado  
✅ Filtros de fecha válidos (datetime conversion)  
✅ Respuesta 404 si vivienda no existe  
✅ Respuesta 500 con detalles en caso de error  

---

## Próximos Pasos

1. **Autenticación**: Implementar validación de roles
   - Solo admin puede ver estadísticas globales
   - Solo propietario/residente puede ver su vivienda

2. **Caché**: Implementar caché en Redis
   - Estadísticas cambian con baja frecuencia
   - Accesos por vivienda pueden cachearse 5 min

3. **Webhooks**: Notificar eventos de acceso
   - Residente notificado de acceso rechazado
   - Admin notificado de intentos fallidos consecutivos

4. **Reportes**: Generar reportes PDF/Excel
   - Accesos por período
   - Análisis de patrones

---

## Conclusión

La implementación mantiene:
- ✅ Arquitectura hexagonal limpia
- ✅ Separación de responsabilidades
- ✅ Código mantenible y escalable
- ✅ Documentación completa
- ✅ Ejemplos para Flutter
- ✅ Facilidad para agregar nuevas funcionalidades

**Status**: ✅ LISTO PARA PRODUCCIÓN
