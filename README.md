# API Control de Acceso Residencial

Backend completo en **Python 3.12 con FastAPI** para un sistema de **control de acceso residencial** utilizando arquitectura hexagonal.

## 📋 Características principales

- **Arquitectura Hexagonal**: Separación clara entre dominio, aplicación e infraestructura
- **FastAPI**: Framework moderno y rápido para APIs REST
- **PostgreSQL**: Base de datos relacional como fuente de verdad
- **Firestore**: Sincronización en tiempo real
- **Firebase Auth**: Validación de tokens (MVP)
- **JWT**: Plan preparado para migración futura
- **FCM**: Notificaciones push
- **SQLAlchemy + Alembic**: ORM y migraciones de base de datos

## 🏗️ Estructura del proyecto

```
backend-api/
│── app/
│   ├── main.py                          # Punto de entrada FastAPI
│   ├── config.py                        # Configuración centralizada
│   │
│   ├── domain/                          # Núcleo de negocio
│   │   ├── entities/models.py           # Entidades del dominio
│   │   └── use_cases/                   # Casos de uso
│   │       ├── qr_use_cases.py          # Generación y validación de QR
│   │       └── ...
│   │
│   ├── application/                     # Capa de aplicación
│   │   ├── services/                    # Servicios de orquestación
│   │   └── dto/                         # Data Transfer Objects
│   │
│   ├── infrastructure/                  # Adaptadores externos
│   │   ├── db/
│   │   │   ├── models.py                # SQLAlchemy ORM
│   │   │   ├── database.py              # Configuración DB
│   │   │   └── __init__.py
│   │   ├── firestore/client.py          # Cliente Firestore
│   │   ├── notifications/fcm_client.py  # Cliente FCM
│   │   └── security/auth.py             # Firebase Auth + JWT
│   │
│   └── interfaces/                      # Puertos de entrada
│       ├── routers/
│       │   ├── qr_router.py             # Endpoints QR
│       │   ├── cuentas_router.py        # Endpoints cuentas
│       │   ├── residentes_router.py     # Endpoints residentes
│       │   └── ...
│       └── schemas/                     # Pydantic schemas
│
├── alembic/                             # Migraciones de BD
│   ├── versions/
│   ├── env.py
│   ├── script.py.mako
│   └── alembic.ini
│
├── requirements.txt                     # Dependencias
├── .env.example                         # Variables de entorno (ejemplo)
├── .gitignore                           # Git ignore
└── README.md                            # Este archivo
```

## 🚀 Instalación y configuración

### 1. Requisitos previos

- Python 3.12+
- PostgreSQL 13+
- Cuenta Firebase (para servicios cloud)
- Git

### 2. Clonar repositorio

```bash
git clone <url-repositorio>
cd backend-api
```

### 3. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con tus valores:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/residencial_db

# Firebase
FIREBASE_PROJECT_ID=tu-proyecto
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_API_KEY=tu-api-key

# FCM
FCM_SENDER_ID=tu-sender-id

# JWT
JWT_SECRET_KEY=cambiar-en-produccion

# Biometría
BIOMETRIA_SERVICE_URL=http://localhost:8001
```

### 6. Descargar credenciales Firebase

1. Ir a [Firebase Console](https://console.firebase.google.com)
2. Seleccionar tu proyecto
3. Ir a Configuración del proyecto → Cuentas de servicio
4. Generar nueva clave privada (JSON)
5. Guardar como `firebase-credentials.json` en la raíz del proyecto

### 7. Configurar base de datos

```bash
# Crear base de datos
createdb residencial_db

# Ejecutar migraciones Alembic
alembic upgrade head
```

### 8. Ejecutar servidor

```bash
python -m app.main

# O con uvicorn directamente
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`

- Documentación interactiva (Swagger): `http://localhost:8000/docs`
- Documentación alternativa (ReDoc): `http://localhost:8000/redoc`

## 📚 Endpoints principales

### Cuentas

- `POST /api/v1/cuentas/residente` - Crear cuenta residente (RF-C01)
- `POST /api/v1/cuentas/{cuenta_id}/bloquear` - Bloquear cuenta (RF-C07)
- `POST /api/v1/cuentas/{cuenta_id}/desbloquear` - Desbloquear cuenta (RF-C08)
- `DELETE /api/v1/cuentas/{cuenta_id}` - Eliminar cuenta (RF-C09)

### QR

- `POST /api/v1/qr/generar-propio` - Generar QR propio (RF-Q01)
- `POST /api/v1/qr/generar-visita` - Generar QR para visita (RF-Q02)
- `GET /api/v1/qr/{qr_id}` - Obtener información de QR

### Residentes

- `POST /api/v1/residentes` - Registrar residente (RF-R01)
- `POST /api/v1/residentes/{residente_id}/desactivar` - Desactivar (RF-R03)
- `POST /api/v1/residentes/{residente_id}/reactivar` - Reactivar (RF-R05)

## 🔐 Seguridad

### MVP: Firebase Auth

En la fase actual, se utiliza **Firebase Authentication**:

```python
# Obtener usuario desde token Firebase
usuario = await obtener_usuario_firebase(credential)
```

El token debe incluirse en el header `Authorization`:

```bash
curl -H "Authorization: Bearer {idToken}" http://localhost:8000/api/v1/qr/generar-propio
```

