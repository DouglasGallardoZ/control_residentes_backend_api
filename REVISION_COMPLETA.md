# Revisión Completa: TODOs y Valores Hardcodeados

**Fecha de Revisión**: 2024
**Estado**: Auditoría completada

---

## 1. Valores Hardcodeados - ESTADO ACTUAL

### ✅ YA RESUELTOS
| Archivo | Línea | Valor | Solución | Estado |
|---------|-------|-------|----------|--------|
| qr_router.py | 58 | `vivienda_id = 2` | Query a ResidenteVivienda | ✅ FIXED |
| qr_router.py | 72 | `usuario_creado="sistema"` | Usa `cuenta.firebase_uid` | ✅ FIXED |
| qr_router.py | 142 | `vivienda_id = 2` | Query a ResidenteVivienda | ✅ FIXED |
| qr_router.py | 160 | `usuario_creado="sistema"` | Usa `cuenta.firebase_uid` | ✅ FIXED |
| residentes_router.py | 228 | `usuario_creado="api_user"` | Usa `request.usuario_creado` | ✅ FIXED |

### ⚠️ VALORES DE CONFIGURACIÓN (No son hardcoded problemáticos)

Estos son constantes legítimas definidas en esquemas/models:

```python
# app/domain/entities/models.py - Constantes válidas
nacionalidad: str = "Ecuador"  # Default para nueva Persona

# app/interfaces/schemas/schemas.py - Default en schema
nacionalidad: str = "Ecuador"

# app/interfaces/routers/cuentas_router.py - Default en schema
usuario_creado: str = "api_user"  # Aunque esto debería revisarse según contexto

# Estados válidos (enums, no hardcoded problemáticos)
ACTIVO = "activo"
INACTIVO = "inactivo"
```

**Conclusión**: No hay valores literales hardcodeados problemáticos activos en ejecución.

---

## 2. TODOs Pendientes - Listado Completo

### 🔴 CRÍTICA (Bloquean funcionalidad MVP)
Tiempo estimado: **2.5 horas**

