# 🔄 Control de Duplicados - Visitantes QR

## Cambio Implementado

Se agregó un **control de duplicados** en el endpoint `POST /qr/generar-visita` para evitar registrar múltiples veces al mismo visitante en la tabla `visita`.

---

## 🎯 Comportamiento

### Antes (Antiguo)
```
Cada vez que se genera QR para una visita:
  → Siempre crea un nuevo registro en tabla visita
  → Posibles duplicados de visitantes
  ❌ Registro sucio: mismo visitante múltiples veces
```

### Ahora (Nuevo)
```
Cada vez que se genera QR para una visita:
  1. Busca si visitante con esa IDENTIFICACIÓN ya existe en esa vivienda
  2. Si EXISTE:
     → Reutiliza ese registro visita
     → No crea duplicado
     → Retorna: es_visitante_nuevo = false
  3. Si NO EXISTE:
     → Crea nuevo registro visita
     → Retorna: es_visitante_nuevo = true
     
✅ Registro limpio: un visitante = un registro
```

---

## 📝 Código Implementado

### Búsqueda de Duplicado

```python
# Verificar si ya existe un visitante con la misma identificación en esta vivienda
visita_existente = db.query(VisitaModel).filter(
    VisitaModel.vivienda_visita_fk == vivienda_id,
    VisitaModel.identificacion == request.visita_identificacion,
    VisitaModel.eliminado == False
).first()
```

### Lógica Condicional

```python
if visita_existente:
    # Reutilizar el registro existente
    visita_id = visita_existente.visita_pk
else:
    # Crear nuevo registro de visita
    visita = VisitaModel(...)
    db.add(visita)
    db.flush()
    visita_id = visita.visita_pk
```

### Respuesta Indicativa

```python
# Determinar si la visita fue nueva o reutilizada
mensaje_visita = "Visitante reutilizado" if visita_existente else "Nuevo visitante registrado"

return {
    "id": qr.qr_pk,
    "token": token,
    "hora_inicio": dt_inicio.isoformat(),
    "hora_fin": hora_fin.isoformat(),
    "estado": "vigente",
    "visita_id": visita_id,
    "mensaje": f"Código QR para visita generado correctamente - {mensaje_visita}",
    "es_visitante_nuevo": visita_existente is None
}
```

---

## 📊 Ejemplos

### Caso 1: Primer QR para Visitante (Nuevo)

```
Request:
{
  "visita_identificacion": "1234567890",
  "visita_nombres": "Carlos",
  "visita_apellidos": "García",
  ...
}

Response (200):
{
  "id": 16,
  "token": "xY9aBcDeFgHiJkLmNoPqRsTuVwXyZ789",
  "hora_inicio": "2024-12-25T10:00:00",
  "hora_fin": "2024-12-25T12:00:00",
  "estado": "vigente",
  "visita_id": 101,
  "mensaje": "... - Nuevo visitante registrado",
  "es_visitante_nuevo": true  ✅ NUEVO
}

BD Tabla visita:
  INSERT INTO visita (vivienda_id, identificacion, nombres, apellidos)
  VALUES (1, '1234567890', 'Carlos', 'García')
```

### Caso 2: Segundo QR para Mismo Visitante (Reutilizado)

```
Request (misma identificación, diferente fecha/hora):
{
  "visita_identificacion": "1234567890",
  "visita_nombres": "Carlos",
  "visita_apellidos": "García",
  "fecha_acceso": "2024-12-26",  ← Otro día
  ...
}

Response (200):
{
  "id": 17,
  "token": "aB9zYxWvUtSrQpOnMlKjIhGfEdCbAz123",
  "hora_inicio": "2024-12-26T14:00:00",
  "hora_fin": "2024-12-26T16:00:00",
  "estado": "vigente",
  "visita_id": 101,  ← MISMO ID de visita
  "mensaje": "... - Visitante reutilizado",
  "es_visitante_nuevo": false  ✅ REUTILIZADO
}

BD Tabla visita:
  NO INSERT - Solo reusa el registro anterior
  
BD Tabla QR:
  INSERT INTO qr (visita_id, token, ...)  ← Nuevo QR
  VALUES (101, 'aB9zYxWvUtSrQpOnMlKjIhGfEdCbAz123', ...)
```

