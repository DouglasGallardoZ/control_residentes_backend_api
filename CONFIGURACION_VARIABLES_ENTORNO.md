# Configuración de Variables de Entorno

La API está completamente configurada para leer todas sus variables de entorno desde un archivo `.env`.

## Archivos de Configuración Disponibles

### `.env.example` (RECOMENDADO PARA SETUP)
Archivo plantilla con todas las variables de entorno disponibles y sus valores por defecto.
- **Uso**: Copia este archivo como base para crear tu `.env` personalizado
- **Contiene**: Documentación de cada variable

### `.env.local` (DESARROLLO LOCAL)
Archivo pre-configurado para desarrollo local con valores típicos de desarrollo.
- **Uso**: Puedes copiar este archivo como `.env` para desarrollo rápido
- **Características**: PostgreSQL en localhost, Debug activo, CORS configurado para desarrollo

### `.env` (ARCHIVO REAL - NO VERSIONADO)
Este es el archivo actual que usa la aplicación.
- **Importante**: Este archivo está en `.gitignore` y NO debe versionarse en git
- **Cómo crear**: Copia `.env.example` o `.env.local` y personaliza según tu ambiente

## Cómo Configurar

### Opción 1: Desarrollo Local Rápido
```bash
# Copia la configuración local
cp .env.local .env

# Ajusta si es necesario (puertos, contraseñas, etc.)
nano .env
```

### Opción 2: Usar .env.example
```bash
# Copia la plantilla
cp .env.example .env

# Personaliza para tu ambiente
nano .env
```

### Opción 3: Docker/Producción
```bash
# Define variables de entorno antes de ejecutar
export DB_HOST=postgres
export DB_USER=prod_user
export DB_PASSWORD=prod_password_segura
export TIMEZONE=America/Bogota
export LOG_LEVEL=INFO

# O pasa las variables al contenedor
docker run -e DB_HOST=postgres -e DB_USER=prod_user ...
```

## Variables de Entorno Principales

### Base de Datos
```env
DB_USER=residencial_user              # Usuario PostgreSQL
DB_PASSWORD=residencial_password      # Contraseña PostgreSQL
DB_HOST=localhost                     # Host del servidor
DB_PORT=5432                          # Puerto PostgreSQL
DB_NAME=residencial_db                # Nombre de la base de datos
```

### Firebase
```env
FIREBASE_PROJECT_ID=tu-proyecto      # ID del proyecto Firebase
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json  # Ruta a JSON
FIREBASE_API_KEY=tu-api-key          # API Key de Firebase
FCM_SENDER_ID=tu-sender-id           # Firebase Cloud Messaging ID
```

### JWT (Autenticación)
```env
JWT_SECRET_KEY=tu-secret-key-segura  # Clave secreta JWT
JWT_ALGORITHM=HS256                  # Algoritmo JWT
JWT_EXPIRATION_HOURS=24              # Horas de expiración del token
```

### API
```env
API_VERSION=v1                       # Versión de API
API_TITLE=API Control de Acceso     # Título de API
TIMEZONE=America/Bogota              # Zona horaria por defecto
```

### Seguridad
```env
PASSWORD_MIN_LENGTH=8                # Longitud mínima de contraseña
PASSWORD_MUST_HAVE_UPPER=True        # Requiere mayúscula
PASSWORD_MUST_HAVE_DIGIT=True        # Requiere dígito
MAX_BIOMETRIC_FAILED_ATTEMPTS=2      # Intentos fallidos permitidos
```

### CORS
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8080  # Orígenes permitidos
```

### Servidor
```env
APP_HOST=0.0.0.0                     # Host de escucha (0.0.0.0 = todos)
APP_PORT=8000                        # Puerto de la API
APP_RELOAD=True                      # Recarga automática (False en producción)
LOG_LEVEL=DEBUG                      # Nivel de logging
```

## Ambientes Típicos

### Desarrollo Local
```bash
DB_HOST=localhost
DB_PASSWORD=password123
SQLALCHEMY_ECHO=True
LOG_LEVEL=DEBUG
APP_RELOAD=True
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:4200
```

### Staging
```bash
DB_HOST=postgres-staging.internal
DB_PASSWORD=staging_password_segura
SQLALCHEMY_ECHO=False
LOG_LEVEL=INFO
APP_RELOAD=False
CORS_ORIGINS=https://staging.example.com
```

### Producción
```bash
DB_HOST=postgres-prod.internal
DB_PASSWORD=produccion_password_ultra_segura
SQLALCHEMY_ECHO=False
LOG_LEVEL=WARNING
APP_RELOAD=False
JWT_SECRET_KEY=produccion_secret_key_super_segura
CORS_ORIGINS=https://api.example.com
```

## Validación de Variables

La aplicación se inicializa automáticamente leyendo las variables de entorno. Si faltan variables requeridas o son inválidas, FastAPI mostrará un error claro indicando cuál es el problema.

## Con Docker Compose

### docker-compose.yml
```yaml
environment:
  - DB_USER=residencial_user
  - DB_PASSWORD=residencial_password
  - DB_HOST=postgres
  - DB_PORT=5432
  - DB_NAME=residencial_db
  - TIMEZONE=America/Bogota
```

### Con .env en Docker Compose
```bash
# Crear archivo .env
cp .env.example .env

# Docker Compose leerá automáticamente las variables
docker-compose up
```

## Seguridad

### ⚠️ IMPORTANTE
1. **NUNCA** commites el archivo `.env` a git (ya está en `.gitignore`)
2. **NUNCA** expongas `JWT_SECRET_KEY` o `DB_PASSWORD` en el código
3. **SIEMPRE** usa contraseñas fuertes en producción
4. **SIEMPRE** usa HTTPS con CORS restrictivo en producción

### Buenas Prácticas
- Usa variables de entorno diferentes por ambiente
- Rota contraseñas regularmente
- No copies credenciales en logs
- Usa valores seguros en producción
- Documenta qué variable controla qué comportamiento

## Troubleshooting

### Error: "Could not connect to database"
- Verifica `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`
- Asegúrate que PostgreSQL está corriendo
- Prueba conexión: `psql -h $DB_HOST -U $DB_USER -d $DB_NAME`

### Error: "Invalid CORS origin"
- Verifica que `CORS_ORIGINS` está separado por comas
- Incluye el protocolo (http:// o https://)
- Ejemplo correcto: `http://localhost:3000,https://api.example.com`

### Error: "Firebase credentials not found"
- Verifica que `FIREBASE_CREDENTIALS_PATH` apunta al archivo correcto
- El archivo debe ser JSON válido descargado de Firebase Console

## Ejemplos Rápidos

### Para desarrollo local
```bash
cd /home/dgallardo/Universidad/Proyectos/backend-api
cp .env.local .env
python -m uvicorn app.main:app --reload
```

### Con Docker
```bash
# Crear .env desde .env.example
cp .env.example .env

# Ejecutar con docker-compose
docker-compose up
```

### Ver qué variables está usando la app
```bash
python -c "from app.config import get_settings; s = get_settings(); print(s.DATABASE_URL)"
```
