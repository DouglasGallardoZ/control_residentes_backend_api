# Cambios: Eliminación de Valores Quemados en usuario_creado/usuario_actualizado

**Fecha**: 2026-01-19
**Estado**: ✅ COMPLETADO

---

## Resumen de Cambios

Se han actualizado todos los endpoints de la API para que los campos `usuario_creado` y `usuario_actualizado` sean **parámetros obligatorios** en las peticiones HTTP, en lugar de tener valores por defecto quemados en el código.

---

## Cambios por Archivo

### 1. **cuentas_router.py**

#### Endpoint: `POST /api/v1/cuentas/{cuenta_id}/bloquear`
```python
# ANTES:
def bloquear_cuenta(
    cuenta_id: int,
    motivo: str = "Cuenta bloqueada por administrador",
    usuario_actualizado: str = "admin",  # ❌ QUEMADO
    db: Session = Depends(get_db)
)

# DESPUÉS:
def bloquear_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,  # ✅ OBLIGATORIO
    motivo: str = "Cuenta bloqueada",
    db: Session = Depends(get_db)
)
```

#### Endpoint: `POST /api/v1/cuentas/{cuenta_id}/desbloquear`
```python
# ANTES:
def desbloquear_cuenta(
    cuenta_id: int,
    motivo: str = "Cuenta desbloqueada por administrador",
    usuario_actualizado: str = "admin",  # ❌ QUEMADO
    db: Session = Depends(get_db)
)

# DESPUÉS:
def desbloquear_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,  # ✅ OBLIGATORIO
    motivo: str = "Cuenta desbloqueada",
    db: Session = Depends(get_db)
)
```

#### Endpoint: `DELETE /api/v1/cuentas/{cuenta_id}`
```python
# ANTES:
def eliminar_cuenta(
    cuenta_id: int,
    motivo: str = "Cuenta eliminada por usuario",
    usuario_actualizado: str = "admin",  # ❌ QUEMADO
    db: Session = Depends(get_db)
)

# DESPUÉS:
def eliminar_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,  # ✅ OBLIGATORIO
    motivo: str = "Cuenta eliminada",
    db: Session = Depends(get_db)
)
```

---

### 2. **propietarios_router.py**

#### Endpoint: `POST /api/v1/propietarios`
```python
# ANTES:
def registrar_propietario(
    persona_data: PersonaCreate,
    vivienda_id: int,
    usuario_creado: str = "api_user",  # ❌ QUEMADO
    db: Session = Depends(get_db)
)

# DESPUÉS:
def registrar_propietario(
    persona_data: PersonaCreate,
    vivienda_id: int,
    usuario_creado: str,  # ✅ OBLIGATORIO
    db: Session = Depends(get_db)
)
```

#### Endpoint: `POST /api/v1/propietarios/{propietario_id}/conyuge`
```python
# ANTES:
def registrar_conyuge_propietario(
    propietario_id: int,
    persona_data: PersonaCreate,
    usuario_creado: str = "api_user",  # ❌ QUEMADO
    db: Session = Depends(get_db)
)

# DESPUÉS:
def registrar_conyuge_propietario(
    propietario_id: int,
    persona_data: PersonaCreate,
    usuario_creado: str,  # ✅ OBLIGATORIO
    db: Session = Depends(get_db)
)
```

---

### 3. **miembros_router.py**

#### Endpoint: `POST /api/v1/miembros/{residente_id}/agregar`
```python
# ANTES:
def agregar_miembro_familia(
    residente_id: int,
    vivienda_id: int,
    persona_data: PersonaCreate,
    parentesco: str,
    parentesco_otro_desc: str = None,
    usuario_creado: str = "api_user",  # ❌ QUEMADO
    db: Session = Depends(get_db)
)

# DESPUÉS:
def agregar_miembro_familia(
    residente_id: int,
    vivienda_id: int,
    persona_data: PersonaCreate,
    parentesco: str,
    usuario_creado: str,  # ✅ OBLIGATORIO
    parentesco_otro_desc: str = None,
    db: Session = Depends(get_db)
)
```

---

### 4. **residentes_router.py**

#### Endpoint: `POST /api/v1/residentes/{persona_id}/foto`
```python
# ANTES:
def agregar_foto_residente(
    persona_id: int,
    ruta_imagen: str,
    formato: str,
    db: Session = Depends(get_db)
)
# En el cuerpo:
usuario_creado="api_user"  # ❌ QUEMADO

# DESPUÉS:
def agregar_foto_residente(
    persona_id: int,
    request: AgregarFotoRequest,  # ✅ Schema con usuario_creado
    db: Session = Depends(get_db)
)
# En el cuerpo:
usuario_creado=request.usuario_creado  # ✅ Desde request
```

**Schema creado**:
```python
class AgregarFotoRequest(BaseModel):
    """Schema para agregar foto a residente"""
    ruta_imagen: str
    formato: str
    usuario_creado: str
```

---

### 5. **qr_router.py**

#### Cambios en ambos endpoints de generación de QR
```python
# ANTES:
usuario_creado="sistema"  # ❌ QUEMADO

# DESPUÉS:
usuario_creado=cuenta.firebase_uid  # ✅ Usa identificador real del usuario
```

**Endpoints actualizados**:
- `POST /api/v1/qr/generar-propio` (visita también)
- `POST /api/v1/qr/generar-visita`

---

## Ejemplos de Uso Actualizado

### Antes (con valores quemados):
```bash
# POST /api/v1/cuentas/1/bloquear
curl -X POST http://localhost:8000/api/v1/cuentas/1/bloquear
```

### Después (valores en petición):
```bash
# POST /api/v1/cuentas/1/bloquear
curl -X POST http://localhost:8000/api/v1/cuentas/1/bloquear \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_actualizado": "admin@example.com"
  }'
```

---

## Validación

### Checklist de Cambios
- [x] `cuentas_router.py` - 3 endpoints actualizados
- [x] `propietarios_router.py` - 2 endpoints actualizados
- [x] `miembros_router.py` - 1 endpoint actualizado
- [x] `residentes_router.py` - 1 endpoint + schema nuevo
- [x] `qr_router.py` - 2 endpoints actualizados (quitados "sistema")
- [x] `schemas.py` - Schema `AgregarFotoRequest` creado

**Total de endpoints modificados**: 9
**Valores quemados eliminados**: 6

---

## Beneficios

1. ✅ **Auditoría mejorada**: Cada acción registra quién la realizó
2. ✅ **Trazabilidad**: Se puede identificar exactamente quién ejecutó cada operación
3. ✅ **Flexibilidad**: Diferentes usuarios pueden realizar operaciones sin cambiar el código
4. ✅ **Seguridad**: No hay valores genéricos que oculten la identidad real del usuario
5. ✅ **Compliance**: Requisitos de auditoría más estrictos

---

## Notas Importantes

- El campo `usuario_creado` y `usuario_actualizado` debe contener la identidad del usuario que realiza la acción
- Para Firebase Auth, se recomienda usar el `firebase_uid` del usuario autenticado
- Los parámetros ahora son **obligatorios** (sin valores por defecto)
- Si se intenta llamar sin estos campos, la API devolverá error 422 (Unprocessable Entity)

