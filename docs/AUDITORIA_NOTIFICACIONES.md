# AUDITORÍA COMPLETA - Sistema de Notificaciones Push (Guardin)

**Fecha:** 2026-07-07  
**Proyecto:** Guardin Backend API  
**Framework:** FastAPI 0.104.1  
**Base de datos:** PostgreSQL (vía SQLAlchemy 2.0.23 + psycopg2-binary)  
**Autenticación:** Firebase Auth (firebase-admin 6.4.0)

---

## SECCIÓN 1: ESTRUCTURA DEL PROYECTO

### 1.1 Árbol de directorios

```
control_residentes_backend_api/
├── app/
│   ├── __init__.py
│   ├── main.py                          # Punto de entrada FastAPI
│   ├── config.py                        # Settings con pydantic-settings
│   ├── application/
│   │   ├── __init__.py
│   │   ├── dto/
│   │   │   └── __init__.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── servicios.py             # QRService, NotificacionService, CuentaService
│   │       └── accesos_service.py       # AccesosService (estadísticas)
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── models.py               # Dataclasses de dominio (Persona, QR, Acceso, Notificacion)
│   │   └── use_cases/
│   │       ├── __init__.py
│   │       └── qr_use_cases.py          # Use cases abstractos QR (ABC)
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py              # Engine, SessionLocal, get_db, Base
│   │   │   └── models.py                # 17 modelos SQLAlchemy (575 líneas)
│   │   ├── firestore/
│   │   │   ├── __init__.py
│   │   │   └── client.py                # FirestoreClient (singleton)
│   │   ├── notifications/
│   │   │   ├── __init__.py
│   │   │   └── fcm_client.py            # FCMClient (Firebase Cloud Messaging)
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                  # FirebaseAuthenticator + JWTHandler
│   │   │   └── firebase_auth.py         # obtener_usuario_autenticado (deprecated)
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── time_utils.py            # Zona horaria configurable
│   └── interfaces/
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── cuentas_router.py        # /api/v1/cuentas
│       │   ├── qr_router.py             # /api/v1/qr
│       │   ├── residentes_router.py     # /api/v1/residentes
│       │   ├── propietarios_router.py   # /api/v1/propietarios
│       │   ├── miembros_router.py       # /api/v1/miembros
│       │   └── accesos_router.py        # /api/v1/accesos
│       └── schemas/
│           ├── __init__.py
│           └── schemas.py               # Schemas Pydantic (396 líneas)
├── requirements.txt
├── pyproject.toml
└── docs/
    └── AUDITORIA_NOTIFICACIONES.md      # Este reporte
```

### 1.2 Archivo principal: `app/main.py`

- Framework: ✅ **FastAPI** (confirmado)
- Middlewares: CORS configurado
- Routers registrados: 6 routers (`app/interfaces/routers/__init__.py:2-4`)
- Las tablas se crean con `Base.metadata.create_all(bind=engine)` en startup (línea 11)
- ❌ **No usa Alembic** para migraciones (aunque está instalado)
- Documentación: `/docs` (Swagger), `/redoc`

### 1.3 Archivos de configuración: `app/config.py`

- Usa `pydantic-settings` con clase `Settings`
- Variables de entorno cargadas de `.env` (no encontrado en repo)
- Configuraciones relevantes para notificaciones:
  - ✅ `FIREBASE_PROJECT_ID` - Configurado
  - ✅ `FIREBASE_CREDENTIALS_PATH` - Configurado
  - ✅ `FCM_SENDER_ID` - Configurado
  - ✅ Variables de paginación configuradas
  - ❌ No hay variable para colección de tokens FCM en Firestore
  - ❌ No hay .env.example en el repositorio

---

## SECCIÓN 2: ROUTERS Y ENDPOINTS EXISTENTES

### 2.1 Resumen de Routers

| Router | Archivo | Prefijo | Tag | # Endpoints |
|--------|---------|---------|-----|-------------|
| Cuentas | `cuentas_router.py` | `/api/v1/cuentas` | Cuentas | 9 |
| QR | `qr_router.py` | `/api/v1/qr` | QR | 5 |
| Residentes | `residentes_router.py` | `/api/v1/residentes` | Residentes | 5 |
| Propietarios | `propietarios_router.py` | `/api/v1/propietarios` | Propietarios | 6 |
| Miembros | `miembros_router.py` | `/api/v1/miembros` | Miembros de Familia | 5 |
| Accesos | `accesos_router.py` | `/api/v1/accesos` | Accesos | 2 |
| **Notificaciones** | ❌ **NO EXISTE** | - | - | **0** |

