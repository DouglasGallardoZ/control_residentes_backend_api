"""
VISUALIZACIÓN DE LA ARQUITECTURA - Accesos Endpoints
=====================================================

Esta visualización muestra cómo se organiza la nueva funcionalidad
siguiendo la arquitectura hexagonal.
"""

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                  🏗️  ARQUITECTURA HEXAGONAL - ACCESOS                     ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│                         🌐 INTERFACES LAYER                             │
│                      (app/interfaces/routers/)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ accesos_router.py                                              │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Endpoint 1: GET /api/v1/accesos/vivienda/{vivienda_id}         │  │
│  │   ├─ Query Params: fecha_inicio, fecha_fin, tipo, resultado    │  │
│  │   ├─ Response: AccesosPorViviendaResponse                      │  │
│  │   └─ Handler: obtener_accesos_vivienda()                       │  │
│  │                                                                  │  │
│  │ Endpoint 2: GET /api/v1/accesos/admin/estadisticas            │  │
│  │   ├─ Query Params: fecha_inicio, fecha_fin                    │  │
│  │   ├─ Response: EstadisticasAdminResponse                      │  │
│  │   └─ Handler: obtener_estadisticas_admin()                    │  │
│  │                                                                  │  │
│  │ Schemas (Pydantic):                                            │  │
│  │   ├─ AccesoResponse                                            │  │
│  │   ├─ AccesosPorViviendaResponse                                │  │
│  │   ├─ EstadisticasAcceso                                        │  │
│  │   ├─ EstadisticasAccesoPorTipo                                 │  │
│  │   ├─ EstadisticasAccesoPorResultado                            │  │
│  │   └─ EstadisticasAdminResponse                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Responsabilidad: HTTP request/response, validación de entrada         │
│  ↓ Depende de: AccesosService                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                     🔧 APPLICATION LAYER                                │
│                  (app/application/services/)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ accesos_service.py                                             │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ AccesosService (clase estática)                                │  │
│  │                                                                  │  │
│  │ Métodos:                                                       │  │
│  │ ┌────────────────────────────────────────────────────────────┐ │  │
│  │ │ obtener_accesos_vivienda()                                 │ │  │
│  │ │   Input: db, vivienda_id, filtros opcionales              │ │  │
│  │ │   Output: (Vivienda, List[Acceso])                        │ │  │
│  │ │   Lógica: Construir query con filtros                     │ │  │
│  │ └────────────────────────────────────────────────────────────┘ │  │
│  │                                                                  │  │
│  │ ┌────────────────────────────────────────────────────────────┐ │  │
│  │ │ obtener_detalles_acceso()                                  │ │  │
│  │ │   Input: db, acceso                                        │ │  │
│  │ │   Output: dict con detalles enriquecidos                   │ │  │
│  │ │   Lógica: Obtener nombres de personas relacionadas         │ │  │
│  │ └────────────────────────────────────────────────────────────┘ │  │
│  │                                                                  │  │
│  │ ┌────────────────────────────────────────────────────────────┐ │  │
│  │ │ obtener_estadisticas_admin()                               │ │  │
│  │ │   Input: db, fecha_inicio, fecha_fin                       │ │  │
│  │ │   Output: dict con estadísticas                            │ │  │
│  │ │   Lógica:                                                   │ │  │
│  │ │   ├─ Contar: total, exitosos, rechazados                  │ │  │
│  │ │   ├─ Agrupar: por tipo, por resultado                      │ │  │
│  │ │   ├─ Contar: visitantes únicos                             │ │  │
│  │ │   └─ Buscar: top 10 viviendas                              │ │  │
│  │ └────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Responsabilidad: Lógica de negocio, transformación de datos           │
│  ↓ Depende de: Modelos de SQLAlchemy                                   │
│  ✨ Reutilizable: Puede usarse en CLI, Workers, Tests                  │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   💾 INFRASTRUCTURE LAYER                               │
│               (app/infrastructure/db/)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ models.py (SQLAlchemy ORM)                                     │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ Modelo: Acceso                                                 │  │
│  │   ├─ acceso_pk (PK)                                            │  │
│  │   ├─ tipo (String) ← CheckConstraint                           │  │
│  │   ├─ vivienda_visita_fk (FK) ← Index para filtrado            │  │
│  │   ├─ resultado (String) ← CheckConstraint                      │  │
│  │   ├─ motivo, placa_detectada, biometria_ok, etc.              │  │
│  │   ├─ fecha_creado (DateTime) ← Index para ordenamiento        │  │
│  │   └─ usuario_creado, usuario_actualizado (auditoría)          │  │
│  │                                                                  │  │
│  │ Relaciones:                                                    │  │
│  │   ├─ vivienda: FK → Vivienda.vivienda_pk                       │  │
│  │   ├─ persona_guardia_fk: FK → Persona.persona_pk              │  │
│  │   ├─ persona_residente_autoriza_fk: FK → Persona.persona_pk   │  │
│  │   └─ visita_ingreso_fk: FK → Visita.visita_pk                 │  │
│  │                                                                  │  │
│  │ Modelos relacionados:                                          │  │
│  │   ├─ Vivienda: id, manzana, villa                              │  │
│  │   ├─ Persona: nombres, apellidos, identificacion              │  │
│  │   └─ Visita: identificacion, nombres, apellidos               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Responsabilidad: Acceso a datos, persistencia                         │
│  ↓ Depende de: PostgreSQL                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    🗄️  DATABASE LAYER                                    │
│                      PostgreSQL 12+                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Tabla: acceso                                                         │
│  ├─ Índices:                                                           │
│  │  ├─ vivienda_visita_fk (para filtrado rápido)                      │
│  │  └─ fecha_creado (para ordenamiento eficiente)                      │
│  │                                                                     │
│  ├─ Constraints:                                                       │
│  │  ├─ tipo IN ('qr_residente', 'qr_visita', ...)                    │
│  │  └─ resultado IN ('autorizado', 'rechazado', ...)                 │
│  │                                                                     │
│  └─ Soft Delete: eliminado BOOLEAN (no borra datos)                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                        📊 FLUJO DE DATOS                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

