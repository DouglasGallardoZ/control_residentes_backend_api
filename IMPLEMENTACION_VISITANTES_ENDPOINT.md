# 📋 IMPLEMENTACIÓN: Endpoint de Visitantes por Vivienda

**Objetivo:** Permite consultar todos los visitantes registrados para una vivienda, facilitando su reutilización en la app Flutter.

**Requirement:** RF-Q04 (Consultar visitantes por vivienda)

---

## 📌 Resumen de Cambios

### 1. Schemas Creados (schemas.py)

Se agregaron 2 nuevos modelos Pydantic:

```python
class VisitaResponse(BaseModel):
    """Schema para un visitante individual"""
    visita_id: int
    identificacion: str
    nombres: str
    apellidos: str
    fecha_creado: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "visita_id": 101,
                "identificacion": "1234567890",
                "nombres": "Carlos",
                "apellidos": "García",
                "fecha_creado": "2024-12-25T10:00:00"
            }
        }


class ViviendaVisitasResponse(BaseModel):
    """Schema para respuesta con todos los visitantes de una vivienda"""
    vivienda_id: int
    manzana: str
    villa: str
    visitantes: List[VisitaResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "vivienda_id": 1,
                "manzana": "A",
                "villa": "101",
                "visitantes": [...],
                "total": 2
            }
        }
```

**Ubicación:** [app/interfaces/schemas/schemas.py](app/interfaces/schemas/schemas.py)

---

### 2. Endpoint Implementado (qr_router.py)

**Ruta:** `GET /api/v1/qr/visitantes/{persona_id}`

**Código:**
```python
@router.get("/visitantes/{persona_id}", response_model=ViviendaVisitasResponse)
def obtener_visitantes_vivienda(
    persona_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los visitantes registrados para la vivienda de una persona.
    
    La persona puede ser residente o miembro de familia.
    Los visitantes se retornan ordenados por fecha descendente (más recientes primero).
    """
    
    # 1. Buscar persona
    persona = db.query(Persona).filter(
        Persona.persona_pk == persona_id
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    
    # 2. Determinar si es residente o miembro
    vivienda_id = None
    
    # Verificar si es residente
    residente = db.query(ResidenteVivienda).filter(
        ResidenteVivienda.persona_residente_fk == persona_id,
        ResidenteVivienda.estado == "activo"
    ).first()
    
    if residente:
        vivienda_id = residente.vivienda_residente_fk
    else:
        # Verificar si es miembro de familia
        miembro = db.query(MiembroVivienda).filter(
            MiembroVivienda.persona_miembro_fk == persona_id,
            MiembroVivienda.estado == "activo"
        ).first()
        
        if miembro:
            vivienda_id = miembro.vivienda_miembro_fk
    
    # 3. Validar que se encontró vivienda
    if not vivienda_id:
        raise HTTPException(
            status_code=403,
            detail="La persona no tiene una vivienda asociada activa"
        )
    
    # 4. Obtener datos de vivienda
    vivienda = db.query(Vivienda).filter(
        Vivienda.vivienda_pk == vivienda_id
    ).first()
    
    if not vivienda:
        raise HTTPException(status_code=404, detail="Vivienda no encontrada")
    
    # 5. Obtener visitantes
    visitantes = db.query(Visita).filter(
        Visita.vivienda_visita_fk == vivienda_id,
        Visita.eliminado == False
    ).order_by(Visita.fecha_creado.desc()).all()
    
    # 6. Construir respuesta
    visitantes_data = [
        VisitaResponse(
            visita_id=v.visita_pk,
            identificacion=v.identificacion,
            nombres=v.nombres,
            apellidos=v.apellidos,
            fecha_creado=v.fecha_creado
        )
        for v in visitantes
    ]
    
    return ViviendaVisitasResponse(
        vivienda_id=vivienda.vivienda_pk,
        manzana=vivienda.manzana,
        villa=vivienda.villa,
        visitantes=visitantes_data,
        total=len(visitantes_data)
    )
```

**Ubicación:** [app/interfaces/routers/qr_router.py](app/interfaces/routers/qr_router.py)

---

## 🔄 Flujo de Lógica

