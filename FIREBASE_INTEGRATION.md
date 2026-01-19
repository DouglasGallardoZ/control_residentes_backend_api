# Firebase Auth Integration - Backend API

## Arquitectura Implementada: Híbrida

```
Flutter App (Firebase Auth)
    ↓
Firebase Auth (email/password registration)
    ↓ (devuelve firebase_uid)
API POST /api/v1/cuentas/residente/firebase
    ↓ (crea metadata local)
BD: tabla cuenta con firebase_uid
    ↓
JWT Token para endpoints protegidos
```

---

## Cambios en la BD

### Tabla `cuenta` - Modificada

**ANTES:**
```sql
CREATE TABLE cuenta (
    cuenta_pk SERIAL PRIMARY KEY,
    persona_titular_fk INTEGER NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,  ← REMOVIDO
    ...
);
```

**AHORA:**
```sql
CREATE TABLE cuenta (
    cuenta_pk SERIAL PRIMARY KEY,
    persona_titular_fk INTEGER NOT NULL,
    firebase_uid VARCHAR(128) NOT NULL UNIQUE,  ← AGREGADO
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    ...
);
```

**Migración necesaria:**
```bash
docker-compose down -v
docker-compose up -d
```

---

## Modelos - Cambios

### `app/infrastructure/db/models.py`
```python
class Cuenta(Base):
    """Tabla de cuentas de usuario (Firebase Auth)"""
    cuenta_pk = Column(Integer, primary_key=True)
    persona_titular_fk = Column(Integer, ForeignKey('persona.persona_pk'), nullable=False)
    firebase_uid = Column(String(128), nullable=False, unique=True)  # ← NUEVO
    # password_hash REMOVIDO
    estado = Column(String(10), nullable=False, default='activo')
    ...
```

---

## Endpoints - API

### 1. POST `/api/v1/cuentas/residente/firebase`

**Crea cuenta para residente después de Firebase Auth**

**Request:**
```json
{
  "persona_id": 5,
  "firebase_uid": "sFIiHjWR0cXPcMHk7pKn3Z8xQmN"
}
```

**Response (201):**
```json
{
  "id": 1,
  "firebase_uid": "sFIiHjWR0cXPcMHk7pKn3Z8xQmN",
  "persona_id": 5,
  "nombres": "Juan Pérez",
  "mensaje": "Cuenta de residente creada exitosamente"
}
```

**Flujo en Flutter:**
```dart
// 1. Registrar en Firebase
var userCredential = await FirebaseAuth.instance
    .createUserWithEmailAndPassword(email: email, password: password);

// 2. Obtener UID
String firebaseUid = userCredential.user!.uid;

// 3. Registrar en API
final response = await http.post(
  Uri.parse('http://localhost:8000/api/v1/cuentas/residente/firebase'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'persona_id': 5,
    'firebase_uid': firebaseUid,
  }),
);
```

---

### 2. POST `/api/v1/cuentas/miembro/firebase`

**Crea cuenta para miembro de familia después de Firebase Auth**

**Request:**
```json
{
  "persona_id": 8,
  "firebase_uid": "tGJjIkXS1dYQnMlOp9aZ2vWxRs3"
}
```

**Response (201):**
```json
{
  "id": 2,
  "firebase_uid": "tGJjIkXS1dYQnMlOp9aZ2vWxRs3",
  "persona_id": 8,
  "nombres": "Ana García",
  "mensaje": "Cuenta de miembro de familia creada exitosamente"
}
```

---

### 3. POST `/{cuenta_id}/bloquear`

**Bloquear una cuenta**

```bash
curl -X POST "http://localhost:8000/api/v1/cuentas/1/bloquear" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Comportamiento sospechoso",
    "usuario_actualizado": "admin"
  }'
```

---

### 4. POST `/{cuenta_id}/desbloquear`

**Desbloquear una cuenta**

```bash
curl -X POST "http://localhost:8000/api/v1/cuentas/1/desbloquear" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Revisión completada",
    "usuario_actualizado": "admin"
  }'
```

---

### 5. DELETE `/{cuenta_id}`

**Eliminar una cuenta (soft delete)**

