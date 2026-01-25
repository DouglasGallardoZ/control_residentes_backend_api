# Despliegue en Google Cloud Run

## Requisitos Previos

```bash
# Instalar Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Verificar instalación
gcloud --version

# Autenticarse
gcloud auth login

# Configurar proyecto
gcloud config set project PROJECT_ID
```

## Paso 1: Preparar Variables de Entorno

Crea un archivo `.env.cloudrun` con todas las variables necesarias:

```bash
cat > .env.cloudrun << 'EOF'
# Base de Datos
DB_HOST=cloudsql-proxy
DB_PORT=5432
DB_USER=residencial_user
DB_PASSWORD=tu_contraseña_segura
DB_NAME=residencial_db

# JWT
JWT_SECRET_KEY=tu_clave_super_larga_y_aleatoria_aqui_minimo_64_caracteres
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Firebase
FIREBASE_PROJECT_ID=tu-firebase-project
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
FIREBASE_API_KEY=tu-firebase-api-key
FIREBASE_FCM_SENDER_ID=tu-sender-id

# API
API_TITLE=API Control de Acceso Residencial
API_VERSION=v1
TIMEZONE=America/Bogota
LOG_LEVEL=INFO

# Seguridad
PASSWORD_MIN_LENGTH=8
PASSWORD_MUST_HAVE_UPPER=True
PASSWORD_MUST_HAVE_SPECIAL=True

# CORS
CORS_ORIGINS=https://tu-frontend.com,https://app.tu-dominio.com

# Pagination
PAGINATION_DEFAULT_PAGE_SIZE=10
PAGINATION_MAX_PAGE_SIZE=100

# QR
QR_TOKEN_LENGTH=32
QR_CODE_VALIDITY_MINUTES=1440
EOF
```

## Paso 2: Construir la Imagen (Local o con Cloud Build)

### Opción A: Construir Localmente y Push

```bash
# Construir imagen
docker build -t gcr.io/PROJECT_ID/api-residencial:latest .

# Verificar que funciona localmente
docker run -it \
  -p 8080:8080 \
  -e DB_HOST=localhost \
  -e DB_USER=test \
  -e DB_PASSWORD=test \
  gcr.io/PROJECT_ID/api-residencial:latest

# Push a Google Container Registry
docker push gcr.io/PROJECT_ID/api-residencial:latest
```

### Opción B: Construir con Cloud Build (Recomendado)

```bash
gcloud builds submit \
  --tag gcr.io/PROJECT_ID/api-residencial:latest \
  --timeout=1800s
```

## Paso 3: Configurar Cloud SQL Proxy (Si usas Cloud SQL)

```bash
# En Cloud Console o via gcloud:
gcloud sql instances create residencial-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Obtener la connection string
gcloud sql instances describe residencial-db \
  --format='value(connectionName)'
# Ejemplo: PROJECT_ID:us-central1:residencial-db
```

## Paso 4: Desplegar a Cloud Run

### Opción A: Con Secret Manager para variables sensibles

```bash
# Crear secrets en Google Secret Manager
echo -n "tu_db_password" | gcloud secrets create db-password --data-file=-
echo -n "tu_jwt_key_larga" | gcloud secrets create jwt-secret-key --data-file=-
echo -n "tu_firebase_json" | gcloud secrets create firebase-credentials --data-file=-

# Verificar secrets
gcloud secrets list
```

### Opción B: Desplegar con variables de entorno

```bash
gcloud run deploy api-residencial \
  --image gcr.io/PROJECT_ID/api-residencial:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DB_USER=residencial_user,API_TITLE=API Residencial,TIMEZONE=America/Bogota,LOG_LEVEL=INFO" \
  --set-secrets="DB_PASSWORD=db-password:latest,JWT_SECRET_KEY=jwt-secret-key:latest" \
  --cpu 2 \
  --memory 1Gi \
  --timeout 3600 \
  --max-instances 100 \
  --min-instances 1
```

### Opción C: Con Cloud SQL Proxy

```bash
gcloud run deploy api-residencial \
  --image gcr.io/PROJECT_ID/api-residencial:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances PROJECT_ID:us-central1:residencial-db \
  --set-env-vars="DB_HOST=/cloudsql/PROJECT_ID:us-central1:residencial-db,DB_USER=residencial_user,DB_NAME=residencial_db" \
  --set-secrets="DB_PASSWORD=db-password:latest,JWT_SECRET_KEY=jwt-secret-key:latest" \
  --cpu 2 \
  --memory 1Gi \
  --timeout 3600 \
  --max-instances 100 \
  --min-instances 1
```

