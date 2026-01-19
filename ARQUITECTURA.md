"""
ARQUITECTURA HEXAGONAL - SISTEMA DE CONTROL DE ACCESO RESIDENCIAL
==================================================================

┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE INTERFACES                          │
│              (Puertos de Entrada - HTTP)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Routers FastAPI          Schemas Pydantic                     │
│  ├── qr_router.py         ├── QRGenerarPropio                 │
│  ├── cuentas_router.py    ├── CuentaCreate                    │
│  ├── residentes_router.py ├── ResidenteCreate                 │
│  ├── propietarios_router  ├── NotificacionMasiva              │
│  └── accesos_router       └── ...                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                          ▲
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                CAPA DE APLICACIÓN                              │
│           (Orquestación y Coordinación)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Services                                                       │
│  ├── QRService                                                 │
│  │   ├── generar_qr_residente()                               │
│  │   └── generar_qr_visita()                                  │
│  │                                                             │
│  ├── NotificacionService                                       │
│  │   ├── enviar_notificacion_masiva_residentes()             │
│  │   ├── enviar_notificacion_individual()                    │
│  │   └── ...                                                 │
│  │                                                             │
│  └── CuentaService                                             │
│      ├── bloquear_cuenta_y_familia()                          │
│      └── desbloquear_cuenta_y_familia()                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                          ▲
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CAPA DE DOMINIO                              │
│             (Lógica de Negocio Pura)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Entities                          Use Cases                   │
│  ├── Persona                       ├── GenerarQRUseCase       │
│  ├── Vivienda                      ├── ValidarQRUseCase       │
│  ├── Residente                     ├── CrearCuentaUseCase     │
│  ├── Miembro                       ├── BloqueoCuentaUseCase   │
│  ├── QR                            └── ...                    │
│  ├── Acceso                                                    │
│  └── Notificacion                                              │
│                                                                 │
│  Lógica de negocio:                                            │
│  - QR.es_vigente()                                            │
│  - Persona.puede_acceder()                                    │
│  - Residente.es_activo()                                      │
│  - Validaciones transversales (CV-01 a CV-32)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                          ▲
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              CAPA DE INFRAESTRUCTURA                           │
│           (Adaptadores y Detalles Técnicos)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Base de Datos          │  Sincronización Real-Time          │
│  ├── models.py          │  ├── firestore/                    │
│  │   ├── Persona        │  │   └── client.py                 │
│  │   ├── Vivienda       │  │       └── get_firestore_client()│
│  │   ├── QR             │  │                                 │
│  │   ├── Cuenta         │  │  Notificaciones                 │
│  │   └── ...            │  │  ├── notifications/             │
│  │                      │  │  │   └── fcm_client.py          │
│  ├── database.py        │  │  │       ├── enviar_push()     │
│  │   ├── SessionLocal   │  │  │       ├── multicast()       │
│  │   └── get_db()       │  │  │       └── topico()          │
│  │                      │  │                                 │
│  └── Alembic            │  Seguridad                         │
│      └── Migraciones    │  ├── security/                     │
│                         │  │   └── auth.py                   │
│                         │  │       ├── Firebase Auth (MVP)   │
│                         │  │       ├── JWT Handler (Plan)    │
│                         │  │       └── obtener_usuario()     │
│                         │  │                                 │
│                         │  Servicios Externos               │
│                         │  ├── Biometría                    │
│                         │  └── (Consumir API externa)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


FLUJO DE SOLICITUD (Request Flow)
==================================

1. Cliente HTTP
   │
   ├─► POST /api/v1/qr/generar-propio
   │
   ▼
2. Router (qr_router.py)
   │
   ├─► Validar header Authorization
   │
   ├─► Llamar a Service
   │
   ▼
3. Service (QRService)
   │
   ├─► Orquestar lógica de negocio
   │
   ├─► Generar token único
   │
   ├─► Persisten en PostgreSQL (via SQLAlchemy)
   │
   ├─► Sincronizar en Firestore
   │
   ├─► Registrar en bitácora
   │
   ├─► Retornar resultado
   │
   ▼
4. Response (QRResponse)
   │
   └─► JSON al cliente


FLUJO DE AUTENTICACIÓN (Authentication Flow)
==============================================

MVP: Firebase Auth
───────────────────
Cliente envía idToken en header Authorization

   │
   ├─► HTTPBearer (FastAPI)
   │
   ├─► FirebaseAuthenticator.verificar_token_firebase()
   │
   ├─► Firebase Admin SDK valida token
   │
   └─► Retorna datos del usuario decodificados


Plan de Migración: JWT
──────────────────────
En el futuro, cambiar a JWT con roles

   │
   ├─► HTTPBearer (FastAPI)
   │
   ├─► JWTHandler.verificar_token()
   │
   ├─► Validar firma y expiración
   │
   └─► Retorna claims del token (usuario, rol, permisos)


PERSISTENCIA DE DATOS
=====================

PostgreSQL (Fuente de Verdad)
────────────────────────────
- Datos normalizados
- Transacciones ACID
- Auditoría (bitacora, evento_cuenta)
- Respaldos y recuperación

Firestore (Sincronización Real-Time)
─────────────────────────────────────
- Documentos desnormalizados
- Replicación de datos críticos (QR, accesos)
- Listeners para cambios en tiempo real
- Optimizado para consultas frecuentes


TABLA DE ROLES Y PERMISOS (Preparado para JWT)
================================================

ADMINISTRADOR        RESIDENTE          MIEMBRO
- RF-C05 a RF-C09   - RF-C01, RF-C04   - RF-C02, RF-C03
- RF-P01 a RF-P05   - RF-Q01, RF-Q02   - RF-Q01, RF-Q02
- RF-R01 a RF-R06   - Generar QR       - Generar QR
- RF-N01 a RF-N04   - Autorizar miembro- Acceso básico
- Notif. masivas    - Notif. individual


VALIDACIONES TRANSVERSALES (CV-01 a CV-32)
===========================================

Validadas en Routers/Services:
- CV-01: Identificación ecuatoriana
- CV-03: Nombres/apellidos no vacíos
- CV-05: Correo electrónico válido
- CV-06: Celular ecuatoriano 09XXXXXXXX
- CV-10: Identificación existente
- CV-13: Estado activo
- CV-14: Estado inactivo
- CV-19: Reconocimiento facial exitoso
- CV-20: Reconocimiento facial fallido
- CV-21: Contraseñas coinciden
- CV-22: Contraseñas no coinciden
- ... (todos los criterios mapeados)


PRÓXIMOS ENDPOINTS A IMPLEMENTAR
=================================

Propietarios (RF-P01 a RF-P05)
├── POST /propietarios
├── POST /propietarios/{id}/conyuge
├── PUT /propietarios/{id}
├── POST /propietarios/{id}/baja
└── POST /propietarios/cambio

Accesos (RF-AQ01 a RF-AQ07)
├── POST /accesos/validar
├── POST /accesos/visita/sin-qr
├── POST /accesos/visita/manual
├── POST /accesos/residente/auto-ingreso
└── POST /accesos/salida-visitante

Biometría (RF-OB01, RF-OB02)
├── POST /biometria/validar-rostro
└── POST /biometria/ocr-documento

Miembros (RF-R02, RF-R04, RF-R06)
├── POST /miembros
├── POST /miembros/{id}/desactivar
└── POST /miembros/{id}/reactivar
"""

# Este es un archivo de documentación en formato de docstring
# Se puede usar como referencia durante el desarrollo