---

## ✨ Ventajas

✅ **Evita Duplicados:** Un visitante = Un registro en tabla visita  
✅ **Múltiples QRs:** Permite generar varios QRs para el mismo visitante  
✅ **Datos Limpios:** Registro histórico centralizado por visitante  
✅ **Auditoría Clara:** Campo `es_visitante_nuevo` indica el caso  
✅ **Sin Cambios de API:** Backward compatible, solo agrega campo  
✅ **Eficiente:** Consulta simple por identificación  

---

## 🔍 Criterios de Búsqueda

La búsqueda compara:
- ✅ `identificacion` - Cédula/Pasaporte del visitante
- ✅ `vivienda_id` - La misma vivienda
- ✅ `eliminado = False` - Solo registros activos

**Nota:** NO compara nombres/apellidos, solo identificación (es el campo único).

---

## 🧪 Testing

### Test Case 1: Nuevo Visitante
```python
# Generar QR para visitante que no existe
response = client.post(
  "/qr/generar-visita",
  json={
    "visita_identificacion": "1111111111",
    "visita_nombres": "Juan",
    "visita_apellidos": "Pérez",
    ...
  }
)
assert response.json()["es_visitante_nuevo"] == True
assert response.json()["visita_id"] == 101  # Nuevo ID
```

### Test Case 2: Visitante Duplicado
```python
# Generar QR para el MISMO visitante (misma ID)
response = client.post(
  "/qr/generar-visita",
  json={
    "visita_identificacion": "1111111111",  # MISMA ID
    "visita_nombres": "Juan",
    "visita_apellidos": "Pérez",
    ...
  }
)
assert response.json()["es_visitante_nuevo"] == False  # Reutilizado
assert response.json()["visita_id"] == 101  # MISMO ID de visita
```

### Test Case 3: Diferente Vivienda
```python
# Mismo visitante pero en diferente vivienda
# (cuenta diferente = vivienda diferente)
# Debería crear nuevo registro

response = client.post(
  "/qr/generar-visita",
  json={
    "visita_identificacion": "1111111111",  # MISMA ID
    "vivienda_id": 2,  # DIFERENTE VIVIENDA
    ...
  }
)
assert response.json()["es_visitante_nuevo"] == True  # Nuevo (otra vivienda)
assert response.json()["visita_id"] == 102  # DIFERENTE ID
```

---

## 📖 Documentación Actualizada

El endpoint está completamente documentado en:
- [API_DOCUMENTACION_COMPLETA.md](API_DOCUMENTACION_COMPLETA.md) - Sección "2. Generar QR Visita"

Incluye:
- ✅ Descripción de duplicados
- ✅ Lógica de funcionamiento
- ✅ Campos nuevos en respuesta
- ✅ Ejemplos JSON (nuevo vs reutilizado)
- ✅ Ejemplo de código Flutter

---

## 🔗 Archivos Modificados

1. **app/interfaces/routers/qr_router.py**
   - Línea ~165: Búsqueda de duplicado
   - Línea ~185: Lógica condicional
   - Línea ~196: Respuesta con campos nuevos

2. **API_DOCUMENTACION_COMPLETA.md**
   - Actualizado endpoint generar-visita
   - Nuevos campos documentados
   - Lógica de duplicados explicada

---

## 💡 Casos de Uso

1. **Técnico Recurrente:** Mismo técnico de gas visita múltiples veces
   - Primer QR: registra visitante en tabla
   - Siguientes QRs: reutiliza el registro
   - BD limpia sin duplicados

2. **Proveedor Habitual:** Servicio de mensajería que entrega regularmente
   - Cada entrega: nuevo QR
   - Misma vivienda: registro reutilizado
   - Histórico centralizado

3. **Familiares Frecuentes:** Parientes que visitan regularmente
   - Cada visita: nuevo QR temporal
   - Mismo visitante: registro único
   - Auditoría completa por visitante

---

## ⚙️ Implementación

**Estado:** ✅ Completada  
**Versión:** 1.0  
**Fecha:** 2026-01-20  
**Impacto:** Control de duplicados en visitantes

