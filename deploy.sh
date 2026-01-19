#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker no está instalado"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose no está instalado"
    exit 1
fi

# Parse arguments
COMMAND=$1
ENVIRONMENT=${2:-development}

case $COMMAND in
    "deploy")
        log_info "Iniciando deployment a $ENVIRONMENT..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            log_info "Verificando archivo .env.prod..."
            if [ ! -f .env.prod ]; then
                log_error ".env.prod no encontrado"
                exit 1
            fi
            
            log_info "Compilando imagen Docker..."
            docker-compose -f docker-compose.prod.yml build
            
            log_info "Iniciando servicios..."
            docker-compose -f docker-compose.prod.yml up -d
            
        else
            log_info "Iniciando servicios de desarrollo..."
            docker-compose up -d
        fi
        
        sleep 5
        log_info "Esperando a que PostgreSQL esté listo..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U ${DB_USER:-residencial_user}
        else
            docker-compose exec -T postgres pg_isready -U residencial_user
        fi
        
        if [ $? -eq 0 ]; then
            log_success "PostgreSQL está listo"
            
            log_info "Ejecutando migraciones..."
            if [ "$ENVIRONMENT" == "production" ]; then
                docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
            else
                docker-compose exec -T backend alembic upgrade head
            fi
            
            log_success "Deployment completado"
        else
            log_error "PostgreSQL no está listo después de esperar"
            exit 1
        fi
        ;;
        
    "stop")
        log_info "Deteniendo servicios de $ENVIRONMENT..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml down
        else
            docker-compose down
        fi
        
        log_success "Servicios detenidos"
        ;;
        
    "restart")
        log_info "Reiniciando servicios de $ENVIRONMENT..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml restart
        else
            docker-compose restart
        fi
        
        log_success "Servicios reiniciados"
        ;;
        
    "logs")
        log_info "Mostrando logs de $ENVIRONMENT..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml logs -f backend
        else
            docker-compose logs -f backend
        fi
        ;;
        
    "shell")
        log_info "Abriendo shell en contenedor backend..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml exec backend bash
        else
            docker-compose exec backend bash
        fi
        ;;
        
    "db-shell")
        log_info "Abriendo psql en PostgreSQL..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml exec postgres psql -U ${DB_USER:-residencial_user} -d ${DB_NAME:-residencial_db}
        else
            docker-compose exec postgres psql -U residencial_user -d residencial_db
        fi
        ;;
        
    "backup")
        log_info "Creando backup de la base de datos..."
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U ${DB_USER:-residencial_user} ${DB_NAME:-residencial_db} > $BACKUP_FILE
        else
            docker-compose exec -T postgres pg_dump -U residencial_user residencial_db > $BACKUP_FILE
        fi
        
        if [ $? -eq 0 ]; then
            log_success "Backup creado: $BACKUP_FILE"
        else
            log_error "Error al crear backup"
            exit 1
        fi
        ;;
        
    "restore")
        BACKUP_FILE=$2
        
        if [ -z "$BACKUP_FILE" ]; then
            log_error "Especifica el archivo de backup"
            echo "Uso: ./deploy.sh restore <archivo.sql>"
            exit 1
        fi
        
        log_warning "Se va a restaurar el backup: $BACKUP_FILE"
        read -p "¿Estás seguro? (y/n) " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ "$ENVIRONMENT" == "production" ]; then
                docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ${DB_USER:-residencial_user} ${DB_NAME:-residencial_db} < $BACKUP_FILE
            else
                docker-compose exec -T postgres psql -U residencial_user residencial_db < $BACKUP_FILE
            fi
            
            if [ $? -eq 0 ]; then
                log_success "Backup restaurado"
            else
                log_error "Error al restaurar backup"
                exit 1
            fi
        else
            log_info "Operación cancelada"
        fi
        ;;
        
    "health")
        log_info "Verificando salud de los servicios..."
        
        if [ "$ENVIRONMENT" == "production" ]; then
            docker-compose -f docker-compose.prod.yml ps
        else
            docker-compose ps
        fi
        ;;
        
    "cleanup")
        log_info "Limpiando recursos Docker no usados..."
        docker system prune -f
        log_success "Limpieza completada"
        ;;
        
    *)
        cat << EOF
${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}
${BLUE}║           Backend API - Deployment Script                       ║${NC}
${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}

Uso: ./deploy.sh <comando> [entorno]

Comandos:
  deploy [dev|prod]       - Desplegar aplicación
  stop [dev|prod]         - Detener servicios
  restart [dev|prod]      - Reiniciar servicios
  logs [dev|prod]         - Ver logs
  shell [dev|prod]        - Abrir shell en backend
  db-shell [dev|prod]     - Abrir psql en PostgreSQL
  backup [dev|prod]       - Crear backup de BD
  restore <archivo.sql>   - Restaurar backup
  health [dev|prod]       - Verificar estado de servicios
  cleanup                 - Limpiar recursos Docker

Entorno por defecto: development

Ejemplos:
  ./deploy.sh deploy              # Desplegar en desarrollo
  ./deploy.sh deploy prod         # Desplegar en producción
  ./deploy.sh logs prod           # Ver logs de producción
  ./deploy.sh backup prod         # Backup de producción
EOF
        ;;
esac