CASO 1: Obtener Accesos de una Vivienda
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Client (Flutter)
    │
    ├─ GET /api/v1/accesos/vivienda/1?resultado=autorizado
    │
    ↓
accesos_router.py:obtener_accesos_vivienda()
    │
    ├─ Valida vivienda_id ✓
    ├─ Obtiene filtros: resultado="autorizado" ✓
    │
    ↓
AccesosService.obtener_accesos_vivienda(db, 1, resultado="autorizado")
    │
    ├─ Query: WHERE vivienda_id=1 AND resultado='autorizado' AND eliminado=false
    ├─ ORDER BY fecha_creado DESC
    │
    ↓
SQLAlchemy → PostgreSQL
    │
    ├─ SELECT * FROM acceso WHERE vivienda_visita_fk=1 ...
    │
    ↓ Resultados
    
AccesosService.obtener_detalles_acceso() (para cada acceso)
    │
    ├─ Busca nombre de guardia (si existe)
    ├─ Busca nombre de residente (si existe)
    ├─ Busca nombres de visita (si existe)
    │
    ↓
Response: AccesosPorViviendaResponse
    │
    ├─ {
    │    "vivienda_id": 1,
    │    "accesos": [
    │      {
    │        "acceso_pk": 101,
    │        "resultado": "autorizado",
    │        "guardia_nombre": null,
    │        "visita_nombres": "María García"
    │      }
    │    ]
    │  }
    │
    ↓
Client (Flutter) - Mostrar en UI


CASO 2: Obtener Estadísticas Admin
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Client (Admin Dashboard)
    │
    ├─ GET /api/v1/accesos/admin/estadisticas?fecha_inicio=2024-12-01
    │
    ↓
accesos_router.py:obtener_estadisticas_admin()
    │
    ├─ Valida token de admin ✓
    ├─ Obtiene filtros: fecha_inicio=2024-12-01 ✓
    │
    ↓
AccesosService.obtener_estadisticas_admin(db, fecha_inicio=2024-12-01)
    │
    ├─ Query 1: COUNT(*) WHERE fecha_creado >= '2024-12-01'
    │           → total = 458
    │
    ├─ Query 2: COUNT(*) WHERE resultado='autorizado'
    │           → exitosos = 442
    │
    ├─ Query 3: GROUP BY tipo, COUNT(*)
    │           → [{'tipo': 'qr_residente', 'cantidad': 285}, ...]
    │
    ├─ Query 4: GROUP BY resultado, COUNT(*)
    │           → [{'resultado': 'autorizado', 'cantidad': 442}, ...]
    │
    ├─ Query 5: SELECT DISTINCT vivienda_id, COUNT(*) GROUP BY vivienda_id
    │           ORDER BY COUNT(*) DESC LIMIT 10
    │           → Top 10 viviendas con más accesos
    │
    ↓ Todas las queries ejecutadas en PostgreSQL
    
