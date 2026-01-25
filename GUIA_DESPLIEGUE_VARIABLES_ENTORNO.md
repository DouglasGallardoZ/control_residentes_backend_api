# Guía de Despliegue con Variables de Entorno

## Descripción General

La API está completamente configurada para usar variables de entorno en lugar de valores hardcodeados. Esto permite que la misma imagen de Docker funcione en desarrollo, staging y producción con diferentes configuraciones.

## Archivo `.env` - La Clave del Deployment

El archivo `.env` es el corazón de la configuración. Las variables de entorno se leen desde este archivo (o desde variables del sistema).

### Archivos Disponibles

1. **`.env.example`** - Plantilla completa con todas las variables
2. **`.env.local`** - Configuración para desarrollo local
3. **`.env.production`** - Plantilla para producción (ajusta valores reales)
4. **`.env`** - El archivo actual que usa la aplicación (NO en git)

## Setup por Ambiente

### DESARROLLO LOCAL

```bash
# 1. Copia la configuración local
cp .env.local .env

# 2. Inicia la aplicación
python -m uvicorn app.main:app --reload

# 3. Valida la configuración
python validate_config.py
```

### STAGING (Docker Compose)

```bash
# 1. Copia y personaliza la configuración
cp .env.example .env

# 2. Edita los valores según tu staging
nano .env
# Cambiar:
# DB_HOST=postgres (nombre del servicio Docker)
# DB_PASSWORD=staging_password
# CORS_ORIGINS=https://staging.example.com
# LOG_LEVEL=INFO

# 3. Levanta con Docker Compose
docker-compose up -d

# 4. Valida dentro del contenedor
docker-compose exec backend python validate_config.py
```

### PRODUCCIÓN (Kubernetes o Docker)

#### Opción 1: Variables de Entorno del Sistema

```bash
# Establece variables en tu entorno
export DB_HOST=postgres.prod.internal
export DB_PASSWORD=prod_super_segura
export DB_USER=prod_residencial_user
export DB_NAME=residencial_db_prod
export TIMEZONE=America/Bogota
export LOG_LEVEL=INFO
export APP_RELOAD=False
export JWT_SECRET_KEY=clave_super_larga_y_aleatoria_aqui
export CORS_ORIGINS=https://api.example.com,https://app.example.com

# Inicia la aplicación
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Opción 2: Con Docker (Variables en docker run)

```bash
docker run -d \
  --name api-residencial \
  -p 8000:8000 \
  -e DB_HOST=postgres.prod.internal \
  -e DB_PASSWORD=prod_super_segura \
  -e DB_USER=prod_residencial_user \
  -e DB_NAME=residencial_db_prod \
  -e TIMEZONE=America/Bogota \
  -e LOG_LEVEL=INFO \
  -e APP_RELOAD=False \
  -e JWT_SECRET_KEY=clave_super_larga_y_aleatoria_aqui \
  -e CORS_ORIGINS=https://api.example.com,https://app.example.com \
  residencial-api:latest
```

#### Opción 3: Con Docker Compose (Archivo .env)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: residencial-api:latest
    container_name: api-residencial
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=residencial_db_prod
      - TIMEZONE=America/Bogota
      - LOG_LEVEL=INFO
      - APP_RELOAD=False
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
    depends_on:
      - postgres
    networks:
      - residencial-network
    restart: always

  postgres:
    image: postgres:15
    container_name: postgres-prod
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: residencial_db_prod
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - residencial-network
    restart: always

volumes:
  postgres-data:

networks:
  residencial-network:
    driver: bridge
```

```bash
# Uso
cp .env.production .env
nano .env  # Personaliza los valores reales
docker-compose -f docker-compose.prod.yml up -d
```

#### Opción 4: Con Kubernetes (ConfigMap + Secrets)

