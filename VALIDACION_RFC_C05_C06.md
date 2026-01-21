# ⚠️ VALIDACIÓN CRÍTICA: RF-C05 y RF-C06 - Cascada de Bloqueo/Desbloqueo

**Fecha:** 21 de Enero de 2026  
**Estado:** ❌ **INCOMPLETO - REQUIERE IMPLEMENTACIÓN**

---

## 📋 Requerimiento

### RF-C05: Bloquear Cuentas de Residente y Miembros de Familia
**"Permite bloquear las cuentas de un residente y todos sus miembros de familia"**

### RF-C06: Desbloquear Cuentas de Residente y Miembros de Familia
**"Permite desbloquear las cuentas de un residente y sus miembros de familia"**

---

## 🔍 Análisis Actual

### Código Actual (cuentas_router.py, líneas 216-328)

```python
@router.post("/{cuenta_id}/bloquear", response_model=dict)
def bloquear_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,
    motivo: str = "Cuenta bloqueada",
    db: Session = Depends(get_db)
):
    """
    Bloquea una cuenta individual
    RF-C07  # ← Esto es RFC-07, NO RF-C05
    """
    # ... código que bloquea SOLO la cuenta_id proporcionada
    
    cuenta.estado = "inactivo"  # ← Solo afecta a UNA cuenta
    db.commit()
```

### Problema Identificado

1. ❌ **El endpoint bloquea SOLO la cuenta individual**
   - Debería bloquear la cuenta del residente AND las cuentas de sus miembros

2. ❌ **No existe lógica para detectar si es residente**
   - Debería verificar si `persona_titular_fk` es residente activo

3. ❌ **No existe lógica para obtener miembros asociados**
   - Debería consultar tabla `MiembroVivienda` para encontrar miembros de esa vivienda

4. ❌ **No existe lógica cascada de bloqueo**
   - Debería bloquear la cuenta de cada miembro encontrado

---

## 📝 Especificación de Cascada (RFC-C05 / RFC-C06)

### Flujo esperado para BLOQUEAR (RFC-C05):

```
Usuario Admin → POST /cuentas/{cuenta_id}/bloquear
                        ↓
            Obtener cuenta desde account_pk
                        ↓
            Obtener persona_titular_fk de esa cuenta
                        ↓
            Verificar si esa persona es RESIDENTE
                        ↓
            ┌─ SI ES RESIDENTE:
            │   ├─ Obtener vivienda_reside_fk
            │   ├─ Obtener todos los MIEMBROS de esa vivienda
            │   ├─ Bloquear cuenta del residente
            │   └─ FOR EACH miembro:
            │       ├─ Obtener su cuenta
            │       ├─ Bloquear cuenta del miembro
            │       └─ Registrar evento
            │
            └─ NO ES RESIDENTE (es miembro):
                └─ Bloquear SOLO su cuenta (no hay cascada hacia arriba)
```

### Datos necesarios:

```python
# Estructura de relaciones:
Persona → Cuenta (relación 1:1)
Persona → ResidenteVivienda (persona_residente_fk)
ResidenteVivienda → Vivienda (vivienda_reside_fk)
Vivienda → MiembroVivienda (vivienda_familia_fk)
MiembroVivienda → Persona (persona_miembro_fk)
Persona → Cuenta (2ª Persona)
```

---

## 🛠️ Implementación Requerida

### Pseudocódigo de solución:

```python
@router.post("/{cuenta_id}/bloquear", response_model=dict)
def bloquear_cuenta(
    cuenta_id: int,
    usuario_actualizado: str,
    motivo: str = "Cuenta bloqueada",
    db: Session = Depends(get_db)
):
    """
    Bloquea una cuenta individual o (si es residente) 
    bloquea también a todos sus miembros de familia
    RFC-C05 / RFC-C07
    """
    try:
        # 1. Obtener cuenta principal
        cuenta_principal = db.query(Cuenta).filter(
            Cuenta.cuenta_pk == cuenta_id
        ).first()
        
        if not cuenta_principal:
            raise HTTPException(404, "Cuenta no encontrada")
        
        # 2. Obtener persona titular de esa cuenta
        persona = db.query(Persona).filter(
            Persona.persona_pk == cuenta_principal.persona_titular_fk
        ).first()
        
        # 3. Verificar si es RESIDENTE
        residente = db.query(ResidenteVivienda).filter(
            ResidenteVivienda.persona_residente_fk == persona.persona_pk,
            ResidenteVivienda.estado == "activo"
        ).first()
        
        cuentas_a_bloquear = [cuenta_principal]  # Siempre bloquear su cuenta
        vivienda_id = None
        
        # 4. Si es residente, obtener vivienda y miembros
        if residente:
            vivienda_id = residente.vivienda_reside_fk
            
            # Obtener todos los miembros de esa vivienda
            miembros = db.query(MiembroVivienda).filter(
                MiembroVivienda.vivienda_familia_fk == vivienda_id,
                MiembroVivienda.estado == "activo"
            ).all()
            
            # Obtener cuentas de cada miembro
            for miembro in miembros:
                cuenta_miembro = db.query(Cuenta).filter(
                    Cuenta.persona_titular_fk == miembro.persona_miembro_fk
                ).first()
                
                if cuenta_miembro:
                    cuentas_a_bloquear.append(cuenta_miembro)
        
        # 5. Bloquear todas las cuentas
        for cuenta in cuentas_a_bloquear:
            cuenta.estado = "inactivo"
            cuenta.fecha_actualizado = ahora_sin_tz()
            cuenta.usuario_actualizado = usuario_actualizado
            
            evento = EventoCuenta(
                cuenta_afectada_fk=cuenta.cuenta_pk,
                tipo_evento="cuenta_bloqueada",
                motivo=motivo,
                usuario_creado=usuario_actualizado
            )
            db.add(evento)
        
        db.commit()
        
        return {
            "mensaje": f"Se han bloqueado {len(cuentas_a_bloquear)} cuenta(s)",
            "cuentas_bloqueadas": len(cuentas_a_bloquear),
            "cuenta_principal_id": cuenta_id,
            "es_residente": residente is not None,
            "vivienda_id": vivienda_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
```

---

## ✅ Checklist de Validación

### Para RFC-C05 (Bloquear):
- [ ] Obtiene cuenta principal desde cuenta_id
- [ ] Obtiene persona titular de esa cuenta
- [ ] Verifica si persona es residente activo
- [ ] Si es residente:
  - [ ] Obtiene vivienda_reside_fk
  - [ ] Obtiene todos los miembros activos de esa vivienda
  - [ ] Obtiene cuenta de cada miembro
  - [ ] Bloquea cuenta de cada miembro
- [ ] Bloquea cuenta principal
- [ ] Registra evento para cada cuenta bloqueada
- [ ] Retorna confirmación con count de cuentas bloqueadas
- [ ] Si NO es residente:
  - [ ] Bloquea SOLO su cuenta (sin cascada)

### Para RFC-C06 (Desbloquear):
- [ ] Exactamente lo mismo que RFC-C05 pero cambiar `estado` a "activo"

---

## 📊 Diferencia entre RFC-C05, RFC-C07, RFC-C08

| RFC | Scope | Cascada | Implementación Actual |
|-----|-------|---------|----------------------|
| **RFC-C05** | Residente + Miembros | ✅ SÍ (cascada) | ❌ NO - Solo residente |
| **RFC-C06** | Residente + Miembros | ✅ SÍ (cascada) | ❌ NO - Solo residente |
| **RFC-C07** | Individual | ❌ NO | ✅ OK - Bloquea solo a la persona |
| **RFC-C08** | Individual | ❌ NO | ✅ OK - Desbloquea solo a la persona |

---

## 🚀 Plan de Corrección

### Opción A: Crear 2 nuevos endpoints (Recomendado)

```
POST /api/v1/cuentas/{residente_id}/bloquear-cascada     (RFC-C05)
POST /api/v1/cuentas/{residente_id}/desbloquear-cascada  (RFC-C06)
```

**Ventajas:**
- Endpoint específico para cascada (más claro)
- No afecta RFC-C07 y RFC-C08
- Requiere validar que es residente en el path

**Desventajas:**
- Más endpoints

### Opción B: Refactorizar endpoints existentes (Actual)

```
POST /api/v1/cuentas/{cuenta_id}/bloquear     
    → Detectar si es residente
    → Si SÍ: cascada a miembros
    → Si NO: solo cuenta individual
```

**Ventajas:**
- Menos endpoints
- Lógica integrada

**Desventajas:**
- Comportamiento variable según rol
- Puede ser confuso

---

## ⏱️ Estimación de Implementación

- **Análisis:** 1 hora ✅ (completado)
- **Desarrollo:** 2-3 horas
- **Testing:** 1 hora
- **Total:** 3-4 horas

---

## 📌 Conclusión

**Estado actual:** ⚠️ **RFC-C05 y RFC-C06 NO están correctamente implementados**

Los endpoints actuales (`bloquear` y `desbloquear`) solo afectan a la cuenta individual, sin cascada a miembros de familia. 

**Acción requerida:** 
1. Actualizar lógica de `bloquear_cuenta()` y `desbloquear_cuenta()` 
2. Implementar detección de residente
3. Implementar lógica cascada de obtención y bloqueo/desbloqueo de miembros
4. Crear test unitarios para ambas cascadas