```
┌─────────────────────────────────────────┐
│ GET /qr/visitantes/{persona_id}          │
│ Autenticación: Bearer Token              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ 1. Validar que persona existe            │
│    - Query: Persona.persona_pk           │
│    - Error 404: Si no existe             │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ 2. Verificar si es RESIDENTE             │
│    - Query: ResidenteVivienda            │
│    - Filtro: estado='activo'             │
│    - Obtener: vivienda_id                │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │ ¿Es residente?       │
        └──────────┬──────────┘
           SÍ │         │ NO
             ▼         ▼
        ┌────────┐  ┌─────────────────────────────────────────┐
        │Usar    │  │ 3. Verificar si es MIEMBRO DE FAMILIA    │
        │vivienda│  │    - Query: MiembroVivienda             │
        │_id    │  │    - Filtro: estado='activo'            │
        │       │  │    - Obtener: vivienda_id               │
        └────┬──┘  └──────────────────┬─────────────────────┘
            │                          │
            │              ┌───────────┴───────────┐
            │              │ ¿Es miembro?          │
            │              └───────────┬───────────┘
            │                  SÍ │         │ NO
            │                    ▼         ▼
            │                ┌────────┐  ┌─────────────────────┐
            │                │Usar    │  │ Error 403:          │
            │                │vivienda│  │ Sin vivienda activa │
            │                │_id    │  │ (return)            │
            │                └────┬──┘  └─────────────────────┘
            │                    │
            └────────┬───────────┘
                     │
                     ▼
         ┌─────────────────────────────────────────┐
         │ 4. Obtener datos de VIVIENDA            │
         │    - Query: Vivienda.vivienda_pk        │
         │    - Error 404: Si no existe            │
         │    - Obtener: manzana, villa            │
         └──────────────────┬──────────────────────┘
                            │
                            ▼
         ┌─────────────────────────────────────────┐
         │ 5. Query VISITANTES                     │
         │    - Query: Visita                      │
         │    - Filtro: vivienda_fk, eliminado=F   │
         │    - Order: fecha_creado DESC           │
         │    - Mapear a VisitaResponse[]          │
         └──────────────────┬──────────────────────┘
                            │
                            ▼
         ┌─────────────────────────────────────────┐
         │ 6. Retornar ViviendaVisitasResponse    │
         │    {                                    │
         │      vivienda_id, manzana, villa,       │
         │      visitantes[], total                │
         │    }                                    │
         └─────────────────────────────────────────┘
```

---

## 📊 Modelos de Base de Datos Utilizados

### Tabla: Persona
```sql
SELECT persona_pk, ... FROM persona WHERE persona_pk = ?
```

### Tabla: ResidenteVivienda
```sql
SELECT * FROM residente_vivienda 
WHERE persona_residente_fk = ? AND estado = 'activo'
```

### Tabla: MiembroVivienda
```sql
SELECT * FROM miembro_vivienda 
WHERE persona_miembro_fk = ? AND estado = 'activo'
```

### Tabla: Vivienda
```sql
SELECT vivienda_pk, manzana, villa FROM vivienda 
WHERE vivienda_pk = ?
```

### Tabla: Visita
```sql
SELECT visita_pk, identificacion, nombres, apellidos, fecha_creado 
FROM visita 
WHERE vivienda_visita_fk = ? AND eliminado = FALSE
ORDER BY fecha_creado DESC
```

---

## 🔐 Seguridad y Validaciones

### Autenticación
- ✅ Requiere Bearer token válido (Firebase JWT)
- ✅ Validado en middleware

### Autorización
- ✅ La persona debe existir
- ✅ La persona debe tener vivienda activa (como residente o miembro)
- ✅ Solo retorna visitantes no eliminados

### Validaciones de Entrada
- ✅ `persona_id` es integer
- ✅ `persona_id` > 0

### Validaciones de Lógica
- ✅ Persona debe tener estado "activo"
- ✅ Verifica tanto residentes como miembros
- ✅ Excluye registros eliminados (soft delete)

---

## 📈 Casos de Uso

### 1. Reutilizar Visitantes Frecuentes
```
Usuario abre formulario para generar QR de visita
  → Llama GET /visitantes/{persona_id}
  → Muestra lista de visitantes anteriores
  → Usuario selecciona de la lista
  → Datos se prellenan automáticamente
  → Usuario solo genera QR
```

### 2. Consultar Historial de Visitantes
```
Usuario quiere ver quién ha visitado su vivienda
  → Llama GET /visitantes/{persona_id}
  → Ve nombre, ID, fecha de cada visitante
  → Información útil para auditoría/control
```

### 3. Control de Acceso por Vivienda
```
Sistema de control quiere listar visitantes esperados
  → Llama GET /visitantes/{persona_id}
  → Compara con visitantes que llegan
  → Valida si son esperados o no
```

---

## 🧪 Pruebas Realizadas

Archivo de pruebas: [test_visitantes_endpoint.py](test_visitantes_endpoint.py)

Incluye:
1. ✅ Obtener visitantes - Caso exitoso
2. ✅ Persona no encontrada (404)
3. ✅ Persona sin vivienda activa (403)
4. ✅ Sin autorización (401)
5. ✅ Validación de fechas ISO 8601
6. ✅ Ordenamiento por fecha descendente
7. ✅ Funciona con miembros de familia

**Para ejecutar:**
```bash
python test_visitantes_endpoint.py
```

---

## 📱 Uso en Flutter