## Paso 5: Configurar credenciales de Firebase (Si aplica)

```bash
# Copiar archivo de credenciales a Cloud Storage
gsutil cp firebase-credentials.json gs://PROJECT_ID-firebase-creds/

# Montarla en Cloud Run (requiere Artifact Registry)
# O usar Secret Manager:
gcloud secrets create firebase-credentials \
  --data-file=firebase-credentials.json
```

## Paso 6: Verificar el Despliegue

```bash
# Ver el estado del servicio
gcloud run services describe api-residencial --region us-central1

# Ver logs
gcloud run services logs read api-residencial --region us-central1 --limit 50

# Obtener la URL
URL=$(gcloud run services describe api-residencial \
  --region us-central1 \
  --format='value(status.url)')

# Probar la API
curl ${URL}/docs

# Probar endpoint
curl -X GET ${URL}/perfil \
  -H "Authorization: Bearer TU_TOKEN"
```

## Configuración Avanzada con `gcloud-run.yaml`

Crea un archivo de configuración para Cloud Run:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: api-residencial
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: '1'
        autoscaling.knative.dev/maxScale: '100'
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/api-residencial:latest
        ports:
        - containerPort: 8080
        env:
        - name: DB_HOST
          value: "cloudsql-proxy"
        - name: DB_PORT
          value: "5432"
        - name: DB_USER
          value: "residencial_user"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-password
              key: latest
        - name: TIMEZONE
          value: "America/Bogota"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          limits:
            cpu: "2"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /docs
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
```

Desplegar con:
```bash
gcloud run services replace gcloud-run.yaml --region us-central1
```

## Monitoreo y Logging

```bash
# Ver logs en tiempo real
gcloud run services logs read api-residencial \
  --region us-central1 \
  --follow

# Exportar logs a Cloud Logging
gcloud logging write api-residencial-log "Servicio desplegado"

# Crear alertas en Cloud Monitoring
# (Ir a Cloud Console → Monitoring → Alertas)
```

## Optimizaciones para Cloud Run

### 1. **Instancias Mínimas y Máximas**
```bash
gcloud run services update api-residencial \
  --min-instances 1 \
  --max-instances 100 \
  --region us-central1
```

### 2. **Configurar Auto-scaling**
- Cloud Run escala automáticamente basado en demanda
- Configurar CPU/Memoria según necesidad
- 100 requests concurrentes por CPU

### 3. **Timeout de Solicitud**
```bash
gcloud run services update api-residencial \
  --timeout 3600 \
  --region us-central1
```

### 4. **Usar Concurrencia Limitada**
```bash
gcloud run deploy api-residencial \
  --concurrency 80 \
  --region us-central1
```

## Troubleshooting

### Error: "Cloud SQL Proxy connection failed"
```bash
# Verificar que Cloud SQL Admin API está habilitada
gcloud services enable sqladmin.googleapis.com

# Verificar connection string
gcloud sql instances describe residencial-db --format='value(connectionName)'
```

### Error: "Permission denied reading secret"
```bash
# Dar permisos al servicio de Cloud Run
PROJECTID=$(gcloud config get-value project)
CLOUDRUN_SA="${PROJECTID}@appspot.gserviceaccount.com"

gcloud secrets add-iam-policy-binding db-password \
  --member=serviceAccount:${CLOUDRUN_SA} \
  --role=roles/secretmanager.secretAccessor
```

### Error: "Image not found"
```bash
# Verificar imagen existe
gcloud container images list --repository=gcr.io/PROJECT_ID

# Verificar que está pública o que tienes permisos
gcloud container images describe gcr.io/PROJECT_ID/api-residencial:latest
```

### Alto uso de memoria
- Reducir `--memory` y usar más instancias
- Implementar connection pooling en BD
- Usar request-scoped dependencies

## CI/CD con Cloud Build

Crear `.cloudbuild.yaml`:

```yaml
steps:
  # Build
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/api-residencial:latest', '.']

  # Push
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/api-residencial:latest']

  # Deploy
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
      - run
      - --deploy
      - --image=gcr.io/$PROJECT_ID/api-residencial:latest
      - --location=us-central1
      - --service-name=api-residencial

images:
  - gcr.io/$PROJECT_ID/api-residencial:latest

options:
  machineType: 'N1_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY

timeout: 1800s
```

Disparar build:
```bash
gcloud builds submit --config=.cloudbuild.yaml
```

## URLs de Referencia

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Cloud SQL Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Build](https://cloud.google.com/build/docs)
