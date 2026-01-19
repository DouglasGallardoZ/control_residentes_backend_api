# TODOs Pendientes del Proyecto Backend API

## Resumen
Total de TODOs encontrados: **11**

---

## 1. QR Router (`app/interfaces/routers/qr_router.py`)
**Archivo:** [qr_router.py](app/interfaces/routers/qr_router.py)

### TODO 1.1 - Línea 57
**Descripción:** `Obtener vivienda del residente desde relación`
- **Ubicación:** Dentro de `generar_qr_propio()`
- **Contexto:** Actualmente hay un placeholder `vivienda_id = 1`
- **Acción requerida:** Obtener la vivienda desde la relación ResidenteVivienda usando usuario_id
- **Dependencia:** Requires usuario_id to be linked to a ResidenteVivienda

### TODO 1.2 - Línea 141
**Descripción:** `Obtener vivienda del residente desde relación`
- **Ubicación:** Dentro de `generar_qr_visita()`
- **Contexto:** Mismo placeholder que el anterior
- **Acción requerida:** Obtener la vivienda del residente desde ResidenteVivienda
- **Dependencia:** Requires usuario_id to be linked to a ResidenteVivienda

### TODO 1.3 - Línea 144
**Descripción:** `Registrar visita si no existe`
- **Ubicación:** Dentro de `generar_qr_visita()`
- **Contexto:** Después de validar el QR
- **Acción requerida:** Registrar entrada/salida en tabla de Acceso (visitas)
- **Dependencia:** Requires Acceso model properly configured

---

## 2. Cuentas Router (`app/interfaces/routers/cuentas_router.py`)
**Archivo:** [cuentas_router.py](app/interfaces/routers/cuentas_router.py)

### TODO 2.1 - Línea 65
**Descripción:** `Validar contraseña con política de seguridad`
- **Ubicación:** Dentro de `crear_cuenta()` 
- **Contexto:** Validación de passwords antes de almacenarlas
- **Acción requerida:** Implementar validación de:
  - Mínimo 8 caracteres
  - Al menos una mayúscula
  - Al menos un número
  - Al menos un carácter especial
- **Archivo sugerido:** `app/domain/validators.py` (CV-20: Validación de contraseña)

### TODO 2.2 - Línea 66
**Descripción:** `Validar reconocimiento facial`
- **Ubicación:** Dentro de `crear_cuenta()`
- **Contexto:** Antes de crear la cuenta
- **Acción requerida:** Integración con Firebase ML Kit o similar para validar biometría
- **Prioridad:** BAJA (Feature avanzada, puede implementarse después)

---

## 3. Residentes Router (`app/interfaces/routers/residentes_router.py`)
**Archivo:** [residentes_router.py](app/interfaces/routers/residentes_router.py)

### TODO 3.1 - Línea 41
**Descripción:** `Validar documento de autorización PDF`
- **Ubicación:** Dentro de `crear_residente()`
- **Contexto:** Validar que el PDF sea válido antes de almacenarlo
- **Acción requerida:** 
  - Validar que el archivo sea PDF
  - Validar tamaño máximo (ej: 5MB)
  - Validar que contenga datos legibles
- **Dependencia:** Requires file validation utilities

### TODO 3.2 - Línea 122
**Descripción:** `Desactivar automáticamente miembros de familia asociados`
- **Ubicación:** Dentro de `desactivar_residente()`
- **Contexto:** Cuando se desactiva un residente
- **Acción requerida:** 
  - Query MiembroVivienda donde persona_residente_fk = residente
  - Actualizar estado = 'inactivo' para todos esos miembros
- **Dependencia:** Requires proper relationship implementation

---

## 4. Servicios (`app/application/services/servicios.py`)
**Archivo:** [servicios.py](app/application/services/servicios.py)

### TODO 4.1 - Línea 115
**Descripción:** `Obtener tokens FCM de residentes desde tabla separada`
- **Ubicación:** Dentro de `notificar_residentes()`
- **Contexto:** Envío de notificaciones masivas
- **Acción requerida:**
  - Crear tabla DispositivoToken o ResidenteToken
  - Almacenar tokens FCM de dispositivos
  - Query tokens activos y enviar notificación