### Plan de migración a JWT

Se ha preparado toda la infraestructura para migrar a **JWT con roles** en el futuro:

```python
# Función preparada para migración futura
async def obtener_usuario_jwt(credential: HTTPAuthCredential = Depends(security)) -> Dict:
    return JWTHandler.verificar_token(credential.credentials)
```

Para migrar en el futuro, simplemente cambiar:

```python
# En obtener_usuario_actual() dentro de auth.py
async def obtener_usuario_actual(credential: HTTPAuthCredential = Depends(security)) -> Dict:
    # Cambiar de:
    return FirebaseAuthenticator.verificar_token_firebase(credential)
    # A:
    return await obtener_usuario_jwt(credential)
```

## 📊 Base de datos

### Tablas principales

- `persona` - Datos de personas
- `vivienda` - Información de viviendas
- `propietario_vivienda` - Propietarios de viviendas
- `residente_vivienda` - Residentes de viviendas
- `miembro_vivienda` - Miembros de familia
- `cuenta` - Cuentas de usuario
- `qr` - Códigos QR
- `acceso` - Registros de acceso
- `notificacion` - Notificaciones
- `bitacora` - Auditoría

### Alembic: Crear migraciones

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripcion del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

## 🔥 Firestore: Sincronización en tiempo real

El cliente de Firestore está preparado en `app/infrastructure/firestore/client.py`:

```python
from app.infrastructure.firestore.client import get_firestore_client

firestore = get_firestore_client()

# Crear documento
firestore.crear_documento("qr", "qr-123", {
    "token": "abc123",
    "vivienda_id": 1,
    "estado": "vigente"
})

# Actualizar documento
firestore.actualizar_documento("qr", "qr-123", {"estado": "usado"})

# Obtener documento
qr = firestore.obtener_documento("qr", "qr-123")
```

## 📱 FCM: Notificaciones push

Cliente de FCM disponible en `app/infrastructure/notifications/fcm_client.py`:

```python
from app.infrastructure.notifications.fcm_client import get_fcm_client

fcm = get_fcm_client()

# Enviar a dispositivo específico
message_id = fcm.enviar_notificacion_push(
    token="fcm-token",
    titulo="Acceso autorizado",
    cuerpo="Bienvenido a la urbanización",
    datos={"tipo": "acceso"}
)

# Enviar a múltiples dispositivos
response = fcm.enviar_notificacion_multicast(
    tokens=["token1", "token2"],
    titulo="Notificación masiva",
    cuerpo="Mensaje para residentes"
)

# Enviar a tópico
message_id = fcm.enviar_notificacion_topico(
    topico="residentes",
    titulo="Alerta de seguridad",
    cuerpo="Se detectó actividad sospechosa"
)
```

## 🧪 Testing

Ejecutar pruebas:

```bash
pytest

# Con cobertura
pytest --cov=app
```

## 📖 Documentación de requerimientos

Todos los requerimientos funcionales están implementados según la especificación SRS:

- **RF-C01 a RF-C09**: Gestión de cuentas
- **RF-P01 a RF-P05**: Gestión de propietarios
- **RF-R01 a RF-R06**: Gestión de residentes
- **RF-Q01, RF-Q02**: Generación de QR
- **RF-N01 a RF-N04**: Notificaciones
- **RF-OB01, RF-OB02**: Biometría (consumir servicio externo)

Ver `Requerimientos_completos.md` para detalles completos.

## 🌐 Arquitectura hexagonal

```
┌─────────────────────────────────────────┐
│           INTERFACES (HTTP)             │
│    Routers FastAPI + Schemas Pydantic   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         APPLICATION LAYER               │
│  Services + DTOs + Orchestration        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           DOMAIN LAYER                  │
│  Entities + Use Cases + Business Logic  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        INFRASTRUCTURE LAYER             │
│  DB + Firestore + FCM + Security        │
└─────────────────────────────────────────┘
```

## 🚦 Próximos pasos

- [ ] Completar routers para propietarios (RF-P01 a RF-P05)
- [ ] Implementar gestión de accesos (RF-AQ01 a RF-AQ07)
- [ ] Integrar servicio de biometría externo
- [ ] Agregar validaciones comunes (CV-01 a CV-32)
- [ ] Implementar repository pattern para mejor testabilidad
- [ ] Agregar más endpoints de notificaciones
- [ ] Crear tests unitarios e integración
- [ ] Documentación OpenAPI completa
- [ ] Migración a JWT

## 📝 Notas de desarrollo

### Estructure el código siguiendo hexagonal architecture
- `domain/`: Lógica de negocio pura, sin dependencias externas
- `application/`: Orquestación entre capas
- `infrastructure/`: Detalles técnicos (DB, APIs externas)
- `interfaces/`: Puertos de entrada (routers HTTP)

### Validaciones
Se implementan validaciones según criterios comunes (CV-01 a CV-32) en los endpoints.

### Auditoría
Todos los cambios se registran en la tabla `bitacora` y en `evento_cuenta` para cuentas.

## 📞 Soporte y contacto

Para dudas o problemas, contactar al equipo de desarrollo.

---

**Versión:** v1.0  
**Última actualización:** Enero 2026  
**Estado:** En desarrollo