### 2.2 Detalle de endpoints por router

**Cuentas** (`cuentas_router.py:10`):
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/residente/firebase` | Crear cuenta residente con Firebase UID |
| POST | `/miembro/firebase` | Crear cuenta miembro con Firebase UID |
| POST | `/{cuenta_id}/bloquear` | Bloquear cuenta (+ cascada) |
| POST | `/{cuenta_id}/desbloquear` | Desbloquear cuenta (+ cascada) |
| DELETE | `/{cuenta_id}` | Soft delete cuenta |
| GET | `/perfil/{firebase_uid}` | Obtener perfil completo |
| GET | `/usuario/por-correo/{correo}` | Buscar usuario por correo |
| GET | `/vivienda/{manzana}/{villa}/usuarios` | Usuarios de vivienda |
| GET | `/prospecto/residente/{identificacion}` | Validar prospecto residente |
| GET | `/prospecto/miembro/{identificacion}` | Validar prospecto miembro |

**QR** (`qr_router.py:15`):
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/generar-propio` | QR para residente |
| POST | `/generar-visita` | QR para visita |
| GET | `/{qr_id}` | Obtener QR |
| GET | `/cuenta/generados` | Listar QRs (paginado) |
| GET | `/visitantes/{persona_id}` | Visitantes de vivienda |

