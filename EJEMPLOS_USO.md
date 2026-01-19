# Ejemplos de uso y casos de prueba

## Ejemplos cURL para probar endpoints

### 1. Crear Cuenta de Residente (RF-C01)

```bash
curl -X POST "http://localhost:8000/api/v1/cuentas/residente" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": 1,
    "username": "juan.perez",
    "password": "MiPassword123!",
    "usuario_creado": "admin"
  }'
```

### 2. Generar Código QR Propio (RF-Q01)

```bash
curl -X POST "http://localhost:8000/api/v1/qr/generar-propio" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "duracion_horas": 2,
    "fecha_acceso": "2026-01-15",
    "hora_inicio": "14:30"
  }'
```

### 3. Generar QR para Visita (RF-Q02)

```bash
curl -X POST "http://localhost:8000/api/v1/qr/generar-visita" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "visita_identificacion": "1234567890",
    "visita_nombres": "Juan",
    "visita_apellidos": "Gonzalez",
    "motivo_visita": "Visita social",
    "duracion_horas": 3,
    "fecha_acceso": "2026-01-15",
    "hora_inicio": "15:00"
  }'
```

### 4. Bloquear Cuenta Individual (RF-C07)

```bash
curl -X POST "http://localhost:8000/api/v1/cuentas/1/bloquear" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Sospecha de actividad fraudulenta",
    "usuario_actualizado": "admin"
  }'
```

### 5. Desbloquear Cuenta Individual (RF-C08)

```bash
curl -X POST "http://localhost:8000/api/v1/cuentas/1/desbloquear" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Se verificó la legitimidad de la cuenta",
    "usuario_actualizado": "admin"
  }'
```

### 6. Eliminar Cuenta (RF-C09)

```bash
curl -X DELETE "http://localhost:8000/api/v1/cuentas/1" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Usuario solicitó eliminar cuenta",
    "usuario_actualizado": "admin"
  }'
```

### 7. Registrar Residente (RF-R01)

```bash
curl -X POST "http://localhost:8000/api/v1/residentes" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "identificacion": "1234567890",
    "tipo_identificacion": "cédula",
    "nombres": "Juan",
    "apellidos": "Pérez",
    "fecha_nacimiento": "1990-05-15",
    "correo": "juan@example.com",
    "celular": "0912345678",
    "vivienda_id": 1,
    "usuario_creado": "admin",
    "doc_autorizacion_pdf": "https://storage.example.com/doc.pdf"
  }'
```

### 8. Desactivar Residente (RF-R03)

```bash
curl -X POST "http://localhost:8000/api/v1/residentes/1/desactivar" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Residencia temporal",
    "usuario_actualizado": "admin"
  }'
```

### 9. Reactivar Residente (RF-R05)

```bash
curl -X POST "http://localhost:8000/api/v1/residentes/1/reactivar" \
  -H "Authorization: Bearer {idToken}" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Retorno del residente",
    "usuario_actualizado": "admin"
  }'
```

## Scripts de Testing

### Script Python para Testing

```python
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": "Bearer {TU_ID_TOKEN}",
    "Content-Type": "application/json"
}

def test_crear_cuenta():
    """Test: Crear cuenta de residente"""
    data = {
        "persona_id": 1,
        "username": "test.user",
        "password": "TestPassword123!",
        "usuario_creado": "admin"
    }
    response = requests.post(f"{BASE_URL}/cuentas/residente", 
                            json=data, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_generar_qr():
    """Test: Generar QR"""
    fecha_acceso = datetime.now().date() + timedelta(days=1)
    data = {
        "duracion_horas": 2,
        "fecha_acceso": fecha_acceso.isoformat(),
        "hora_inicio": "14:30"
    }
    response = requests.post(f"{BASE_URL}/qr/generar-propio", 
                            json=data, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_bloquear_cuenta():
    """Test: Bloquear cuenta"""
    cuenta_id = 1
    data = {
        "motivo": "Test bloqueo",
        "usuario_actualizado": "admin"
    }
    response = requests.post(f"{BASE_URL}/cuentas/{cuenta_id}/bloquear",
                            json=data, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("=== TEST: Crear Cuenta ===")
    test_crear_cuenta()
    
    print("\n=== TEST: Generar QR ===")
    test_generar_qr()
    
    print("\n=== TEST: Bloquear Cuenta ===")
    test_bloquear_cuenta()
```