```yaml
---
# ConfigMap para configuración no sensible
apiVersion: v1
kind: ConfigMap
metadata:
  name: residencial-config
data:
  DB_HOST: "postgres.default.svc.cluster.local"
  DB_PORT: "5432"
  DB_NAME: "residencial_db_prod"
  TIMEZONE: "America/Bogota"
  LOG_LEVEL: "INFO"
  APP_RELOAD: "False"
  API_VERSION: "v1"
  CORS_ORIGINS: "https://api.example.com,https://app.example.com"

---
# Secret para datos sensibles
apiVersion: v1
kind: Secret
metadata:
  name: residencial-secrets
type: Opaque
stringData:
  DB_USER: prod_residencial_user
  DB_PASSWORD: CAMBIAR_ESTO_CONTRASEÑA_SUPER_SEGURA
  JWT_SECRET_KEY: CAMBIAR_ESTO_CLAVE_SUPER_LARGA_Y_ALEATORIA

---
# Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: residencial-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: residencial-api
  template:
    metadata:
      labels:
        app: residencial-api
    spec:
      containers:
      - name: api
        image: residencial-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: residencial-config
        - secretRef:
            name: residencial-secrets
        env:
        - name: APP_HOST
          value: "0.0.0.0"
        - name: APP_PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /docs
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Variables Críticas por Ambiente

### Siempre Cambiar en Producción

```env
# Seguridad - OBLIGATORIO
JWT_SECRET_KEY=       # Clave muy larga y aleatoria (>64 chars)
DB_PASSWORD=          # Contraseña segura

# Base de Datos
DB_HOST=              # Dirección del servidor real
DB_USER=              # Usuario real

# API
CORS_ORIGINS=         # Solo dominios autorizados
LOG_LEVEL=INFO        # NO DEBUG en producción
APP_RELOAD=False      # NUNCA True en producción

# Política de Contraseñas
PASSWORD_MIN_LENGTH=12
PASSWORD_MUST_HAVE_SPECIAL=True
```

### Típicamente Iguales en Todos los Ambientes

```env
TIMEZONE=America/Bogota
API_TITLE=API Control de Acceso Residencial
PAGINATION_DEFAULT_PAGE_SIZE=10
QR_TOKEN_LENGTH=32
```

## Checklist de Despliegue

- [ ] ¿El archivo `.env` está en `.gitignore`?
- [ ] ¿No hay valores hardcodeados en el código?
- [ ] ¿Se ejecutó `python validate_config.py` sin errores?
- [ ] ¿`JWT_SECRET_KEY` es aleatorio y seguro (>64 caracteres)?
- [ ] ¿`DB_PASSWORD` es seguro?
- [ ] ¿`CORS_ORIGINS` contiene solo dominios autorizados?
- [ ] ¿`LOG_LEVEL` es `INFO` o `WARNING` en producción?
- [ ] ¿`APP_RELOAD` es `False` en producción?
- [ ] ¿Las credenciales de Firebase están correctas?
- [ ] ¿La conexión a PostgreSQL funciona (`pytest` o test manual)?
- [ ] ¿El archivo `.env` NO está en git?

## Verificación Rápida

```bash
# Ver qué valores está usando la aplicación
python validate_config.py

# Prueba de conexión a BD
python -c "from app.config import get_settings; s=get_settings(); print('DB URL:', s.DATABASE_URL)"

# Prueba de la API
curl http://localhost:8000/docs
```

## Troubleshooting

### "Could not connect to database"
- Verifica `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`
- En Docker: usa el nombre del servicio (`postgres` no `localhost`)

### "Invalid environment variable"
- Ejecuta `python validate_config.py` para ver qué falta
- Las variables enteras deben ser números: `DB_PORT=5432` (no "5432")
- Las variables booleanas: `True` o `False` (case-sensitive)

### "CORS error"
- Verifica que `CORS_ORIGINS` está separado por comas sin espacios
- Incluye el protocolo: `https://` no solo `example.com`

## Referencias

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/usage/settings/)
- [Environment Variables Best Practices](https://12factor.net/config)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