**Accesos** (`accesos_router.py:10`):
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/vivienda/{vivienda_id}` | Accesos por vivienda |
| GET | `/admin/estadisticas` | Estadísticas admin |

### 2.3 Dependencias de autenticación

- ❌ **Ningún router usa `Depends(obtener_usuario_actual)` ni `Depends(security)`**
- Los routers reciben `usuario_id` como query param o en el body (no autenticado)
- Solo `obtener_usuario_autenticado` en `firebase_auth.py` está diseñado como dependency pero no se usa
- El router de cuentas tiene su propio `obtener_perfil_usuario` que busca por Firebase UID (sin middleware)

### 2.4 Estructura de un router típico

Patrón observado en todos los routers:
- `APIRouter` con `prefix` y `tags`
- Schemas definidos inline o importados de `app.interfaces.schemas`
- Sesión DB inyectada con `db: Session = Depends(get_db)`
- Manejo de errores: try/except con `HTTPException` raising y `db.rollback()`
- Respuestas: `dict` directamente (no usan response_model tipado)
- Sin capa de repositorio intermedia; queries SQLAlchemy directas

---

## SECCIÓN 3: MODELOS DE BASE DE DATOS (SQLAlchemy)

### 3.1 Conexión: `app/infrastructure/db/database.py`

```
Engine: PostgreSQL (psycopg2-binary)
Session: sessionmaker con autocommit=False, autoflush=False
Dependency: get_db() -> yield db
Base: declarative_base() (definida en dos lugares: database.py y models.py)
```

⚠️ **Problema:** `Base` se define en `database.py:17` y en `models.py:11`. Los modelos usan la Base de `models.py`. Ambas son instancias separadas; esto puede causar problemas con migraciones.

### 3.2 Modelos existentes (17 tablas)

| # | Modelo | Tabla | PK | Relaciones clave |
|---|--------|-------|----|-----------------|
| 1 | `Vivienda` | `vivienda` | `vivienda_pk` | propietarios, residentes, miembros, visitas, accesos, qrs |
| 2 | `Persona` | `persona` | `persona_pk` | fotos, propietarios, residentes, miembros, cuentas, guardias, vehiculos, admin |
| 3 | `PersonaFoto` | `persona_foto` | `foto_pk` | persona |
| 4 | `PropietarioVivienda` | `propietario_vivienda` | `propietario_vivienda_pk` | vivienda, persona |
| 5 | `ResidenteVivienda` | `residente_vivienda` | `residente_vivienda_pk` | vivienda, persona |
| 6 | `MiembroVivienda` | `miembro_vivienda` | `miembro_vivienda_pk` | vivienda, persona_residente, persona_miembro |
| 7 | `Cuenta` | `cuenta` | `cuenta_pk` | persona, eventos, qrs |
| 8 | `Admin` | `admin` | `admin_pk` | persona |
| 9 | `Guardia` | `guardia` | `guardia_pk` | persona |
| 10 | `EventoCuenta` | `evento_cuenta` | `evento_cuenta_pk` | cuenta |
| 11 | `Vehiculo` | `vehiculo` | `vehiculo_pk` | persona |
| 12 | `Visita` | `visita` | `visita_pk` | vivienda |
| 13 | `Acceso` | `acceso` | `acceso_pk` | vivienda |
| 14 | `AutorizacionTelefonica` | `autorizacion_telefonica` | `autorizacion_tel_pk` | - |
| 15 | `AutorizacionCodigo` | `autorizacion_codigo` | `autorizacion_codigo_pk` | - |
| 16 | `QR` | `qr` | `qr_pk` | cuenta, vivienda |
| 17 | **`Notificacion`** | `notificacion` | `notificacion_pk` | destinos |
| 18 | **`NotificacionDestino`** | `notificacion_destino` | `notificacion_destino_pk` | notificacion |
| 19 | **`Bitacora`** | `bitacora` | `bitacora_pk` | - |

### 3.3 Modelos de Notificación (detalle)

**`Notificacion`** (`models.py:511-540`):
```python
notificacion_pk: Integer (PK)
tipo: String(30)          # CHECK constraint con 15 tipos
mensaje: Text
persona_emisor_fk: Integer (FK -> persona)  # Nullable
eliminado: Boolean
fecha_creado: DateTime
usuario_creado: String(20)
# ... campos de auditoría estándar
destinos: relationship -> NotificacionDestino
```

Tipos de notificación válidos (CHECK constraint):
```
solicitud_autorizacion, ingreso_autorizado, ingreso_rechazado,
intento_fallido, qr_generado, qr_expirado,
codigo_generado, codigo_usado, alerta_seguridad,
cuenta_bloqueada, acceso_manual,
alta_usuario, baja_usuario,
cambio_estado, actualizacion_datos
```

**`NotificacionDestino`** (`models.py:543-560`):
```python
notificacion_destino_pk: Integer (PK)
notificacion_envio_fk: Integer (FK -> notificacion)
persona_receptor_fk: Integer (FK -> persona)
entregada: Boolean (default=False)    # ✅ Para tracking de entrega
hora_entregado: DateTime              # ✅ Para tracking de entrega
error: Text                           # ✅ Para tracking de errores
# ... campos de auditoría estándar
```

✅ **Los modelos de notificación ya existen y están bien diseñados.**

### 3.4 Migraciones

- ❌ **No se encontró `alembic/` ni `migrations/`**
- ❌ No hay `alembic.ini`
- Alembic está instalado (`requirements.txt:1`) pero no configurado
- Las tablas se crean con `Base.metadata.create_all()` en `main.py:11`

---

## SECCIÓN 4: ESQUEMAS Pydantic

### 4.1 Archivo: `app/interfaces/schemas/schemas.py` (396 líneas)

**Schemas de notificación existentes** (líneas 275-309):
```
✅ NotificacionMasivaResidentes   (mensaje, tipo, usuario_emisor)
✅ NotificacionMasivaPropietarios (mensaje, tipo, usuario_emisor)
✅ NotificacionIndividualResidente (persona_id, mensaje, tipo, usuario_emisor)
✅ NotificacionIndividualPropietario (persona_id, mensaje, tipo, usuario_emisor)
✅ NotificacionResponse           (id, tipo, mensaje, fecha_creado)
```

**Schemas de autenticación existentes** (líneas 312-327):
```
✅ LoginRequest           (username, password)
✅ LoginResponse          (access_token, token_type, usuario_id, username)
✅ FirebaseLoginRequest   (id_token)
```

### 4.2 Schemas FALTANTES para notificaciones

```
❌ TokenFCMRegisterRequest    (token_fcm: str, dispositivo: str)
❌ TokenFCMUpdateRequest      (token_fcm: str)
❌ NotificacionPaginadaResponse
❌ NotificacionConDestinosResponse
❌ NotificacionMarcaLeidaRequest
❌ NotificacionConteoResponse  (total, no_leidas)
❌ TopicoSubscribeRequest     (topico: str)
❌ TopicoUnsubscribeRequest   (topico: str)
```

---

## SECCIÓN 5: SERVICIOS Y LÓGICA DE NEGOCIO

### 5.1 Servicios existentes

**`app/application/services/servicios.py`:**
```
✅ QRService              - Genera QR + sincroniza con Firestore
✅ NotificacionService    - Envía notificaciones masivas/individuales (PARCIAL)
✅ CuentaService          - Bloqueo/desbloqueo (TODO/stub)
```

**`app/application/services/accesos_service.py`:**
```
✅ AccesosService         - Consulta accesos + estadísticas admin
```

### 5.2 NotificacionService - Estado actual (parcial)

`servicios.py:80-200`:
- ✅ `enviar_notificacion_masiva_residentes()` - Crea registro en BD + registra destinos
- ✅ `enviar_notificacion_individual()` - Crea registro + destino
- ❌ `tokens = []  # Placeholder` (línea 117) - Los tokens FCM no se obtienen
- ❌ La llamada a FCM está comentada (línea 188)
- ❌ No hay tabla/modelo para almacenar tokens FCM de dispositivos
- ❌ No hay método para marcar notificación como leída

