# Base: Python 3.12 slim
FROM python:3.12-slim

# Establecer variables de entorno generales y de localización
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=es_ES.UTF-8 \
    LANGUAGE=es_ES:es \
    LC_ALL=es_ES.UTF-8 \
    TZ=America/Bogota

# Instalar dependencias del sistema:
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    tzdata \
    postgresql-client \
    curl \
    ca-certificates \
    build-essential \
    python3-dev \
    # Configurar el locale a español
    && sed -i '/es_ES.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    # Configurar la zona horaria
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    # Limpiar caché de apt para reducir el tamaño de la imagen
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear y establecer directorio de trabajo
WORKDIR /app

# Copiar solo requirements.txt primero para aprovechar el caché de capas de Docker
COPY requirements.txt .

# Actualizar pip e instalar dependencias de Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación (asumiendo que tu código está en la carpeta 'app')
COPY app ./app

# Configurar variables de entorno (por defecto 8080)
ENV PORT=8080 \
    HOST=0.0.0.0 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    APP_RELOAD=False

# Exponer el puerto
EXPOSE 8080

# Comando para iniciar la aplicación
# Cloud Run requiere que la aplicación escuche en 0.0.0.0:8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1","--log-level","debug"]
