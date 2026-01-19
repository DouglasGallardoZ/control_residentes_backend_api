# QUICKSTART.md

# 🚀 Quick Start Guide

Guía rápida para poner el proyecto en funcionamiento en 5 minutos.

## Opción 1: Con Docker (Recomendado) ⭐

```bash
# 1. Clonar proyecto
git clone <tu-repo>
cd backend-api

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Iniciar servicios
docker-compose up -d

# 4. Verificar servicios
docker-compose ps

# 5. Abrir en navegador
# FastAPI: http://localhost:8000
# Docs: http://localhost:8000/docs
# PgAdmin: http://localhost:5050
```

**Credenciales por defecto:**
- PgAdmin: admin@residencial.com / admin123
- PostgreSQL: residencial_user / residencial_password

---

## Opción 2: Desarrollo Local (Sin Docker)

```bash
# 1. Crear entorno virtual
python3.12 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
nano .env

# 4. Ejecutar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Pruebas Rápidas

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Generar QR Personal
```bash
curl -X POST "http://localhost:8000/qr/generar-propio" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha_vigencia": "2024-02-01",
    "hora_inicio": "08:00",
    "duracion_minutos": 60,
    "persona_id": 1
  }'
```

### 3. Ver Documentación Interactiva
```
Abre en navegador: http://localhost:8000/docs
```

---

## Comandos Útiles

```bash
# Ver logs
docker-compose logs -f backend

# Acceder a shell del contenedor
docker-compose exec backend bash

# Ejecutar comando en BD
docker-compose exec postgres psql -U residencial_user -d residencial_db

# Detener servicios
docker-compose down

# Limpiar todo
docker-compose down -v
```

---

## Arquitectura en Un Vistazo

```
┌─────────────────────────────────────────┐
│         Cliente (Web/Mobile)             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           FastAPI (Puerto 8000)          │
│  ┌──────────────────────────────────┐   │
│  │  Interfaces (Routers)            │   │
│  │  - /qr                           │   │
│  │  - /cuentas                      │   │
│  │  - /residentes                   │   │
│  └──────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
┌───────────────┐    ┌─────────────────┐
│  PostgreSQL   │    │   Firestore     │
│  (Datos)      │    │   (Real-time)   │
└───────────────┘    └─────────────────┘
                          │
                          ▼
                   ┌─────────────────┐
                   │ Firebase Auth   │
                   │ & FCM (Push)    │
                   └─────────────────┘
```

---

## Estructura de Carpetas

```
app/
├── domain/           # Lógica de negocio
├── application/      # Servicios
├── infrastructure/   # BD, APIs externas
└── interfaces/       # HTTP endpoints
```

---

## Primeras Pruebas

### 1. Abrir Swagger UI
```
http://localhost:8000/docs
```

### 2. Crear una persona (POST /personas)
```json
{
  "cedula": "1234567890",
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "telefono": "0987654321"
}
```

### 3. Crear una vivienda (POST /viviendas)
```json
{
  "numero": "101",
  "piso": 1,
  "bloque": "A"
}
```

### 4. Generar QR (POST /qr/generar-propio)
```json
{
  "persona_id": 1,
  "fecha_vigencia": "2024-02-01",
  "hora_inicio": "08:00",
  "duracion_minutos": 60
}
```

---

## Solución de Problemas

### PostgreSQL no inicia
```bash
# Resetear BD
docker-compose down -v
docker-compose up -d postgres
```

### Puerto 8000 en uso
```bash
# Ver qué usa el puerto
lsof -i :8000

# Cambiar puerto en .env
FASTAPI_PORT=8001
```

### Módulo no encontrado
```bash
# Reinstalar dependencias
pip install --force-reinstall -r requirements.txt
```

---

## Próximos Pasos

1. ✅ Proyecto ejecutándose
2. 📚 Leer [README.md](README.md)
3. 🏗️ Estudiar [ARQUITECTURA.md](ARQUITECTURA.md)
4. 🚀 Leer [DEPLOYMENT.md](DEPLOYMENT.md)
5. 💻 Explorar código en `app/`

---

## Recursos

- 📖 [FastAPI Docs](https://fastapi.tiangolo.com/)
- 🐘 [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- 🔥 [Firebase Docs](https://firebase.google.com/docs)
- 🐳 [Docker Docs](https://docs.docker.com/)
- 🔗 [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

## Soporte

¿Problemas? Ver:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Troubleshooting
- [README.md](README.md) - Documentación completa
- [CONTRIBUTING.md](CONTRIBUTING.md) - Cómo contribuir

---

**¡Bienvenido a Residencial API! 🎉**
