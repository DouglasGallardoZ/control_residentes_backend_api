# 📑 Índice de Navegación del Proyecto

Bienvenido al Backend API para Sistema de Control de Acceso Residencial. Este documento te ayudará a navegar por la documentación y código del proyecto.

---

## 🎯 Comienza Aquí

### Para Nuevos Desarrolladores
1. **[QUICKSTART.md](QUICKSTART.md)** ⭐ - Poner el proyecto funcionando en 5 minutos
2. **[README.md](README.md)** - Documentación principal y descripción general
3. **[ARQUITECTURA.md](ARQUITECTURA.md)** - Entender la estructura y patrones

### Para DevOps/SRE
1. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guía completa de deployment
2. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Procesos y estándares
3. **[Makefile](Makefile)** - Comandos disponibles

### Para Gerentes/Stakeholders
1. **[RESUMEN_FINAL.md](RESUMEN_FINAL.md)** - Estado del proyecto y estadísticas
2. **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios y roadmap
3. **[ESTADO_PROYECTO.md](ESTADO_PROYECTO.md)** - Métricas y progreso

---

## 📚 Documentación Completa

### 📖 Guías Principales

| Documento | Propósito | Audiencia | Líneas |
|-----------|-----------|-----------|--------|
| [README.md](README.md) | Documentación principal | Todos | 450+ |
| [QUICKSTART.md](QUICKSTART.md) | Setup rápido (5 min) | Nuevos devs | 150+ |
| [ARQUITECTURA.md](ARQUITECTURA.md) | Patrones y diagramas | Arquitectos/Devs | 300+ |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deploy a producción | DevOps/SRE | 400+ |
| [EJEMPLOS_USO.md](EJEMPLOS_USO.md) | Ejemplos prácticos | Devs | 200+ |
| [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md) | Métricas y estado | PM/Tech Lead | 150+ |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo contribuir | Contribuidores | 300+ |
| [CHANGELOG.md](CHANGELOG.md) | Historial/Roadmap | Todos | 200+ |
| [RESUMEN_FINAL.md](RESUMEN_FINAL.md) | Resumen integral | Todos | 400+ |

### 🔧 Configuración

| Archivo | Propósito |
|---------|-----------|
| [Dockerfile](Dockerfile) | Construcción de imagen Docker |
| [docker-compose.yml](docker-compose.yml) | Servicios desarrollo |
| [docker-compose.prod.yml](docker-compose.prod.yml) | Servicios producción |
| [nginx.conf](nginx.conf) | Configuración del proxy |
| [Makefile](Makefile) | Automatización de tareas |
| [deploy.sh](deploy.sh) | Script de deployment |
| [pyproject.toml](pyproject.toml) | Configuración build/Poetry |
| [setup.cfg](setup.cfg) | Herramientas (Black, isort, etc) |
| [pytest.ini](pytest.ini) | Configuración de tests |
| [.env.example](.env.example) | Template de variables |
| [.gitignore](.gitignore) | Archivos ignorados |
| [.dockerignore](.dockerignore) | Archivos ignorados en Docker |

---

## 💻 Código Fuente

### Estructura Hexagonal

```
app/
├── domain/                    # 🎯 Lógica de negocio pura
│   ├── entities/
│   │   └── models.py         # 6 entidades: Persona, Vivienda, QR, etc.
│   └── use_cases/
│       └── qr_use_cases.py   # Casos de uso
│
├── application/               # 🔄 Orquestación de lógica
│   └── services/
│       └── servicios.py      # 3 servicios: QR, Notificación, Cuenta
│
├── infrastructure/            # 🔌 Implementaciones técnicas
│   ├── db/
│   │   ├── models.py         # 18 modelos SQLAlchemy
│   │   └── database.py       # Setup de BD
│   ├── firestore/
│   │   └── client.py         # Cliente Firestore
│   ├── notifications/
│   │   └── fcm_client.py     # Cliente FCM
│   └── security/
│       └── auth.py           # Autenticación
│
└── interfaces/                # 📡 API HTTP
    ├── schemas/
    │   └── schemas.py        # 40+ Pydantic schemas
    └── routers/
        ├── qr_router.py      # 3 endpoints QR
        ├── cuentas_router.py # 4 endpoints Cuentas
        └── residentes_router.py # 3 endpoints Residentes

config.py                       # ⚙️ Configuración centralizada
main.py                         # 🚀 Punto de entrada FastAPI
```

### Mapeo de Archivos por Funcionalidad

