#!/bin/bash

# Script de verificación del proyecto

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Verificación de Estructura del Proyecto Backend API       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Contador
TOTAL=0
ENCONTRADOS=0

check_file() {
    local file=$1
    local description=$2
    TOTAL=$((TOTAL + 1))
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $description"
        echo -e "   📍 $file"
        ENCONTRADOS=$((ENCONTRADOS + 1))
    else
        echo -e "${RED}❌${NC} $description"
        echo -e "   ${RED}No encontrado:${NC} $file"
    fi
}

check_dir() {
    local dir=$1
    local description=$2
    TOTAL=$((TOTAL + 1))
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅${NC} $description"
        echo -e "   📍 $dir"
        ENCONTRADOS=$((ENCONTRADOS + 1))
    else
        echo -e "${RED}❌${NC} $description"
        echo -e "   ${RED}No encontrado:${NC} $dir"
    fi
}

echo "## Archivos Core Backend"
echo ""
check_file "app/config.py" "Configuración centralizada"
check_file "app/main.py" "Punto de entrada FastAPI"
check_file "app/infrastructure/db/models.py" "Modelos SQLAlchemy (18 tablas)"
check_file "app/infrastructure/db/database.py" "Setup de base de datos"
check_file "app/domain/entities/models.py" "Entidades de dominio"
check_file "app/domain/use_cases/qr_use_cases.py" "Casos de uso"
check_file "app/application/services/servicios.py" "Servicios de aplicación"

echo ""
echo "## Integraciones"
echo ""
check_file "app/infrastructure/firestore/client.py" "Cliente Firestore"
check_file "app/infrastructure/notifications/fcm_client.py" "Cliente FCM"
check_file "app/infrastructure/security/auth.py" "Autenticación"

echo ""
echo "## APIs y Schemas"
echo ""
check_file "app/interfaces/schemas/schemas.py" "Pydantic Schemas"
check_file "app/interfaces/routers/qr_router.py" "Router QR"
check_file "app/interfaces/routers/cuentas_router.py" "Router Cuentas"
check_file "app/interfaces/routers/residentes_router.py" "Router Residentes"

echo ""
echo "## Docker & DevOps"
echo ""
check_file "Dockerfile" "Dockerfile multi-stage"
check_file "docker-compose.yml" "Docker Compose desarrollo"
check_file "docker-compose.prod.yml" "Docker Compose producción"
check_file ".dockerignore" ".dockerignore"
check_file "Makefile" "Makefile con comandos"
check_file "deploy.sh" "Script de deployment"
check_file "nginx.conf" "Configuración Nginx"

echo ""
echo "## Configuración"
echo ""
check_file "pyproject.toml" "Configuración pyproject.toml"
check_file "setup.cfg" "Configuración setup.cfg"
check_file "pytest.ini" "Configuración pytest"
check_file ".gitignore" ".gitignore"
check_file ".env.example" "Template de variables .env"

echo ""
echo "## CI/CD"
echo ""
check_dir ".github/workflows" "Directorio workflows"
check_file ".github/workflows/ci-cd.yml" "Pipeline CI/CD"

echo ""
echo "## Documentación"
echo ""
check_file "README.md" "README principal"
check_file "ARQUITECTURA.md" "Documentación de arquitectura"
check_file "DEPLOYMENT.md" "Guía de deployment"
check_file "EJEMPLOS_USO.md" "Ejemplos de uso"
check_file "ESTADO_PROYECTO.md" "Estado del proyecto"
check_file "CONTRIBUTING.md" "Guía de contribución"
check_file "CHANGELOG.md" "Changelog"
check_file "RESUMEN_FINAL.md" "Resumen final del proyecto"

echo ""
echo "## Directorios de Aplicación"
echo ""
check_dir "app/domain" "Capa de dominio"
check_dir "app/application" "Capa de aplicación"
check_dir "app/infrastructure" "Capa de infraestructura"
check_dir "app/interfaces" "Capa de interfaces"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "📊 Resultados: ${GREEN}$ENCONTRADOS${NC}/$TOTAL archivos y directorios"
echo ""

if [ $ENCONTRADOS -eq $TOTAL ]; then
    echo -e "${GREEN}✅ ¡Verificación completada exitosamente!${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. Inicializar Alembic: alembic init alembic"
    echo "2. Crear migración base: alembic revision --autogenerate -m 'Initial schema'"
    echo "3. Aplicar migraciones: alembic upgrade head"
    echo "4. Ejecutar servidor: make dev"
    echo ""
    exit 0
else
    FALTANTES=$((TOTAL - ENCONTRADOS))
    echo -e "${RED}⚠️  Faltan $FALTANTES archivo(s)${NC}"
    echo ""
    exit 1
fi
