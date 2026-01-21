# 🎯 PLAN DE ACCIÓN: Completar Requerimientos del Administrador

## Fase 1: Críticos - Endpoints de Propietarios Faltantes

### 1. RF-P03: Actualización de información del propietario

**Endpoint:** `PUT /api/v1/propietarios/{propietario_id}`

**Campos actualizables:**
- Email (correo_electronico)
- Celular (numero_celular)
- Fotografías de rostro
- Dirección alternativa (opcional)

**Campos NO modificables:**
- Identificación
- Nombres y apellidos
- Manzana y villa
- Estado de propiedad

**Validaciones:**
- El propietario debe existir y estar activo
- Email debe ser válido (CV-06)
- Celular ecuatoriano: 09XXXXXXXX (CV-05)
- Fotografías deben ser JPG/PNG con distinta resolución

---

### 2. RF-P04: Baja de propietario

**Endpoint:** `POST /api/v1/propietarios/{propietario_id}/baja`

**Lógica:**
1. Validar que propietario existe y está activo
2. Cambiar campo `estado` a "inactivo" (NO eliminar)
3. **Cambiar estado del cónyuge a "inactivo"** (si existe)
4. Registrar motivo en auditoría
5. Retornar confirmación

**Request Body:**
```json
{
  "motivo": "Cambio de domicilio",
  "usuario_actualizado": "admin_001"
}
```

**Response:**
```json
{
  "mensaje": "Propietario dado de baja correctamente",
  "propietario_id": 5,
  "conyuge_procesado": true
}
```

---

### 3. RF-P05: Cambio de propietario de vivienda

**Endpoint:** `POST /api/v1/propietarios/cambio-propiedad`

**Proceso completo:**
1. Obtener propietario actual y validar que existe
2. Dar de baja al propietario actual (cambiar a inactivo)
3. Registrar o activar nuevo propietario
4. Actualizar relación vivienda ↔ propietario
5. **Si el residente actual ES el propietario:**
   - Registrar automáticamente al nuevo propietario como residente activo
6. Registrar en auditoría
7. Retornar confirmación

**Request Body:**
```json
{
  "vivienda_id": 1,
  "nuevo_propietario_id": 15,
  "motivo_cambio": "Venta de propiedad",
  "usuario_actualizado": "admin_001"
}
```

**Response:**
```json
{
  "mensaje": "Cambio de propietario realizado correctamente",
  "vivienda_id": 1,
  "propietario_anterior_id": 5,
  "propietario_nuevo_id": 15,
  "residente_actualizado": true,
  "propietario_como_residente": true
}
```

---

## Fase 2: Notificaciones - Nuevo Router

### Router: `notificaciones_router.py`

**Prefijo:** `/api/v1/notificaciones`  
**Tags:** ["Notificaciones"]

### 1. RF-N01: Notificaciones masivas a residentes

**Endpoint:** `POST /masivas/residentes`

```python
@router.post("/masivas/residentes", response_model=dict)
def enviar_notificacion_masiva_residentes(
    request: NotificacionMasivaRequest,  # { titulo, cuerpo, usuario_creado }
    db: Session = Depends(get_db)
):
    """
    Envía notificación push a TODOS los residentes activos
    RF-N01
    """
    # Lógica:
    # 1. Obtener todos los residentes con estado='activo'
    # 2. Obtener sus cuentas
    # 3. Enviar FCM push a cada uno
    # 4. Registrar en tabla notificacion
    # 5. Retornar count de enviadas
```

### 2. RF-N02: Notificaciones masivas a propietarios

**Endpoint:** `POST /masivas/propietarios`

```python
@router.post("/masivas/propietarios", response_model=dict)
def enviar_notificacion_masiva_propietarios(
    request: NotificacionMasivaRequest,
    db: Session = Depends(get_db)
):
    """
    Envía notificación push a TODOS los propietarios activos
    RF-N02
    """
```

### 3. RF-N03: Notificación individual a residente

**Endpoint:** `POST /individual/residente/{residente_id}`

```python
@router.post("/individual/residente/{residente_id}", response_model=dict)
def enviar_notificacion_residente(
    residente_id: int,
    request: NotificacionIndividualRequest,  # { titulo, cuerpo, usuario_creado }
    db: Session = Depends(get_db)
):
    """
    Envía notificación push a un residente específico
    RF-N03
    """
```