#### Gestión de QR (RF-Q01, Q02)
- **Lógica**: `app/domain/use_cases/qr_use_cases.py`
- **Servicios**: `app/application/services/servicios.py::QRService`
- **API**: `app/interfaces/routers/qr_router.py`
- **Schemas**: `app/interfaces/schemas/schemas.py::QR*`
- **BD**: `app/infrastructure/db/models.py::QR`

#### Gestión de Cuentas (RF-C01, C07-C09)
- **Lógica**: `app/domain/entities/models.py`
- **Servicios**: `app/application/services/servicios.py::CuentaService`
- **API**: `app/interfaces/routers/cuentas_router.py`
- **Schemas**: `app/interfaces/schemas/schemas.py::Cuenta*`
- **BD**: `app/infrastructure/db/models.py::Persona, EventoCuenta`

#### Gestión de Residentes (RF-R01, R03, R05)
- **Lógica**: `app/domain/entities/models.py`
- **API**: `app/interfaces/routers/residentes_router.py`
- **Schemas**: `app/interfaces/schemas/schemas.py::Residente*`
- **BD**: `app/infrastructure/db/models.py::ResidenteVivienda`

---

## 🗂️ Guía Rápida de Archivos

### Entender la Base de Datos
1. **Esquema SQL**: [esquema.sql](esquema.sql) - SQL raw del esquema
2. **ORM Models**: [app/infrastructure/db/models.py](app/infrastructure/db/models.py)
3. **Documentación**: [ARQUITECTURA.md](ARQUITECTURA.md) - Diagramas ER

### Entender la API
1. **Routers**: `app/interfaces/routers/*.py` - Endpoints
2. **Schemas**: [app/interfaces/schemas/schemas.py](app/interfaces/schemas/schemas.py) - Request/Response
3. **Documentación**: [EJEMPLOS_USO.md](EJEMPLOS_USO.md) - cURL examples

### Entender la Lógica
1. **Domain**: [app/domain/entities/models.py](app/domain/entities/models.py) - Entidades
2. **Use Cases**: [app/domain/use_cases/](app/domain/use_cases/) - Casos de uso
3. **Services**: [app/application/services/](app/application/services/) - Orquestación

### Entender la Infraestructura
1. **Database**: [app/infrastructure/db/](app/infrastructure/db/) - BD
2. **Firebase**: [app/infrastructure/security/auth.py](app/infrastructure/security/auth.py) - Auth
3. **Firestore**: [app/infrastructure/firestore/client.py](app/infrastructure/firestore/client.py) - Real-time
4. **FCM**: [app/infrastructure/notifications/fcm_client.py](app/infrastructure/notifications/fcm_client.py) - Push

---

## 🚀 Tareas Comunes

### "Quiero ejecutar el proyecto"
→ Ver [QUICKSTART.md](QUICKSTART.md)

### "Quiero entender la arquitectura"
→ Ver [ARQUITECTURA.md](ARQUITECTURA.md)

### "Quiero deployar a producción"
→ Ver [DEPLOYMENT.md](DEPLOYMENT.md)

### "Quiero ver ejemplos de API"
→ Ver [EJEMPLOS_USO.md](EJEMPLOS_USO.md)

### "Quiero contribuir"
→ Ver [CONTRIBUTING.md](CONTRIBUTING.md)