### 5.3 FCMClient - Estado actual

**`app/infrastructure/notifications/fcm_client.py`** (154 líneas):
```
✅ enviar_notificacion_push(token, titulo, cuerpo, datos)
✅ enviar_notificacion_multicast(tokens, titulo, cuerpo, datos)
✅ suscribir_a_topico(tokens, topico)
✅ enviar_notificacion_topico(topico, titulo, cuerpo, datos)
```

El cliente FCM está completamente implementado y listo para usar.

### 5.4 FirestoreClient - Estado actual

**`app/infrastructure/firestore/client.py`** (104 líneas):
```
✅ Singleton pattern
✅ crear_documento(coleccion, doc_id, datos)
✅ actualizar_documento(coleccion, doc_id, datos)
✅ obtener_documento(coleccion, doc_id)
✅ eliminar_documento(coleccion, doc_id)
✅ obtener_coleccion(coleccion)
```

⚠️ `FirestoreClient.__init__` llama a `firebase_admin.initialize_app()` sin verificar si ya está inicializado. Si FCMClient también lo hace, habrá conflicto.

### 5.5 Repositorios

- ❌ **No existe capa de repositorio** (`repositories/`, `dal/`)
- Las queries se hacen directamente en routers y servicios con `db.query()`

---

## SECCIÓN 6: AUTENTICACIÓN Y AUTORIZACIÓN

### 6.1 Mecanismo principal

**Archivo:** `app/infrastructure/security/auth.py` (137 líneas)

Clase `FirebaseAuthenticator`:
```python
# auth.py:18-40
verificar_token_firebase(credential: HTTPAuthCredential) -> Dict
# Usa firebase_admin.auth.verify_id_token()
# Lanza HTTPException 401 si es inválido
```

Dependencias disponibles:
```python
# auth.py:43-48
obtener_usuario_firebase(credential) -> Dict  # Solo Firebase

# auth.py:117-126
obtener_usuario_jwt(credential) -> Dict       # Solo JWT (migración futura)

# auth.py:130-137
obtener_usuario_actual(credential) -> Dict    # Actualmente usa Firebase
```

**Archivo:** `app/infrastructure/security/firebase_auth.py` (136 líneas)

Contiene una versión alternativa (deprecated/simulación):
```python
# firebase_auth.py:46-103
obtener_usuario_autenticado(authorization, db) -> dict
# Busca Cuenta por firebase_uid en BD
# Retorna: {firebase_uid, cuenta_id, persona_id, nombres, email, estado}
```

### 6.2 Cómo se usa en routers

- ❌ **Ningún router actual usa dependencias de autenticación**
- Los routers reciben `usuario_id` como query parameter sin validar
- `cuentas_router.py:29` recibe `request: CuentaFirebaseCreate` sin auth
- Es necesario agregar `usuario: dict = Depends(obtener_usuario_actual)` a los routers

