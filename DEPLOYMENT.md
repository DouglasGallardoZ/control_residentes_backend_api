# Guía de Deployment

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Desarrollo Local](#desarrollo-local)
3. [Deployment a Producción](#deployment-a-producción)
4. [Gestión de Base de Datos](#gestión-de-base-de-datos)
5. [Monitoreo y Logs](#monitoreo-y-logs)
6. [Troubleshooting](#troubleshooting)

---

## Requisitos Previos

### Sistema Operativo
- Linux (recomendado: Ubuntu 20.04+)
- macOS
- Windows con WSL2

### Software Requerido
```bash
# Docker (versión 20.10+)
docker --version

# Docker Compose (versión 1.29+)
docker-compose --version

# Git
git --version

# Python 3.12 (solo para desarrollo local sin Docker)
python3.12 --version
```

### Instalación de Docker

#### Ubuntu/Debian
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Agregar usuario actual al grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

#### macOS
```bash
# Instalar Docker Desktop desde: https://www.docker.com/products/docker-desktop
# O usar Homebrew:
brew install docker docker-compose

# Iniciar Docker Desktop
open /Applications/Docker.app
```

---

## Desarrollo Local

### Configuración Inicial

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd backend-api

# 2. Crear archivo .env
cp .env.example .env

# 3. Configurar variables de entorno
nano .env
```

### Con Docker Compose

```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

**Servicios disponibles en desarrollo:**
- FastAPI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PgAdmin: http://localhost:5050
- PostgreSQL: localhost:5432
- Firestore Emulator: localhost:8080
- Redis: localhost:6379

### Sin Docker (Desarrollo Puro)

```bash
# 1. Crear entorno virtual
python3.12 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
nano .env

# 4. Ejecutar migraciones
alembic upgrade head

# 5. Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Deployment a Producción

### Pre-Requisitos de Producción

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd backend-api

# 2. Crear variables de entorno para producción
cp .env.example .env.prod
nano .env.prod
```

**Variables críticas en `.env.prod`:**
```bash
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://user:password@postgres:5432/residencial_db
FIREBASE_PROJECT_ID=<tu-proyecto>
FIREBASE_API_KEY=<tu-api-key>
JWT_SECRET_KEY=<clave-secreta-fuerte>
REDIS_PASSWORD=<contraseña-fuerte>
```

### Despliegue con Docker

```bash
# 1. Usar el script de deployment
./deploy.sh deploy prod

# O manualmente:
# 2. Compilar imagen
docker-compose -f docker-compose.prod.yml build

# 3. Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# 4. Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. Verificar estado
docker-compose -f docker-compose.prod.yml ps
```

### Configuración de SSL/TLS

```bash
# 1. Crear directorio para certificados
mkdir -p ssl

# 2. Obtener certificados (ejemplo con Let's Encrypt)
certbot certonly --standalone -d tu-dominio.com
cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem ssl/

# 3. Actualizar nginx.conf con configuración SSL
# (Ver sección SSL en nginx.conf)
```

### Deployment Manual en Servidor

```bash
# 1. SSH al servidor
ssh usuario@servidor.com

# 2. Clonar repositorio
git clone <repository-url>
cd backend-api

# 3. Crear variables de entorno
nano .env.prod

# 4. Usar systemd para gestionar servicio
# Crear archivo /etc/systemd/system/residencial-api.service:
```

**Archivo systemd (residencial-api.service):**
```ini
[Unit]
Description=Residencial API Backend
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/path/to/backend-api
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable residencial-api
sudo systemctl start residencial-api

# Verificar estado
sudo systemctl status residencial-api

# Ver logs
sudo journalctl -u residencial-api -f
```

---

## Gestión de Base de Datos

### Migraciones

```bash
# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Aplicar n migraciones
alembic upgrade +2

# Revertir última migración
alembic downgrade -1

# Ver historial de migraciones
alembic history
```

### Backups

```bash
# Crear backup
./deploy.sh backup prod

# Restaurar backup
./deploy.sh restore backup_20240101_120000.sql prod
```

**Backup automático (cron):**
```bash
# Editar crontab
crontab -e

# Agregar línea para backup diario a las 2 AM
0 2 * * * /path/to/backend-api/deploy.sh backup prod > /var/log/residencial-backup.log 2>&1
```

### Limpieza de Datos

```bash
# Conectar a PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U residencial_user -d residencial_db

# Ejemplo: Eliminar registros antiguos
DELETE FROM acceso WHERE fecha_acceso < NOW() - INTERVAL '90 days';
DELETE FROM log_actividad WHERE fecha_creacion < NOW() - INTERVAL '6 months';

# Optimizar índices
REINDEX DATABASE residencial_db;
VACUUM ANALYZE;
```

---

## Monitoreo y Logs

### Ver Logs

```bash
# Logs del backend
docker-compose -f docker-compose.prod.yml logs -f backend

# Logs de PostgreSQL
docker-compose -f docker-compose.prod.yml logs -f postgres

# Logs de Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Ver últimas N líneas
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Health Check

```bash
# Verificar endpoint de salud
curl http://localhost:8000/health

# Desde dentro del contenedor
docker-compose exec backend curl http://localhost:8000/health
```

### Métricas (Opcional)

Instalar Prometheus + Grafana:

```bash
# Ver docker-compose.monitoring.yml
docker-compose -f docker-compose.monitoring.yml up -d

# Acceder a Grafana
# http://localhost:3000
# Usuario: admin / Contraseña: admin
```

---

## Troubleshooting

### Problema: PostgreSQL no inicia

```bash
# Revisar logs
docker-compose logs postgres

# Solución: Resetear volumen
docker-compose down -v
docker-compose up -d

# O resetear solo PostgreSQL
docker volume rm backend-api_postgres_data
```

### Problema: Puerto en uso

```bash
# Encontrar proceso usando puerto
lsof -i :8000

# Matar proceso
kill -9 <PID>

# O cambiar puerto en .env
DATABASE_PORT=5433
```

### Problema: Migraciones fallan

```bash
# Revisar estado de migraciones
alembic current

# Si hay migraciones pendientes
alembic upgrade head

# Si hay conflictos, revisar
alembic history
```

### Problema: Firestore no conecta

```bash
# Verificar variable de entorno
echo $FIRESTORE_EMULATOR_HOST

# En desarrollo, debería ser:
# firestore:8080

# Verificar que el emulador está corriendo
docker-compose ps | grep firestore
```

### Problema: Firebase Auth no funciona

```bash
# Verificar ruta del archivo de credenciales
ls -la ./firebase-credentials.json

# Verificar variable de entorno
echo $FIREBASE_CREDENTIALS_PATH

# Test de conexión
docker-compose exec backend python -c "from app.infrastructure.security.auth import firebase_auth; print(firebase_auth.get_user('test'))"
```

### Limpiar Todo y Reiniciar

```bash
# Remover todos los contenedores y volúmenes
docker-compose down -v

# Remover imagen
docker-compose rm -f

# Reconstruir
docker-compose build --no-cache

# Iniciar nuevamente
docker-compose up -d
```

---

## Checklist de Producción

- [ ] Variables de entorno configuradas
- [ ] SSL/TLS configurado
- [ ] Backups automáticos configurados
- [ ] Monitoreo y alertas configurados
- [ ] Logs centralizados
- [ ] Firewall configurado
- [ ] Secrets seguros (sin hardcoding)
- [ ] Rate limiting configurado
- [ ] CORS apropiadamente configurado
- [ ] Database replicada/backup
- [ ] CDN para archivos estáticos (si aplica)
- [ ] DNS configurado
- [ ] Documentación actualizada

---

## Contacto y Soporte

Para problemas de deployment, contactar al equipo de DevOps o revisar:
- Logs de la aplicación
- Docker logs
- Sistema operativo logs
- Documentación de Docker Compose

**Comando de diagnostico rápido:**
```bash
./deploy.sh health
docker-compose logs --tail=50
```