### "Quiero ver el código de una feature específica"
→ Ver tabla en [Mapeo de Archivos por Funcionalidad](#mapeo-de-archivos-por-funcionalidad)

### "Quiero saber el estado del proyecto"
→ Ver [RESUMEN_FINAL.md](RESUMEN_FINAL.md) o [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md)

---

## 📊 Estadísticas del Proyecto

```
Archivos Python:         20
Archivos Docker:          4
Archivos Markdown:        9
Archivos Config:          7
Total:                   40+

Líneas de Código:      ~2,000
Líneas de Documentación: ~2,000

BD Tables:               18
API Endpoints:           10+
Pydantic Schemas:        40+
```

---

## 🔍 Buscar Información

### Por Tecnología
- **FastAPI**: [README.md](README.md) - Sección Stack
- **SQLAlchemy**: [app/infrastructure/db/models.py](app/infrastructure/db/models.py)
- **Pydantic**: [app/interfaces/schemas/schemas.py](app/interfaces/schemas/schemas.py)
- **Firebase**: [app/infrastructure/security/auth.py](app/infrastructure/security/auth.py)
- **Docker**: [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml)
- **GitHub Actions**: [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)

### Por Patrón
- **Hexagonal Architecture**: [ARQUITECTURA.md](ARQUITECTURA.md)
- **Singleton Pattern**: [app/infrastructure/firestore/client.py](app/infrastructure/firestore/client.py)
- **Soft Delete**: [app/infrastructure/db/models.py](app/infrastructure/db/models.py)
- **Dependency Injection**: [app/main.py](app/main.py)
- **Repository Pattern**: [ESTADO_PROYECTO.md](ESTADO_PROYECTO.md) - Pendiente

### Por Requisito
- **RF-Q01 (QR Residente)**: [app/interfaces/routers/qr_router.py](app/interfaces/routers/qr_router.py)
- **RF-Q02 (QR Visitante)**: [app/interfaces/routers/qr_router.py](app/interfaces/routers/qr_router.py)
- **RF-C01 (Crear Cuenta)**: [app/interfaces/routers/cuentas_router.py](app/interfaces/routers/cuentas_router.py)
- **RF-R01 (Registrar Residente)**: [app/interfaces/routers/residentes_router.py](app/interfaces/routers/residentes_router.py)

---

## 🛠️ Comandos Útiles

```bash
# Desarrollo
make dev                  # Ejecutar servidor
make install             # Instalar dependencias
make test                # Ejecutar tests
make lint                # Verificar código

# Docker
make docker-up           # Iniciar servicios
make docker-down         # Detener servicios
docker-compose logs -f   # Ver logs

# Base de datos
make db-migrate          # Ejecutar migraciones
make db-seed            # Cargar datos de prueba
./deploy.sh backup prod # Backup de producción
```

---

## 📋 Checklist para Nuevos Desarrolladores

- [ ] Cloné el repositorio
- [ ] Ejecuté QUICKSTART.md
- [ ] Accedí a http://localhost:8000/docs
- [ ] Leí README.md
- [ ] Leí ARQUITECTURA.md
- [ ] Exploré el código en `app/`
- [ ] Ejecuté algunos tests
- [ ] Hice un cambio pequeño y lo commiteé
- [ ] Leí CONTRIBUTING.md

---

## 📞 Preguntas Frecuentes

### "¿Cómo agrego un nuevo endpoint?"
1. Crear método en `app/interfaces/routers/`
2. Definir schema en `app/interfaces/schemas.py`
3. Crear servicio en `app/application/services/`
4. Registrar en `app/main.py`

### "¿Dónde va la lógica de negocio?"
→ En `app/domain/` y `app/application/services/`

### "¿Cómo conecto a una API externa?"
→ Crear cliente en `app/infrastructure/`

### "¿Cómo agrego validación?"
→ En schemas Pydantic o en servicios

### "¿Cómo despliego a producción?"
→ Ver [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🎓 Recursos de Aprendizaje

### Documentación Oficial
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web
- [SQLAlchemy](https://docs.sqlalchemy.org/) - ORM
- [Pydantic](https://docs.pydantic.dev/) - Validación
- [PostgreSQL](https://www.postgresql.org/docs/) - Base de datos
- [Firebase](https://firebase.google.com/docs) - Auth y FCM

### Patrones y Arquitectura
- [Hexagonal Architecture](https://en.wikipedia.org/wiki/Hexagonal_architecture)
- [Domain-Driven Design](https://en.wikipedia.org/wiki/Domain-driven_design)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### DevOps
- [Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [GitHub Actions](https://docs.github.com/en/actions)

---

## 🎯 Próximos Pasos

1. **Ahora**: Ejecuta [QUICKSTART.md](QUICKSTART.md)
2. **Después**: Lee [ARQUITECTURA.md](ARQUITECTURA.md)
3. **Luego**: Explora `app/` y estudia un router
4. **Finalmente**: Haz un cambio y crea un PR

---

## 📝 Notas Importantes

- 🔑 **Credenciales**: En `docker-compose.yml` y `.env.example`
- 🔒 **Secretos**: NUNCA commitear `.env` o credenciales
- 📦 **Dependencias**: Actualizar `requirements.txt` cuando agregues paquetes
- 🧪 **Tests**: Todos los nuevos features necesitan tests
- 📖 **Documentación**: Actualizar docs cuando cambies comportamiento

---

## 🙋 ¿Necesitas Ayuda?

1. **Búsqueda rápida**: Ctrl+F en esta página
2. **Preguntas técnicas**: Ver documentación relevante
3. **Reportar bugs**: GitHub Issues
4. **Contribuir**: Ver [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Versión**: 1.0.0  
**Última actualización**: Enero 2024  
**Mantenedor**: Equipo de Desarrollo

---

¡Bienvenido al proyecto! Esperamos que esta guía te ayude a navegar 🚀