- **Dependencia:** Requires new database table

### TODO 4.2 - Línea 186
**Descripción:** `Obtener token FCM del usuario`
- **Ubicación:** Dentro de `notificar_usuario()`
- **Contexto:** Envío de notificación individual
- **Acción requerida:**
  - Obtener token FCM desde tabla DispositivoToken
  - Validar que el dispositivo esté activo
  - Enviar notificación individual
- **Dependencia:** Requires DispositivoToken table

### TODO 4.3 - Línea 215
**Descripción:** `Implementar bloqueo en cascada`
- **Ubicación:** Dentro de `bloquear_residente()`
- **Contexto:** Bloquear residente y cascada a miembros
- **Acción requerida:**
  - Al bloquear residente, bloquear todas sus Cuentas
  - Desactivar todos los MiembroVivienda asociados
  - Crear registro de auditoría
- **Dependencia:** Requires transaction management

### TODO 4.4 - Línea 225
**Descripción:** `Implementar desbloqueo en cascada`
- **Ubicación:** Dentro de `desbloquear_residente()`
- **Contexto:** Desbloquear residente y cascada a miembros
- **Acción requerida:**
  - Al desbloquear residente, reactivar Cuentas
  - Reactivar MiembroVivienda
  - Crear registro de auditoría
- **Dependencia:** Requires transaction management

---

## Plan de Implementación Recomendado

### Fase 1: CRÍTICA (Semana 1)
1. **TODO 1.1 & 1.2** - Obtener vivienda de residente
   - Impacta: QR generation (RF-Q01, RF-Q02)
   - Tiempo: 30 min
   
2. **TODO 3.2** - Desactivar miembros en cascada
   - Impacta: Residentes deactivation
   - Tiempo: 45 min

### Fase 2: ALTA PRIORIDAD (Semana 2)
1. **TODO 2.1** - Validación de contraseña
   - Impacta: Account security
   - Tiempo: 1 hora
   
2. **TODO 1.3** - Registrar visitas
   - Impacta: Access logging (RF-AQ)
   - Tiempo: 1.5 horas

### Fase 3: MEDIA PRIORIDAD (Semana 3)
1. **TODO 3.1** - Validar PDF
   - Impacta: File uploads
   - Tiempo: 1 hora
   
2. **TODO 4.1 & 4.2** - Sistema de notificaciones
   - Impacta: Push notifications
   - Tiempo: 3 horas
   - Requiere: Nueva tabla DispositivoToken

### Fase 4: BAJA PRIORIDAD (Post-MVP)
1. **TODO 2.2** - Reconocimiento facial
   - Impacta: Biometric authentication
   - Tiempo: 2-3 horas
   - Nota: Puede ser post-MVP

2. **TODO 4.3 & 4.4** - Bloqueo/Desbloqueo en cascada
   - Impacta: Account management
   - Tiempo: 2 horas
   - Nota: Puede optimizarse después

---

## Estimación Total
- **TODOs Críticos:** ~1.25 horas
- **TODOs Alta Prioridad:** ~2.5 horas
- **TODOs Media Prioridad:** ~4 horas
- **TODOs Baja Prioridad:** ~5 horas
- **TOTAL:** ~12.75 horas

---

## Checklist de Implementación

- [ ] TODO 1.1: Obtener vivienda en generar_qr_propio()
- [ ] TODO 1.2: Obtener vivienda en generar_qr_visita()
- [ ] TODO 1.3: Registrar visita en tabla Acceso
- [ ] TODO 2.1: Validación de contraseña (CV-20)
- [ ] TODO 2.2: Reconocimiento facial (FUTURO)
- [ ] TODO 3.1: Validar PDF en crear_residente()
- [ ] TODO 3.2: Desactivar miembros en cascada
- [ ] TODO 4.1: Obtener tokens FCM de residentes
- [ ] TODO 4.2: Obtener token FCM del usuario
- [ ] TODO 4.3: Bloqueo en cascada
- [ ] TODO 4.4: Desbloqueo en cascada

---

Última actualización: 19 de Enero, 2026