```bash
curl -X DELETE "http://localhost:8000/api/v1/cuentas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Usuario solicitó eliminación",
    "usuario_actualizado": "admin"
  }'
```

---

## Middleware de Autenticación

**Archivo:** `app/infrastructure/security/firebase_auth.py`

### Usar en endpoints protegidos:

```python
from app.infrastructure.security.firebase_auth import obtener_usuario_autenticado

@router.get("/perfil")
def get_perfil(usuario: dict = Depends(obtener_usuario_autenticado)):
    """
    Endpoint protegido - requiere Firebase JWT token
    """
    return {
        "firebase_uid": usuario["firebase_uid"],
        "cuenta_id": usuario["cuenta_id"],
        "nombres": usuario["nombres"],
        "estado": usuario["estado"]
    }
```

**Uso en Cliente (Flutter):**
```dart
// 1. Obtener token de Firebase
String token = await FirebaseAuth.instance.currentUser!.getIdToken();

// 2. Enviar en header Authorization
final response = await http.get(
  Uri.parse('http://localhost:8000/api/v1/perfil'),
  headers: {
    'Authorization': 'Bearer $token'
  },
);
```

---

## Testing Temporal (Sin Firebase)

Mientras configuras Firebase, usa el mock:

```python
from app.infrastructure.security.firebase_auth import obtener_usuario_mock

@router.get("/perfil/test")
def get_perfil_test(usuario: dict = Depends(obtener_usuario_mock)):
    """
    Usa mock para testing sin Firebase
    Headers esperado: usuario_id=1
    """
    return usuario
```

**Test en Postman:**
```
GET http://localhost:8000/api/v1/perfil/test
Headers:
  usuario_id: 1
```

---

## Configuración de Firebase (Próximos Pasos)

### 1. Instalar firebase-admin
```bash
pip install firebase-admin
```

### 2. Descargar credenciales de Firebase
- Ir a Firebase Console
- Project Settings → Service Accounts
- Descargar JSON de credenciales
- Guardar como `firebase-credentials.json` en root del proyecto

### 3. Inicializar Firebase en `app/infrastructure/security/firebase_auth.py`
```python
import firebase_admin
from firebase_admin import auth

# Inicializar (una sola vez)
firebase_admin.initialize_app(
    options={
        'projectId': 'tu-proyecto-id'
    }
)

class FirebaseAuth:
    @staticmethod
    def verify_id_token(token: str) -> dict:
        """Verifica JWT token real de Firebase"""
        try:
            decoded = auth.verify_id_token(token)
            return decoded
        except auth.InvalidIdTokenError:
            raise ValueError("Token inválido")
```

---

## Validaciones en Endpoints

Ambos endpoints (`/residente/firebase` y `/miembro/firebase`) validan:

✅ Persona existe y está activa
✅ Usuario es residente o miembro de familia activo
✅ No hay cuenta previa para esa persona
✅ Firebase UID es único
✅ Registra evento en tabla `evento_cuenta`

---

## Schema Changes Summary

| Campo | Antes | Ahora | Razón |
|-------|-------|-------|-------|
| `username` | VARCHAR(50) UNIQUE | REMOVIDO | Firebase maneja usernames |
| `password_hash` | TEXT NOT NULL | REMOVIDO | Firebase maneja hashing |
| `firebase_uid` | N/A | VARCHAR(128) UNIQUE | Vincular con Firebase Auth |

---

## Seguridad

- ✅ No almacenamos contraseñas (Firebase las maneja)
- ✅ Firebase UID es único y no puede reutilizarse
- ✅ Validación de tokens JWT en endpoints protegidos
- ✅ Auditoría: evento_cuenta registra cambios

---

## Próximas Tareas

1. [ ] Configura Firebase Console
2. [ ] Descarga credenciales de servicio
3. [ ] Actualiza `firebase_auth.py` con inicialización real
4. [ ] Instala `firebase-admin`
5. [ ] Resetea BD: `docker-compose down -v && docker-compose up -d`
6. [ ] Prueba endpoints con Postman
7. [ ] Integra en Flutter con Firebase SDK

---

**Última actualización:** 19 de Enero, 2026