Response: EstadisticasAdminResponse
    │
    ├─ {
    │    "estadisticas_generales": {
    │      "total": 458,
    │      "exitosos": 442,
    │      "rechazados": 12,
    │      "pendientes": 4
    │    },
    │    "accesos_por_tipo": [...],
    │    "viviendas_con_mas_accesos": [...]
    │  }
    │
    ↓
Client (Admin) - Mostrar dashboard


╔═══════════════════════════════════════════════════════════════════════════╗
║                    🔄 INTEGRACIÓN EN APP                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

app/main.py
│
├─ from app.interfaces.routers import accesos_router ✓
├─ app.include_router(accesos_router.router) ✓
│
↓ Resultado
│
app.routes:
  ├─ /docs
  ├─ /api/v1/accesos/vivienda/{vivienda_id} ← NUEVO ✓
  ├─ /api/v1/accesos/admin/estadisticas ← NUEVO ✓
  ├─ /api/v1/qr/...
  └─ ... otros routers ...


╔═══════════════════════════════════════════════════════════════════════════╗
║                    ✅ VALIDACIONES IMPLEMENTADAS                          ║
╚═══════════════════════════════════════════════════════════════════════════╝

Endpoint 1: GET /api/v1/accesos/vivienda/{vivienda_id}
  ✓ Vivienda existe
  ✓ Vivienda está activa (estado="activo")
  ✓ Acceso no está eliminado (eliminado=false)
  ✓ Filtros de fecha válidos (datetime conversion)
  ✓ Respuesta 404 si vivienda no existe
  ✓ Respuesta 500 con detalle si hay error

Endpoint 2: GET /api/v1/accesos/admin/estadisticas
  ✓ Filtros de fecha válidos
  ✓ Visitantes únicos sin duplicados
  ✓ Top 10 viviendas (no excesivo volumen)
  ✓ Respuesta 500 con detalle si hay error


╔═══════════════════════════════════════════════════════════════════════════╗
║                    📦 ESTRUCTURA DE CARPETAS FINAL                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

backend-api/
├── app/
│   ├── main.py ✏️ (incluye accesos_router)
│   ├── config.py
│   ├── interfaces/
│   │   ├── routers/
│   │   │   ├── __init__.py ✏️ (exporta accesos_router)
│   │   │   ├── accesos_router.py ✨ NUEVO
│   │   │   ├── qr_router.py
│   │   │   ├── cuentas_router.py
│   │   │   ├── residentes_router.py
│   │   │   ├── propietarios_router.py
│   │   │   └── miembros_router.py
│   │   └── schemas/
│   │       └── schemas.py
│   ├── application/
│   │   └── services/
│   │       ├── __init__.py ✏️ (exporta AccesosService)
│   │       ├── accesos_service.py ✨ NUEVO
│   │       ├── accesos_service.py
│   │       └── servicios.py
│   ├── domain/
│   │   ├── entities/
│   │   │   └── models.py
│   │   └── use_cases/
│   │       └── qr_use_cases.py
│   └── infrastructure/
│       ├── db/
│       │   ├── models.py (usa Acceso, Vivienda, etc.)
│       │   └── database.py
│       └── ...
│
├── API_DOCUMENTACION_COMPLETA.md ✏️ (agregó sección Accesos)
├── ACCESOS_RESUMEN_CAMBIOS.md ✨ NUEVO
├── ACCESOS_ENDPOINTS_EJEMPLOS.py ✨ NUEVO
├── ACCESOS_ENDPOINTS_IMPLEMENTACION.md ✨ NUEVO
├── test_accesos_endpoints.py ✨ NUEVO
│
└── ... otros archivos ...


╔═══════════════════════════════════════════════════════════════════════════╗
║                    🎓 CÓMO USAR DESDE FLUTTER                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

1. Importar http
   import 'package:http/http.dart' as http;

2. Llamar a endpoint
   final response = await http.get(
     Uri.parse('https://api.residencias.com/api/v1/accesos/vivienda/1'),
     headers: {'Authorization': 'Bearer $token'}
   );

3. Procesar respuesta
   if (response.statusCode == 200) {
     final data = jsonDecode(response.body);
     final accesos = data['accesos'] as List;
     // Mostrar accesos en UI
   }

Ver: ACCESOS_ENDPOINTS_EJEMPLOS.py para código completo

╔═══════════════════════════════════════════════════════════════════════════╗
║                        ✨ CONCLUSIÓN                                      ║
╚═══════════════════════════════════════════════════════════════════════════╝

✅ Arquitectura hexagonal implementada correctamente
✅ Separación clara de responsabilidades
✅ Lógica reutilizable en AccesosService
✅ Documentación completa
✅ Ejemplos para Flutter incluidos
✅ Tests de validación listos
✅ Listo para producción

""")