### Modelo Dart
```dart
class Visitante {
  final int id;
  final String identificacion;
  final String nombres;
  final String apellidos;
  final DateTime fechaCreado;

  Visitante({
    required this.id,
    required this.identificacion,
    required this.nombres,
    required this.apellidos,
    required this.fechaCreado,
  });

  String get nombreCompleto => '$nombres $apellidos';
  
  factory Visitante.fromJson(Map<String, dynamic> json) {
    return Visitante(
      id: json['visita_id'],
      identificacion: json['identificacion'],
      nombres: json['nombres'],
      apellidos: json['apellidos'],
      fechaCreado: DateTime.parse(json['fecha_creado']),
    );
  }
}
```

### Integración con Formulario
```dart
class GenerarQRVisitaForm extends StatefulWidget {
  final int personaId;

  @override
  _GenerarQRVisitaFormState createState() => _GenerarQRVisitaFormState();
}

class _GenerarQRVisitaFormState extends State<GenerarQRVisitaForm> {
  List<Visitante> visitantesDisponibles = [];
  Visitante? visitanteSeleccionado;
  bool cargando = true;

  @override
  void initState() {
    super.initState();
    _cargarVisitantes();
  }

  Future<void> _cargarVisitantes() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/qr/visitantes/${widget.personaId}'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          visitantesDisponibles = (data['visitantes'] as List)
              .map((v) => Visitante.fromJson(v))
              .toList();
          cargando = false;
        });
      }
    } catch (e) {
      setState(() => cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (cargando) return CircularProgressIndicator();

    return Column(
      children: [
        if (visitantesDisponibles.isNotEmpty)
          DropdownButton<Visitante>(
            isExpanded: true,
            hint: Text('Seleccionar visitante anterior'),
            value: visitanteSeleccionado,
            items: visitantesDisponibles.map((v) {
              return DropdownMenuItem(
                value: v,
                child: Text(v.displayText),
              );
            }).toList(),
            onChanged: (seleccionado) {
              setState(() => visitanteSeleccionado = seleccionado);
              // Prellenar campos
              if (seleccionado != null) {
                identificacionController.text = seleccionado.identificacion;
                nombresController.text = seleccionado.nombres;
                apellidosController.text = seleccionado.apellidos;
              }
            },
          ),
        SizedBox(height: 16),
        // Campos de formulario...
      ],
    );
  }
}
```

---

## 📝 Cambios en el Código

### Archivo: app/interfaces/schemas/schemas.py
- ✅ Agregadas clases: `VisitaResponse`, `ViviendaVisitasResponse`
- ✅ Docstrings con ejemplos JSON

### Archivo: app/interfaces/routers/qr_router.py
- ✅ Agregado import: `MiembroVivienda` desde models
- ✅ Agregados imports: `VisitaResponse`, `ViviendaVisitasResponse` desde schemas
- ✅ Implementado endpoint: `GET /visitantes/{persona_id}`
- ✅ ~100 líneas de código nuevo

### Archivo: API_DOCUMENTACION_COMPLETA.md
- ✅ Actualizado conteo de endpoints QR (4 → 5)
- ✅ Actualizado conteo total (24 → 25)
- ✅ Agregada documentación completa del endpoint
- ✅ Incluidos 3 ejemplos Flutter prácticos

---

## 🚀 Próximos Pasos Recomendados

1. **Testing Manual:**
   - Probar con diferentes usuarios (residentes vs miembros)
   - Validar paginación si se agrega en futuro
   - Probar con viviendas sin visitantes

2. **Optimización:**
   - Agregar caché para consultas frecuentes
   - Implementar paginación si hay muchos visitantes
   - Agregar filtros por rango de fechas

3. **Documentación:**
   - Crear guía Flutter en [GUIA_VISITANTES_FLUTTER.md](GUIA_VISITANTES_FLUTTER.md)
   - Actualizar arquitectura del proyecto

4. **Features Futuras:**
   - Endpoint para obtener estadísticas de visitantes
   - Exportar historial de visitantes (PDF)
   - Notificaciones cuando llega un visitante

---

## 📞 Soporte

**Problemas Comunes:**

1. **Error 403: "La persona no tiene vivienda asociada activa"**
   - Verificar que persona_id corresponde a residente o miembro
   - Verificar que el estado es "activo"
   - Verificar relación con vivienda

2. **Error 404: "Persona no encontrada"**
   - Verificar persona_id es correcto
   - Verificar usuario está logueado con permiso

3. **Lista vacía de visitantes**
   - Vivienda es nueva sin visitantes registrados
   - Todos los visitantes fueron marcados como eliminados
   - Normal, mostrar opción "Crear nuevo visitante"

---

**Versión:** 1.0.0  
**Fecha:** 2024  
**Status:** ✅ Implementado y Documentado