#### TODO 1.3: Registrar visita en tabla Acceso (RF-AQ01)
- **Archivo**: [qr_router.py](qr_router.py#L166)
- **Línea**: 166
- **Descripción**: Después de generar QR para visita, registrar en tabla `acceso`
- **Contexto**: `generar_qr_visita()` endpoint
- **Requerimiento**: RF-AQ01 - Registrar acceso de visitante
- **Implementación necesaria**:
  ```python
  # Después de crear QR vigente
  acceso = Acceso(
      qr_fk=qr_vigente.qr_id,
      resultado="vigente",
      dispositivo="API",
      usuario_creado=cuenta.firebase_uid
  )
  db.add(acceso)
  db.commit()
  ```
- **Impacto**: Sin esto, el sistema no registra intentos de acceso de visitantes
- **Status**: ⏳ PENDING

#### TODO 3.2: Desactivar automáticamente miembros de familia (RF-R05)
- **Archivo**: [residentes_router.py](residentes_router.py#L122)
- **Línea**: 122
- **Descripción**: Cuando se desactiva un residente, desactivar todos sus miembros de familia
- **Contexto**: `desactivar_residente()` endpoint
- **Requerimiento**: RF-R05 - Gestión de miembros en cascada
- **Implementación necesaria**:
  ```python
  # Cuando residente.estado = "inactivo"
  miembros = db.query(MiembroVivienda).filter(
      MiembroVivienda.persona_residente_fk == residente.persona_residente_fk,
      MiembroVivienda.estado == "activo"
  ).all()
  
  for miembro in miembros:
      miembro.estado = "inactivo"
      miembro.fecha_actualizacion = datetime.now()
  
  db.commit()
  ```
- **Impacto**: Si falta, quedarán miembros activos sin residente titular
- **Status**: ⏳ PENDING

### 🟡 ALTA (Funcionalidad importante)
Tiempo estimado: **2 horas**

#### TODO 3.1: Validar documento de autorización PDF (RF-R01)
- **Archivo**: [residentes_router.py](residentes_router.py#L41)
- **Línea**: 41
- **Descripción**: Cuando se agrega residente, validar que PDF de autorización sea válido
- **Contexto**: `agregar_residente()` endpoint
- **Requerimiento**: RF-R01 - Registro de residentes con documentación
- **Validación necesaria**:
  - Verificar que PDF existe y es válido
  - Posiblemente usar servicio OCR para validar contenido
  - Guardar hash del PDF para auditoría
- **Status**: ⏳ PENDING

#### TODO 2.1: Validar password según política (REMOVIDO - Migrado a Firebase)
- **Archivo**: ~~cuentas_router.py~~ (Removido)
- **Estado**: ✅ RESUELTO (Firebase maneja autenticación)

### 🟠 MEDIA (Funcionalidad complementaria)
Tiempo estimado: **3 horas**

#### TODO 4.1: Obtener tokens FCM para notificación masiva (RF-N01)
- **Archivo**: [servicios.py](servicios.py#L115)
- **Línea**: 115-116
- **Descripción**: `notificar_todos_residentes()` ahora retorna lista vacía
- **Contexto**:
  ```python
  tokens = []  # Placeholder - TODO: Obtener desde tabla
  ```
- **Implementación necesaria**:
  ```python
  tokens = db.query(NotificacionDestino.token_fcm).filter(
      NotificacionDestino.estado == "activo",
      NotificacionDestino.dispositivo == "mobile"
  ).all()
  tokens = [t[0] for t in tokens]
  ```
- **Impacto**: Notificaciones push no se envían
- **Status**: ⏳ PENDING

#### TODO 4.2: Obtener token FCM del usuario individual (RF-N02)
- **Archivo**: [servicios.py](servicios.py#L186)
- **Línea**: 186
- **Descripción**: `notificar_usuario()` no obtiene token del destinatario
- **Contexto**: Método para enviar notificación a usuario específico
- **Implementación necesaria**:
  ```python
  token = db.query(NotificacionDestino.token_fcm).filter(
      NotificacionDestino.cuenta_fk == cuenta_id,
      NotificacionDestino.estado == "activo"
  ).first()
  
  if token:
      self.fcm.enviar_notificacion(token[0], titulo, mensaje)
  ```
- **Status**: ⏳ PENDING

### 🔵 BAJA (Post-MVP, Nice to have)
Tiempo estimado: **2.5 horas**

#### TODO 2.2: Facial recognition para autenticación (RF-C02)
- **Archivo**: [cuentas_router.py](cuentas_router.py)
- **Descripción**: Integrar reconocimiento facial como factor de autenticación
- **Requerimiento**: RF-C02 - Autenticación biométrica (POST-MVP)
- **Contexto**: Esta es una feature futura, no bloqueante
- **Status**: 🔮 POST-MVP

#### TODO 4.3: Implementar bloqueo en cascada (RF-C07 extend)
- **Archivo**: [servicios.py](servicios.py#L215)
- **Línea**: 215
- **Descripción**: `bloquear_cuenta_residente()` no bloquea miembros asociados
- **Contexto**: Cuando se bloquea titular, deben bloquearse miembros
- **Implementación necesaria**:
  ```python
  # Bloquear miembros del residente
  miembros = db.query(MiembroVivienda).filter(
      MiembroVivienda.persona_residente_fk == residente.persona_residente_fk
  ).all()
  
  for miembro in miembros:
      cuenta_miembro = db.query(Cuenta).filter(
          Cuenta.persona_titular_fk == miembro.persona_miembro_fk
      ).first()
      if cuenta_miembro:
          cuenta_miembro.estado = "bloqueado"
  ```
- **Status**: ⏳ PENDING

#### TODO 4.4: Implementar desbloqueo en cascada (RF-C08 extend)
- **Archivo**: [servicios.py](servicios.py#L225)
- **Línea**: 225
- **Descripción**: `desbloquear_cuenta_residente()` no desbloquea miembros asociados
- **Contexto**: Similar a bloqueo en cascada
- **Status**: ⏳ PENDING

---

## 3. Placeholders en Código

### ⚠️ Placeholders Legítimos
```python
# app/infrastructure/security/firebase_auth.py:15
"""Placeholder para Firebase Auth"""
# Línea 24: # Placeholder - implementar con firebase_admin

# app/application/services/servicios.py:116
tokens = []  # Placeholder
```

**Estado**: Estos son placeholders esperados que se llenarán con la integración de Firebase y FCM.

---

## 4. Matriz de Riesgo

| TODO | Criticidad | Riesgo | Impacto Usuarios | Tiempo |
|------|-----------|--------|-----------------|--------|
| 1.3 Acceso tabla | 🔴 CRÍTICA | Alto | No se registran intentos de acceso | 1.0h |
| 3.2 Cascada miembros | 🔴 CRÍTICA | Alto | Miembros quedan activos sin residente | 1.5h |
| 3.1 Validar PDF | 🟡 ALTA | Medio | Residentes sin documentación válida | 1.5h |
| 4.1 FCM masivo | 🟠 MEDIA | Bajo | Notificaciones no llegan | 1.5h |
| 4.2 FCM individual | 🟠 MEDIA | Bajo | Notificaciones no llegan | 1.0h |
| 4.3 Bloqueo cascada | 🟠 MEDIA | Bajo | Miembros pueden acceder si titular bloqueado | 1.0h |
| 4.4 Desbloqueo cascada | 🟠 MEDIA | Bajo | Miembros siguen bloqueados si titular desbloqueado | 0.5h |

---

## 5. Resumen de Acciones

### Completadas ✅
- [x] Removidos hardcoded values de qr_router.py (vivienda_id, usuario_creado)
- [x] Removido hardcoded value de residentes_router.py (usuario_creado)
- [x] Identificados todos los TODOs en el proyecto (11 totales)
- [x] Documentados con contexto y requerimientos

### Pendientes ⏳
- [ ] Implementar TODO 1.3 (Acceso/Visitas)
- [ ] Implementar TODO 3.2 (Cascada miembros)
- [ ] Implementar TODO 3.1 (Validación PDF)
- [ ] Implementar TODO 4.1-4.2 (Notificaciones FCM)
- [ ] Implementar TODO 4.3-4.4 (Bloqueos en cascada)

---

## 6. Próximos Pasos Recomendados

1. **Inmediato**: Implementar TODO 1.3 (registrar en tabla Acceso) - bloquea acceso
2. **Después**: Implementar TODO 3.2 (cascada miembros) - validación de datos
3. **Siguiente**: Crear accesos_router.py con endpoints para RF-AQ01 a RF-AQ07
4. **Luego**: Integrar FCM para notificaciones (TODO 4.1-4.2)
5. **Final**: Completar cascadas de bloqueo/desbloqueo (TODO 4.3-4.4)

---

## 7. Referencias de Código

- [esquema.sql](esquema.sql) - Definición de tablas
- [models.py](app/infrastructure/db/models.py) - Modelos SQLAlchemy
- [qr_router.py](app/interfaces/routers/qr_router.py) - Endpoints de QR
- [residentes_router.py](app/interfaces/routers/residentes_router.py) - Endpoints de residentes
- [servicios.py](app/application/services/servicios.py) - Lógica de negocio
- [firebase_auth.py](app/infrastructure/security/firebase_auth.py) - Autenticación Firebase

