# 🔍 ÍNDICE RÁPIDO: Requerimientos del Administrador

**Generado:** 21 de Enero de 2026

---

## 📊 Estado General

| Métrica | Valor |
|---------|-------|
| **Implementados** | 12/18 ✅ |
| **Porcentaje** | 67% |
| **Críticos faltantes** | 3 |
| **Con problemas** | 2 |

---

## 🔗 Enlaces a Documentación

### 📋 Documentos Principales

| Documento | Propósito | Audiencia |
|-----------|----------|-----------|
| [RESUMEN_EJECUTIVO_ADMIN.md](RESUMEN_EJECUTIVO_ADMIN.md) | Visión general ejecutiva | PMs, Líderes |
| [EVALUACION_ADMIN_REQUIREMENTS.md](EVALUACION_ADMIN_REQUIREMENTS.md) | Análisis detallado por RF | Developers, QA |
| [PLAN_ACCION_ADMIN_REQUIREMENTS.md](PLAN_ACCION_ADMIN_REQUIREMENTS.md) | Especificación de desarrollo | Developers |
| [VALIDACION_RFC_C05_C06.md](VALIDACION_RFC_C05_C06.md) | Análisis de cascada (bloqueo) | Developers, QA |

---

## 🎯 Requerimientos por Estado

### ✅ IMPLEMENTADOS (12)

#### Gestión de Cuentas (5/5)
- `RFC-C05` → `POST /api/v1/cuentas/{id}/bloquear` ⚠️ cascada?
- `RFC-C06` → `POST /api/v1/cuentas/{id}/desbloquear` ⚠️ cascada?
- `RFC-C07` → `POST /api/v1/cuentas/{id}/bloquear`
- `RFC-C08` → `POST /api/v1/cuentas/{id}/desbloquear`
- `RFC-C09` → `DELETE /api/v1/cuentas/{id}`

#### Gestión de Residentes (6/6)
- `RFC-R01` → `POST /api/v1/residentes`
- `RFC-R02` → `POST /api/v1/miembros/{residente_id}/agregar`
- `RFC-R03` → `POST /api/v1/residentes/{id}/desactivar`
- `RFC-R04` → `POST /api/v1/miembros/{id}/desactivar`
- `RFC-R05` → `POST /api/v1/residentes/{id}/reactivar`
- `RFC-R06` → `POST /api/v1/miembros/{id}/reactivar`

#### Gestión de Propietarios (2/5)
- `RFC-P01` → `POST /api/v1/propietarios`
- `RFC-P02` → `POST /api/v1/propietarios/{id}/conyuge`

---

### ❌ NO IMPLEMENTADOS (6)

#### Gestión de Propietarios (3)
- `RFC-P03` → `PUT /api/v1/propietarios/{id}` **FALTA**
  - Actualizar: email, celular, fotos, dirección alternativa
  - Prioridad: MEDIA
  
- `RFC-P04` → `POST /api/v1/propietarios/{id}/baja` **FALTA**
  - Cambiar estado a "inactivo" + cónyuge
  - Prioridad: ALTA
  
- `RFC-P05` → `POST /api/v1/propietarios/cambio-propiedad` **FALTA**
  - Transferencia completa de propiedad + residente
  - Prioridad: ALTA

#### Notificaciones (4) - Router Completo FALTA
- `RFC-N01` → `POST /api/v1/notificaciones/masivas/residentes` **FALTA**
- `RFC-N02` → `POST /api/v1/notificaciones/masivas/propietarios` **FALTA**
- `RFC-N03` → `POST /api/v1/notificaciones/individual/residente/{id}` **FALTA**
- `RFC-N04` → `POST /api/v1/notificaciones/individual/propietario/{id}` **FALTA**

---

### ⚠️ CON PROBLEMAS (2)

#### RFC-C05: Bloquear Cuentas en Cascada
- **Endpoint actual:** `POST /api/v1/cuentas/{id}/bloquear`
- **Problema:** Solo bloquea la cuenta individual, NO los miembros de familia
- **Requerimiento:** Cuando se bloquea residente → también bloquear miembros
- **Solución:** Ver [VALIDACION_RFC_C05_C06.md](VALIDACION_RFC_C05_C06.md)
- **Tiempo estimado:** 2-3 horas