### 6.3 Roles y permisos

- ❌ No hay sistema de roles implementado como dependencia reutilizable
- El rol se determina en cada endpoint verificando tablas (ResidenteVivienda, Admin, etc.)
- `cuentas_router.py:526-596` (`obtener_perfil_usuario`) tiene lógica de determinación de rol inline:
  - Verifica `ResidenteVivienda` → "residente"
  - Verifica `PropietarioVivienda` → "residente"
  - Verifica `MiembroVivienda` → "miembro_familia"
  - Verifica `Admin` → "admin"

---

## SECCIÓN 7: DEPENDENCIAS EXTERNAS

### 7.1 requirements.txt completo

Paquetes clave para notificaciones:
```
✅ firebase-admin==6.4.0           # Firebase Admin SDK
✅ google-cloud-firestore==2.14.0  # Firestore client
✅ google-cloud-storage==2.14.0    # Cloud Storage (no usado aún)
✅ fastapi==0.104.1
✅ sqlalchemy==2.0.23
✅ pydantic==2.5.0
✅ pydantic-settings==2.1.0
✅ psycopg2-binary==2.9.9
✅ python-jose==3.3.0              # JWT
✅ passlib==1.7.4
✅ bcrypt==5.0.0
✅ alembic==1.13.0
✅ pytest==7.4.3
```

### 7.2 Dependencias FALTANTES para notificaciones

```
❌ google-cloud-firestore (ya instalado ✅)
❌ firebase-admin (ya instalado ✅)
```

Todas las dependencias necesarias ya están instaladas.

### 7.3 Servicios externos ya integrados

| Servicio | Estado | Archivo |
|----------|--------|---------|
| Firebase Auth | ✅ Configurado | `auth.py`, `firebase_auth.py` |
| Firebase Admin SDK | ✅ Instalado | `firebase-admin==6.4.0` |
| Firestore | ✅ Cliente implementado | `firestore/client.py` |
| FCM | ✅ Cliente implementado | `notifications/fcm_client.py` |
| Google Cloud Storage | ✅ Instalado (no usado) | - |

### 7.4 Variables de entorno

De `app/config.py`:

```python
# Firebase
FIREBASE_PROJECT_ID: str         # "tu-proyecto-firebase"
FIREBASE_CREDENTIALS_PATH: str   # "./firebase-credentials.json"
FIREBASE_API_KEY: str            # "tu-api-key"

# FCM
FCM_SENDER_ID: str               # "tu-sender-id"

# JWT
JWT_SECRET_KEY: str
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRATION_HOURS: int = 24

# Biometría (microservicio externo)
BIOMETRIA_SERVICE_URL: str
BIOMETRIA_SERVICE_KEY: str

# API
API_VERSION: str = "v1"
CORS_ORIGINS: List[str]          # ["http://localhost:3000","http://localhost:8080"]

# Paginación
PAGINATION_DEFAULT_PAGE: int = 1
PAGINATION_DEFAULT_PAGE_SIZE: int = 10
PAGINATION_MAX_PAGE_SIZE: int = 100

# Zona horaria
TIMEZONE: str = "America/Bogota"

# BD
DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
```

❌ **No existe `.env.example` en el repositorio**
❌ No hay variable para colección de tokens en Firestore (ej: `FCM_TOKENS_COLLECTION`)

---

## SECCIÓN 8: UTILIDADES Y HELPERS

### 8.1 Helpers existentes

**`app/infrastructure/utils/time_utils.py`** (202 líneas):
```
✅ obtener_zona_horaria()     → pytz.timezone desde settings
✅ ahora()                    → datetime timezone-aware
✅ ahora_sin_tz()             → datetime naive (usado en toda la app)
✅ ahora_utc()                → datetime UTC
✅ convertir_a_local(dt_utc)  → Conversión UTC→local
✅ convertir_de_local_a_utc() → Conversión local→UTC
✅ fecha_hoy()                → Fecha a medianoche
✅ es_vigente(inicio, fin)    → Verifica vigencia
✅ ha_expirado(fin)           → Verifica expiración
```

### 8.2 Helpers FALTANTES para notificaciones