## Casos de Prueba Manual

### Caso 1: Flujo Completo de Acceso con QR

**Precondiciones:**
- Residente "Juan Pérez" existe en la BD
- Residente tiene cuenta activa

**Pasos:**
1. Residente genera QR propio para hoy a las 14:30 con duración 2 horas
2. QR se crea en PostgreSQL
3. QR se sincroniza en Firestore
4. API retorna token del QR
5. Residente presenta QR en puerta
6. Sistema valida QR
7. Sistema valida vigencia
8. Sistema marca como "usado"
9. Abre puerta
10. Notifica al guardia

**Resultado esperado:**
- QR marcado como "usado" en ambas BD
- Registro de acceso creado
- Notificación enviada

### Caso 2: Bloqueo en Cascada de Residente y Miembros

**Precondiciones:**
- Residente con cuenta activa
- 2 miembros de familia con cuentas activas

**Pasos:**
1. Admin bloquea cuenta de residente
2. Sistema detecta miembros asociados
3. Sistema bloquea automáticamente cuentas de miembros
4. Eventos registrados en evento_cuenta
5. Cambios registrados en bitácora

**Resultado esperado:**
- 3 cuentas marcadas como inactivas
- 3 eventos en evento_cuenta con tipo "cuenta_bloqueada"
- Registros de auditoría en bitácora

### Caso 3: Notificación Masiva a Residentes

**Precondiciones:**
- Existen 10 residentes activos con tokens FCM registrados
- Admin tiene permisos para enviar notificaciones

**Pasos:**
1. Admin envía notificación masiva
2. Sistema obtiene lista de residentes activos
3. Sistema obtiene tokens FCM
4. FCM envía notificación a 10 dispositivos
5. Sistema registra notificación en BD
6. Sistema registra destinos de notificación

**Resultado esperado:**
- Notificación creada en tabla notificacion
- 10 destinos registrados en notificacion_destino
- Push recibida en 10 dispositivos
- Respuesta indique 10 exitosas, 0 fallidas

### Caso 4: Validación de Criterios Comunes (CV-01)

**Requerimiento:** Identificación ecuatoriana inválida

**Pasos:**
1. Intentar crear persona con identificación: "abc123" (inválida)
2. Sistema debe rechazar

**Resultado esperado:**
- Error 400: "Identificación inválida"
- Persona no creada

## Base de Datos: Datos Iniciales (Seeders)

```sql
-- Vivienda de prueba
INSERT INTO vivienda (manzana, villa, estado, usuario_creado)
VALUES ('A', '101', 'activo', 'admin');

-- Persona de prueba
INSERT INTO persona (identificacion, tipo_identificacion, nombres, apellidos, 
                     fecha_nacimiento, estado, usuario_creado)
VALUES ('1234567890', 'cédula', 'Juan', 'Pérez', 
        '1990-05-15', 'activo', 'admin');

-- Propietario de vivienda
INSERT INTO propietario_vivienda (vivienda_propiedad_fk, persona_propietario_fk, 
                                  estado, usuario_creado)
VALUES (1, 1, 'activo', 'admin');

-- Residente
INSERT INTO residente_vivienda (vivienda_reside_fk, persona_residente_fk, 
                               estado, usuario_creado)
VALUES (1, 1, 'activo', 'admin');

-- Cuenta
INSERT INTO cuenta (persona_titular_fk, username, password_hash, estado, usuario_creado)
VALUES (1, 'juan.perez', 
        '$2b$12$...',  -- Hash bcrypt de "password123"
        'activo', 'admin');
```

## Variables de Entorno para Testing

```bash
# .env.test
DATABASE_URL=postgresql://test:test@localhost:5432/residencial_test
FIREBASE_PROJECT_ID=test-project
FIREBASE_CREDENTIALS_PATH=./test-firebase-credentials.json
JWT_SECRET_KEY=test-secret-key
BIOMETRIA_SERVICE_URL=http://localhost:8001
```

## Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/test_qr.py -v
pytest tests/test_cuentas.py -v
pytest tests/test_residentes.py -v

# Tests con output detallado
pytest -vv -s
```

## Monitoreo y Logs

```bash
# Ver logs de la aplicación
tail -f logs/app.log

# Logs de eventos de cuenta
grep "evento_cuenta" logs/app.log

# Logs de acceso
grep "acceso" logs/app.log

# Búsqueda por usuario
grep "admin" logs/app.log
```