### 4. RF-N04: Notificación individual a propietario

**Endpoint:** `POST /individual/propietario/{propietario_id}`

```python
@router.post("/individual/propietario/{propietario_id}", response_model=dict)
def enviar_notificacion_propietario(
    propietario_id: int,
    request: NotificacionIndividualRequest,
    db: Session = Depends(get_db)
):
    """
    Envía notificación push a un propietario específico
    RF-N04
    """
```

---

## Validaciones Necesarias

### RF-C05/C06: Verificar Cascada

**Ubicación:** `app/interfaces/routers/cuentas_router.py`

**Validación requerida:**
```python
# Cuando se bloquea una cuenta de residente:
# 1. Bloquear la cuenta del residente
# 2. Obtener todos los miembros de esa vivienda
# 3. Bloquear cuentas de cada miembro
# 4. Registrar auditoría

# Cuando se desbloquea una cuenta de residente:
# 1. Desbloquear la cuenta del residente
# 2. Obtener todos los miembros de esa vivienda
# 3. Desbloquear cuentas de cada miembro
# 4. Registrar auditoría
```

---

## Tablas de Base de Datos Necesarias

### Para Notificaciones (si no existen):

```sql
-- Si no existe
CREATE TABLE IF NOT EXISTS notificacion (
    notificacion_pk SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    cuerpo TEXT NOT NULL,
    tipo_destinatario VARCHAR(50),  -- 'residentes' | 'propietarios' | 'individual'
    estado VARCHAR(50),  -- 'enviada' | 'pendiente' | 'fallida'
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(100),
    eliminado BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS notificacion_destino (
    notificacion_destino_pk SERIAL PRIMARY KEY,
    notificacion_fk INTEGER NOT NULL REFERENCES notificacion(notificacion_pk),
    cuenta_fk INTEGER NOT NULL REFERENCES cuenta(cuenta_pk),
    estado_envio VARCHAR(50),  -- 'enviado' | 'fallido' | 'no_leido'
    fecha_envio TIMESTAMP,
    fecha_lectura TIMESTAMP,
    eliminado BOOLEAN DEFAULT FALSE
);
```

---

## Esquema de Implementación Recomendado

### Sprint 1: Propietarios (2-3 días)
- [ ] Implementar RF-P03 (PUT /propietarios/{id})
- [ ] Implementar RF-P04 (POST /propietarios/{id}/baja)
- [ ] Implementar RF-P05 (POST /propietarios/cambio-propiedad)
- [ ] Validar RF-C05/C06 cascada
- [ ] Crear test unitarios

### Sprint 2: Notificaciones (2-3 días)
- [ ] Crear router `notificaciones_router.py`
- [ ] Crear schemas `NotificacionMasivaRequest`, `NotificacionIndividualRequest`
- [ ] Implementar RF-N01 a RF-N04
- [ ] Integrar con FCM
- [ ] Crear test unitarios

### Sprint 3: Integración y validación (1-2 días)
- [ ] Integrar nuevos routers a main.py
- [ ] Actualizar API_DOCUMENTACION_COMPLETA.md
- [ ] Test end-to-end
- [ ] Actualizar README.md

---

## Criterios de Aceptación

### RF-P03
- ✅ Permite actualizar email, celular, fotos
- ✅ NO permite modificar identificación/nombres/villa/manzana
- ✅ Valida email y celular
- ✅ Retorna error si propietario no existe

### RF-P04
- ✅ Cambia estado a "inactivo" (NO elimina)
- ✅ Requiere motivo
- ✅ Procesa baja del cónyuge si existe
- ✅ Registra auditoría

### RF-P05
- ✅ Desactiva propietario anterior
- ✅ Activa nuevo propietario
- ✅ Si residente = propietario, registra nuevo como residente
- ✅ Retorna confirmación con todos los datos

### RF-N01 a N04
- ✅ Envía FCM push correctamente
- ✅ Registra en tabla notificacion
- ✅ Retorna count de enviadas/fallidas
- ✅ Valida destinatarios