```
❌ Paginación genérica reutilizable (se hace manual en qr_router.py)
❌ Helper para respuestas HTTP consistentes (success/error wrapper)
❌ Helper para registro en bitácora
❌ Helper para logging estructurado
```

### 8.3 Manejo de errores

- No hay `exceptions.py` ni `error_handlers.py`
- Cada router maneja errores con try/except + HTTPException
- Patrón observado:
  ```python
  except HTTPException:
      raise
  except Exception as e:
      db.rollback()
      raise HTTPException(status_code=500, detail=str(e))
  ```
- ❌ No hay handlers globales de excepciones FastAPI
- ❌ No hay excepciones de dominio personalizadas

---

## SECCIÓN 9: RESPUESTAS HTTP Y FORMATOS

### 9.1 Formato de respuesta estándar

- ❌ **No hay un helper/wrapper para respuestas consistentes**
- Las respuestas varían entre routers:
  - `cuentas_router`: dict con `mensaje`, `id`, etc.
  - `qr_router`: dict con `token`, `estado`, `mensaje`
  - `residentes_router`: dict con `success`, `mensaje`
  - `propietarios_router`: dict con `success`, `mensaje`
  - `accesos_router`: Usa Pydantic `response_model` (más consistente)

### 9.2 Paginación

- ✅ Configurada en settings: page, page_size, max_page_size
- ✅ `QRPaginatedResponse` en `schemas.py:215-225`:
  ```python
  data: list[QRListResponse]
  total: int
  page: int
  page_size: int
  total_pages: int
  has_next: bool
  ```
- ❌ La paginación se implementa manualmente en `qr_router.py:318-418`
- ❌ No hay un helper de paginación reutilizable para otros endpoints

---

## SECCIÓN 10: BITÁCORA Y AUDITORÍA

### 10.1 Tabla Bitacora

**Modelo:** `models.py:563-575`:
```python
class Bitacora(Base):
    __tablename__ = "bitacora"
    bitacora_pk: Integer (PK)
    entidad: String(50)           # Ej: "notificacion", "cuenta"
    entidad_id: String(50)        # ID de la entidad
    operacion: String(20)         # Ej: "CREAR", "ACTUALIZAR", "ELIMINAR"
    persona_actor_fk: Integer (FK -> persona)
    valor_anterior: JSONB
    valor_nuevo: JSONB
    descripcion: Text
    fecha_creado: DateTime
```

### 10.2 Uso de Bitacora

- ❌ **Bitacora NO se usa en ningún endpoint actual**
- El modelo existe pero no hay código que escriba en ella
- Las tablas `cuenta` y `evento_cuenta` llevan su propio registro de eventos

### 10.3 Uso de Notificacion / NotificacionDestino

- ✅ Los modelos existen en `models.py`
- ✅ `NotificacionService` en `servicios.py` crea registros en ambas tablas
- ❌ **No hay router de notificaciones** (no expuesto vía API)
- ❌ Los métodos `enviar_notificacion_masiva_residentes` y `enviar_notificacion_individual` no se llaman desde ningún router

---

## RESUMEN EJECUTIVO

### 1. Qué está listo para integrar notificaciones

| Componente | Estado | Detalle |
|------------|--------|---------|
| Modelos Notificacion/NotificacionDestino | ✅ | `models.py:511-560` |
| Schemas de notificación | ✅ | `schemas.py:275-309` |
| FCM Client (push notifications) | ✅ | `fcm_client.py` - Completo |
| Firestore Client | ✅ | `firestore/client.py` - Completo |
| NotificacionService | ⚠️ Parcial | Lógica BD existe, FCM comentado |
| Firebase Admin SDK | ✅ | `firebase-admin==6.4.0` |
| google-cloud-firestore | ✅ | `firebase-admin==2.14.0` |
| Mecanismo de autenticación | ✅ | `auth.py:130` `obtener_usuario_actual` |
| Settings de Firebase/FCM | ✅ | `config.py` |

### 2. Archivos nuevos que hay que crear