#### RFC-C06: Desbloquear Cuentas en Cascada
- **Endpoint actual:** `POST /api/v1/cuentas/{id}/desbloquear`
- **Problema:** Solo desbloquea la cuenta individual, NO los miembros de familia
- **Requerimiento:** Cuando se desbloquea residente → también desbloquear miembros
- **Solución:** Ver [VALIDACION_RFC_C05_C06.md](VALIDACION_RFC_C05_C06.md)
- **Tiempo estimado:** 2-3 horas

---

## 📈 Cobertura por Módulo

```
Gestión de Cuentas:      ████████████████████ 100% (5/5)
Gestión de Residentes:   ████████████████████ 100% (6/6)
Gestión de Propietarios: ████░░░░░░░░░░░░░░░  40% (2/5)
Notificaciones:          ░░░░░░░░░░░░░░░░░░░░  0% (0/4)
─────────────────────────────────────────────────────
TOTAL:                   ██████████░░░░░░░░░░  67% (12/18)
```

---

## 🚀 Plan de Acción Resumido

### FASE 1: Correcciones Urgentes (1-2 días)
- [ ] Validar y corregir cascada RFC-C05/C06

### FASE 2: Endpoints Críticos (2-3 días)
- [ ] Implementar RFC-P04: Baja de propietario
- [ ] Implementar RFC-P05: Cambio de propietario
- [ ] Implementar RFC-P03: Actualizar información

### FASE 3: Módulo de Notificaciones (2-3 días)
- [ ] Crear `notificaciones_router.py`
- [ ] Implementar RFC-N01 a RFC-N04
- [ ] Integrar FCM

### FASE 4: Validación (1-2 días)
- [ ] Test unitarios
- [ ] Test end-to-end
- [ ] Actualizar documentación

**Total estimado:** 1-2 semanas

---

## 📋 Checklist para Developers

### Antes de comenzar:
- [ ] Revisar [EVALUACION_ADMIN_REQUIREMENTS.md](EVALUACION_ADMIN_REQUIREMENTS.md)
- [ ] Leer [PLAN_ACCION_ADMIN_REQUIREMENTS.md](PLAN_ACCION_ADMIN_REQUIREMENTS.md)
- [ ] Revisar [VALIDACION_RFC_C05_C06.md](VALIDACION_RFC_C05_C06.md) si trabajarás en C05/C06

### Para cada RF a implementar:
- [ ] Crear schema en `schemas.py`
- [ ] Crear endpoint en router correspondiente
- [ ] Implementar validaciones según CV-*
- [ ] Crear test unitario
- [ ] Documentar en API_DOCUMENTACION_COMPLETA.md
- [ ] Ejecutar `get_errors` para validar sintaxis

### Al terminar:
- [ ] Actualizar README.md
- [ ] Actualizar CHANGELOG.md
- [ ] Actualizar este archivo

---

## 🔍 Búsqueda Rápida

**¿Qué endpoint debería implementar primero?**
→ RFC-P04 (Baja de propietario) - Ver página 3

**¿Cuál es el problema con bloqueo/desbloqueo?**
→ Revisar VALIDACION_RFC_C05_C06.md

**¿Cuántos endpoints faltan?**
→ 7 endpoints (3 de propietarios + 4 de notificaciones)

**¿Cuál es el impacto total?**
→ 33% de funcionalidades de administrador faltan - Ver RESUMEN_EJECUTIVO_ADMIN.md

---

## 📌 Notas Importantes

1. ⚠️ RFC-C05 y RFC-C06 están "implementadas" pero SIN cascada - Revisar VALIDACION_RFC_C05_C06.md
2. 📁 No existe router `notificaciones_router.py` - Crear desde cero
3. 🔄 RFC-R03 (desactivar residente) SÍ tiene cascada a miembros ✓
4. 📊 La cobertura es 67% a nivel de endpoints, pero algunos están incompletos
5. 🎯 Prioridad: P04 > P05 > Notificaciones > P03

---

## 📞 Referencias Rápidas

| Necesidad | Archivo |
|-----------|---------|
| Ver pseudocódigo de P04 | PLAN_ACCION_ADMIN_REQUIREMENTS.md#rf-p04 |
| Ver pseudocódigo de P05 | PLAN_ACCION_ADMIN_REQUIREMENTS.md#rf-p05 |
| Ver pseudocódigo de cascada | VALIDACION_RFC_C05_C06.md |
| Ver especificación de N01-N04 | PLAN_ACCION_ADMIN_REQUIREMENTS.md#notificaciones |
| Ver matriz completa | EVALUACION_ADMIN_REQUIREMENTS.md |

---

*Última actualización: 21 de Enero de 2026*

