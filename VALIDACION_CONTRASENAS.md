# Política de Validación de Contraseñas

## Implementación
**Archivo:** [app/interfaces/routers/cuentas_router.py](app/interfaces/routers/cuentas_router.py)
**Función:** `validar_contraseña(password: str)`

## Requisitos de Contraseña (CV-20)

La contraseña debe cumplir con TODOS los siguientes criterios:

| Criterio | Requisito | Validación |
|----------|-----------|-----------|
| **Longitud mínima** | 8 caracteres | `len(password) >= 8` |
| **Longitud máxima** | 72 bytes | `len(password.encode('utf-8')) <= 72` |
| **Mayúscula** | Al menos 1 | `any(c.isupper() for c in password)` |
| **Número** | Al menos 1 | `any(c.isdigit() for c in password)` |
| **Carácter especial** | Al menos 1 | Uno de: `!@#$%^&*()_+-=[]{}|;:,.<>?` |

## Ejemplos Válidos
✅ `MiPass@123`
✅ `Secure#Password2024`
✅ `MyP@ssw0rd`
✅ `Test!ing123`

## Ejemplos Inválidos
❌ `password123` - Sin mayúscula, sin carácter especial
❌ `PASSWORD!` - Sin número, sin minúscula
❌ `Pass@1` - Menos de 8 caracteres
❌ `MuyLargaConcaracteresEspecialesYNumerosYmayúsculasqueexcedelos72bytes!@#$%` - Más de 72 bytes (UTF-8)

## Mensajes de Error

```json
{
  "detail": "Contraseña debe tener al menos 8 caracteres"
}
```

```json
{
  "detail": "Contraseña demasiado larga. Máximo 72 bytes (aprox 72 caracteres)"
}
```

```json
{
  "detail": "Contraseña debe contener al menos una mayúscula"
}
```

```json
{
  "detail": "Contraseña debe contener al menos un número"
}
```

```json
{
  "detail": "Contraseña debe contener al menos un carácter especial"
}
```

## Limitación Técnica: Bcrypt 72 bytes

Bcrypt es un algoritmo de hashing seguro pero tiene un límite de 72 bytes por contraseña. Esto es una limitación técnica del estándar.

### Por qué 72 bytes es seguro:
- 72 bytes = ~72 caracteres ASCII o más si incluyen acentos (UTF-8)
- Es suficiente para contraseñas seguras y memorables
- Previene ataques de fuerza bruta

### Ejemplos de longitud en UTF-8:
- `Contraseña123!` = 16 bytes (válido)
- `MiP@ssw0rd` = 11 bytes (válido)
- `ElÑoño2024@` = 15 bytes (válido, incluye ñ con tilde)

## Endpoints que Usan Validación

### 1. POST `/api/v1/cuentas/residente`
Crea cuenta para residente titular
```bash
curl -X POST "http://localhost:8000/api/v1/cuentas/residente" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": 1,
    "username": "residente_123",
    "password": "MiPass@123",
    "usuario_creado": "admin"
  }'
```

### 2. POST `/api/v1/cuentas/miembro`
Crea cuenta para miembro de familia
```bash
curl -X POST "http://localhost:8000/api/v1/cuentas/miembro" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": 5,
    "username": "miembro_familia_01",
    "password": "FamPass@456",
    "usuario_creado": "admin"
  }'
```

## Cambios Recientes

### v1.1 (19 Enero 2026)
- ✅ Implementada validación de contraseña con política de seguridad
- ✅ Agregado endpoint `/api/v1/cuentas/miembro` para miembros de familia
- ✅ Validación de límite de 72 bytes (bcrypt)
- ✅ Error handling mejorado con mensajes específicos

## Consideraciones Futuras

1. **Multi-factor Authentication (MFA)**
   - Código OTP por SMS
   - Código OTP por email
   - Autenticación biométrica

2. **Recuperación de Contraseña**
   - Token temporal enviado por email
   - Validación de identidad con preguntas

3. **Historial de Contraseñas**
   - Prevenir reutilización de contraseñas recientes
   - Mantener hash de últimas 5 contraseñas

4. **Expiración de Contraseña**
   - Forzar cambio cada 90 días
   - Notificaciones previas

---
**Última actualización:** 19 de Enero, 2026