```
✅ Prioridad ALTA:
├── app/interfaces/routers/notificaciones_router.py   # CRUD notificaciones + registro tokens
├── app/application/services/fcm_token_service.py     # Gestión de tokens FCM
├── app/infrastructure/db/models/fcm_token.py         # Modelo TokenFCM (o en Firestore)
├── app/interfaces/schemas/notificaciones_schemas.py  # Schemas adicionales
└── .env.example                                      # Documentar variables de entorno

🔶 Prioridad MEDIA:
├── app/interfaces/routers/bitacora_router.py         # Consulta de bitácora
├── app/application/services/bitacora_service.py      # Servicio de registro en bitácora
└── app/shared/exceptions.py                          # Excepciones de dominio
```

### 3. Archivos existentes que hay que modificar

```
🔴 IMPRESCINDIBLES:
├── app/main.py                                       # Registrar notificaciones_router
├── app/interfaces/routers/__init__.py                # Exportar notificaciones_router
├── app/application/services/servicios.py             # Completar NotificacionService
│   └── Descomentar llamadas FCM (línea 188)
│   └── Implementar obtención de tokens FCM reales (línea 117)

🟡 RECOMENDADOS:
├── app/interfaces/schemas/schemas.py                 # Agregar schemas TokenFCM
├── app/config.py                                     # Agregar FCM_TOKEN_COLLECTION
├── app/infrastructure/db/__init__.py                 # Exportar TokenFCM si es modelo BD
├── app/infrastructure/notifications/__init__.py      # Mejorar exports
└── app/infrastructure/security/auth.py               # Agregar dependency require_role()
```

### 4. Dependencias que hay que agregar

```
✅ Ninguna - todas las dependencias necesarias ya están instaladas:
   - firebase-admin==6.4.0
   - google-cloud-firestore==2.14.0
   - El resto es estándar (FastAPI, SQLAlchemy, Pydantic)
```

### 5. Plan de implementación recomendado

**Fase 1 - Infraestructura (1-2 días):**
1. Crear modelo/colección para tokens FCM (se recomienda Firestore para tiempo real)
2. Implementar `FCMTokenService` para registro/actualización de tokens
3. Crear endpoint `POST /api/v1/notificaciones/token` para registro de dispositivo

**Fase 2 - Core de notificaciones (2-3 días):**
4. Completar `NotificacionService` con llamadas reales a FCM
5. Implementar endpoint `POST /api/v1/notificaciones/enviar` (admin)
6. Implementar endpoint `GET /api/v1/notificaciones` (listar notificaciones del usuario)
7. Implementar endpoint `PATCH /api/v1/notificaciones/{id}/leida`

**Fase 3 - Tiempo real (2-3 días):**
8. Sincronizar estado de lectura en Firestore (colección `notifications/{userId}/items/{notifId}`)
9. Implementar listeners en la app Flutter para actualizaciones en tiempo real
10. Sincronizar notificaciones PostgreSQL ↔ Firestore

**Fase 4 - Notificaciones automáticas (2-3 días):**
11. Disparar notificaciones desde eventos de negocio (QR generado, acceso, etc.)
12. Implementar notificaciones por tópicos FCM ("residentes", "guardias")
13. Auditoría y bitácora de notificaciones

---

### Arquitectura propuesta para notificaciones

```
┌─────────────────────────────────────────────────────────────┐
│                     Flutter App                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ FCM Listener│  │Firestore     │  │ API HTTP Client  │   │
│  │ (background)│  │Listener (RT) │  │ (REST calls)     │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼────────────────┼───────────────────┼──────────────┘
          │                │                   │
          ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Guardin Backend API                      │
│                                                             │
│  ┌──────────────────┐  ┌────────────┐  ┌────────────────┐  │
│  │Notificaciones    │  │FCM Client  │  │Firestore Client│  │
│  │Router + Service  │──│(push send) │──│(read status)   │  │
│  └────────┬─────────┘  └────────────┘  └────────────────┘  │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────────┐                 │
│  │         PostgreSQL                     │                 │
│  │  ┌──────────────┐ ┌──────────────────┐ │                 │
│  │  │ notificacion  │ │notif_destino     │ │                 │
│  │  └──────────────┘ └──────────────────┘ │                 │
│  └────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

- **PostgreSQL**: Fuente de verdad, almacena todas las notificaciones
- **Firestore**: Réplica para estado de lectura en tiempo real y tokens FCM
- **FCM**: Entrega de push notifications a dispositivos
- **Flutter**: Recibe push vía FCM + sincroniza estado lectura vía Firestore listener
```

