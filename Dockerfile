# Dockerfile para GCP Cloud Run
# Base: Ubuntu 24.04 con Python 3.12
# Optimizado para Cloud Run (puerto 8080, sin estado, usuario no-root)

FROM ubuntu:24.04

# Configurar locale y zona horaria
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=es_ES.UTF-8 \
    LANGUAGE=es_ES:es \
    LC_ALL=es_ES.UTF-8 \
    TZ=America/Bogota

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de aplicación
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Crear virtual environment e instalar paquetes
RUN python3.12 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Configurar puerto para Cloud Run (por defecto 8080)
ENV PORT=8080 \
    HOST=0.0.0.0 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    APP_RELOAD=False

# Exponer puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/docs || exit 1

# Comando para iniciar la aplicación
# Cloud Run requiere que la aplicación escuche en 0.0.0.0:8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
