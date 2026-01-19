.PHONY: help install dev test lint format clean docker-build docker-up docker-down db-migrate db-seed

help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║           Backend API - Residencial Access Control             ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Comandos disponibles:"
	@echo ""
	@echo "  Desarrollo:"
	@echo "    make install          - Instalar dependencias"
	@echo "    make dev              - Ejecutar servidor en modo desarrollo"
	@echo "    make lint             - Ejecutar linting (pylint, flake8)"
	@echo "    make format           - Formatear código (black, isort)"
	@echo "    make test             - Ejecutar tests con pytest"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-build     - Compilar imagen Docker"
	@echo "    make docker-up        - Iniciar servicios con docker-compose"
	@echo "    make docker-down      - Detener servicios"
	@echo "    make docker-logs      - Ver logs de los servicios"
	@echo ""
	@echo "  Base de datos:"
	@echo "    make db-migrate       - Ejecutar migraciones Alembic"
	@echo "    make db-seed          - Cargar datos de prueba"
	@echo "    make db-downgrade     - Revertir última migración"
	@echo ""
	@echo "  Utilidades:"
	@echo "    make clean            - Limpiar archivos temporales"
	@echo "    make requirements      - Actualizar requirements.txt"
	@echo ""

# Instalación de dependencias
install:
	@echo "📦 Instalando dependencias..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	@echo "✅ Dependencias instaladas"

install-dev:
	@echo "📦 Instalando dependencias de desarrollo..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio black flake8 pylint isort mypy
	@echo "✅ Dependencias instaladas"

# Desarrollo
dev:
	@echo "🚀 Iniciando servidor en modo desarrollo..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-with-db:
	@echo "🚀 Iniciando servidor con docker-compose..."
	docker-compose up -d postgres redis firestore
	sleep 2
	@echo "⏳ Esperando a que PostgreSQL esté listo..."
	docker-compose exec -T postgres pg_isready -U residencial_user
	@echo "✅ PostgreSQL listo"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Linting
lint:
	@echo "🔍 Ejecutando linting..."
	flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
	pylint app --disable=all --enable=E,F
	@echo "✅ Linting completado"

format:
	@echo "🎨 Formateando código..."
	black app
	isort app
	@echo "✅ Código formateado"

check-format:
	@echo "🔍 Verificando formato..."
	black --check app
	isort --check-only app
	@echo "✅ Formato verificado"

# Testing
test:
	@echo "🧪 Ejecutando tests..."
	pytest tests/ -v --cov=app --cov-report=html
	@echo "✅ Tests completados"

test-fast:
	@echo "🧪 Ejecutando tests (modo rápido)..."
	pytest tests/ -v --tb=short
	@echo "✅ Tests completados"

# Docker
docker-build:
	@echo "🐳 Compilando imagen Docker..."
	docker-compose build
	@echo "✅ Imagen compilada"

docker-up:
	@echo "🐳 Iniciando servicios..."
	docker-compose up -d
	@echo "✅ Servicios iniciados"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   PgAdmin: http://localhost:5050"
	@echo "   FastAPI: http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

docker-down:
	@echo "🛑 Deteniendo servicios..."
	docker-compose down
	@echo "✅ Servicios detenidos"

docker-restart:
	@echo "🔄 Reiniciando servicios..."
	docker-compose restart
	@echo "✅ Servicios reiniciados"

docker-logs:
	@echo "📋 Mostrando logs..."
	docker-compose logs -f backend

docker-logs-all:
	@echo "📋 Mostrando todos los logs..."
	docker-compose logs -f

docker-shell:
	@echo "🐚 Abriendo shell en contenedor backend..."
	docker-compose exec backend bash

docker-db-shell:
	@echo "🐚 Abriendo psql en contenedor PostgreSQL..."
	docker-compose exec postgres psql -U residencial_user -d residencial_db

# Base de datos
db-migrate:
	@echo "📊 Ejecutando migraciones..."
	alembic upgrade head
	@echo "✅ Migraciones completadas"

db-migrate-create:
	@echo "📊 Creando nueva migración..."
	@read -p "Nombre de la migración: " migration_name; \
	alembic revision --autogenerate -m "$$migration_name"

db-downgrade:
	@echo "⏮️  Revirtiendo última migración..."
	alembic downgrade -1
	@echo "✅ Migración revertida"

db-seed:
	@echo "🌱 Cargando datos de prueba..."
	@if [ -f "scripts/seed.sql" ]; then \
		psql -h localhost -U residencial_user -d residencial_db -f scripts/seed.sql; \
		echo "✅ Datos cargados"; \
	else \
		echo "⚠️  scripts/seed.sql no encontrado"; \
	fi

# Utilidades
clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	rm -rf build dist htmlcov .tox
	@echo "✅ Limpieza completada"

requirements:
	@echo "📝 Actualizando requirements.txt..."
	pip freeze > requirements.txt
	@echo "✅ requirements.txt actualizado"

# Estadísticas de código
stats:
	@echo "📊 Estadísticas del código:"
	@find app -name "*.py" | wc -l | xargs echo "  Archivos Python:"
	@find app -name "*.py" -exec wc -l {} + | tail -1 | xargs echo "  Líneas de código:"

# Validación
validate:
	@echo "✔️  Validando el proyecto..."
	@make check-format
	@make lint
	@echo "✅ Validación completada"

# Todas las herramientas
all-dev: install-dev format lint test
	@echo "✅ Desarrollo completado"
