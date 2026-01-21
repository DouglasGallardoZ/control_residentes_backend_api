# 📱 GUÍA DE INTEGRACIÓN: Reutilizar Visitantes en Flutter

## 🎯 Objetivo

Permitir que los usuarios de la app Flutter reutilicen información de visitantes anteriores al generar nuevos códigos QR de visita, mejorando la experiencia de usuario.

---

## 🔄 Flujo Completo

```
┌─────────────────────────────────────────────┐
│ Usuario abre pantalla "Generar QR Visita"  │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ App llama: GET /qr/visitantes/{persona_id} │
│ Carga lista de visitantes anteriores        │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Si hay visitantes: Mostrar Dropdown/List   │
│ Si no hay: Mostrar formulario vacío        │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Usuario selecciona visitante                │
│ O llena formulario nuevo                    │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ App llama: POST /qr/generar-visita         │
│ Con datos prellenados                       │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ Backend retorna:                            │
│ - QR token                                  │
│ - es_visitante_nuevo (true/false)           │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│ App muestra QR generado                    │
└─────────────────────────────────────────────┘
```

---

## 🛠️ Implementación en Flutter

### 1. Modelo Visitante

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
  
  String get displayText => '$nombreCompleto ($identificacion)';
  
  String get tiempoAtras {
    final ahora = DateTime.now();
    final diferencia = ahora.difference(fechaCreado);
    
    if (diferencia.inMinutes < 1) return 'hace poco';
    if (diferencia.inMinutes < 60) return 'hace ${diferencia.inMinutes}m';
    if (diferencia.inHours < 24) return 'hace ${diferencia.inHours}h';
    if (diferencia.inDays < 7) return 'hace ${diferencia.inDays}d';
    return 'hace ${diferencia.inDays ~/ 7}s';
  }

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

class RespuestaVisitantes {
  final int viviendaId;
  final String manzana;
  final String villa;
  final List<Visitante> visitantes;
  final int total;

  RespuestaVisitantes({
    required this.viviendaId,
    required this.manzana,
    required this.villa,
    required this.visitantes,
    required this.total,
  });

  String get direccion => 'Manzana $manzana, Villa $villa';

  factory RespuestaVisitantes.fromJson(Map<String, dynamic> json) {
    return RespuestaVisitantes(
      viviendaId: json['vivienda_id'],
      manzana: json['manzana'],
      villa: json['villa'],
      visitantes: List<Visitante>.from(
        (json['visitantes'] as List).map((v) => Visitante.fromJson(v))
      ),
      total: json['total'],
    );
  }
}
```

### 2. Servicio de API

```dart
class VisitantesService {
  final String baseUrl = 'http://localhost:8000/api/v1';
  String? _token;

  VisitantesService({String? token}) {
    _token = token;
  }

  Future<RespuestaVisitantes> obtenerVisitantes(int personaId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/qr/visitantes/$personaId'),
        headers: {
          'Authorization': 'Bearer $_token',
          'Content-Type': 'application/json',
        },
      ).timeout(
        Duration(seconds: 10),
        onTimeout: () => throw Exception('Timeout al cargar visitantes'),
      );

      if (response.statusCode == 200) {
        return RespuestaVisitantes.fromJson(jsonDecode(response.body));
      } else if (response.statusCode == 403) {
        throw Exception('Persona sin vivienda activa');
      } else if (response.statusCode == 404) {
        throw Exception('Persona no encontrada');
      } else if (response.statusCode == 401) {
        throw Exception('No autorizado');
      } else {
        throw Exception('Error: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error al cargar visitantes: $e');
    }
  }

  Future<Map<String, dynamic>> generarQRVisita({
    required int personaId,
    required String identificacion,
    required String nombres,
    required String apellidos,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/qr/generar-visita'),
        headers: {
          'Authorization': 'Bearer $_token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'persona_id': personaId,
          'identificacion': identificacion,
          'nombres': nombres,
          'apellidos': apellidos,
          'usuario_creado': 'flutter_app',
        }),
      );

      if (response.statusCode == 201) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Error: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error al generar QR: $e');
    }
  }
}
```

### 3. Widget Principal

```dart
class PantallaGenerarQRVisita extends StatefulWidget {
  final int personaId;
  final String token;

  const PantallaGenerarQRVisita({
    required this.personaId,
    required this.token,
  });

  @override
  State<PantallaGenerarQRVisita> createState() =>
      _PantallaGenerarQRVisitaState();
}

class _PantallaGenerarQRVisitaState extends State<PantallaGenerarQRVisita> {
  late VisitantesService _service;
  late Future<RespuestaVisitantes> _futureVisitantes;

  final _identificacionController = TextEditingController();
  final _nombresController = TextEditingController();
  final _apellidosController = TextEditingController();

  Visitante? _visitanteSeleccionado;
  bool _cargando = false;
  String? _qrGenerado;
  bool? _esNuevo;

  @override
  void initState() {
    super.initState();
    _service = VisitantesService(token: widget.token);
    _futureVisitantes = _service.obtenerVisitantes(widget.personaId);
  }

  @override
  void dispose() {
    _identificacionController.dispose();
    _nombresController.dispose();
    _apellidosController.dispose();
    super.dispose();
  }

  void _prerellenarDatos(Visitante visitante) {
    _identificacionController.text = visitante.identificacion;
    _nombresController.text = visitante.nombres;
    _apellidosController.text = visitante.apellidos;
    setState(() => _visitanteSeleccionado = visitante);
  }

  Future<void> _generarQR() async {
    if (_identificacionController.text.isEmpty ||
        _nombresController.text.isEmpty ||
        _apellidosController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Completa todos los campos')),
      );
      return;
    }

    setState(() => _cargando = true);

    try {
      final resultado = await _service.generarQRVisita(
        personaId: widget.personaId,
        identificacion: _identificacionController.text,
        nombres: _nombresController.text,
        apellidos: _apellidosController.text,
      );

      setState(() {
        _qrGenerado = resultado['token'];
        _esNuevo = resultado['es_visitante_nuevo'] ?? false;
        _cargando = false;
      });

      _mostrarQRGenerado();
    } catch (e) {
      setState(() => _cargando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    }
  }

  void _mostrarQRGenerado() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('✅ QR Generado'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_qrGenerado != null)
              QrImageView(
                data: _qrGenerado!,
                version: QrVersions.auto,
                size: 250.0,
              ),
            SizedBox(height: 16),
            Text(_esNuevo == false ? 'Visitante reutilizado' : 'Visitante nuevo'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cerrar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Generar QR de Visita')),
      body: FutureBuilder<RespuestaVisitantes>(
        future: _futureVisitantes,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.red),
                  SizedBox(height: 16),
                  Text('Error: ${snapshot.error}'),
                  SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      setState(() {
                        _futureVisitantes =
                            _service.obtenerVisitantes(widget.personaId);
                      });
                    },
                    child: Text('Reintentar'),
                  ),
                ],
              ),
            );
          }

          final respuesta = snapshot.data!;

          return SingleChildScrollView(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Información de vivienda
                  Card(
                    child: Padding(
                      padding: EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Vivienda',
                            style: Theme.of(context).textTheme.labelSmall,
                          ),
                          SizedBox(height: 4),
                          Text(
                            respuesta.direccion,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 24),

                  // Selector de visitantes anteriores
                  if (respuesta.visitantes.isNotEmpty)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Visitantes Anteriores (${respuesta.total})',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        SizedBox(height: 12),
                        _construirListaVisitantes(respuesta.visitantes),
                        SizedBox(height: 24),
                        Divider(),
                        SizedBox(height: 24),
                        Text(
                          'O crear nuevo visitante',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey,
                          ),
                        ),
                        SizedBox(height: 12),
                      ],
                    ),

                  // Formulario
                  TextField(
                    controller: _identificacionController,
                    decoration: InputDecoration(
                      labelText: 'Identificación',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.badge),
                    ),
                  ),
                  SizedBox(height: 12),

                  TextField(
                    controller: _nombresController,
                    decoration: InputDecoration(
                      labelText: 'Nombres',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.person),
                    ),
                  ),
                  SizedBox(height: 12),

                  TextField(
                    controller: _apellidosController,
                    decoration: InputDecoration(
                      labelText: 'Apellidos',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                  ),
                  SizedBox(height: 24),

                  // Botón generar
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _cargando ? null : _generarQR,
                      child: _cargando
                          ? SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                          : Text('Generar QR'),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _construirListaVisitantes(List<Visitante> visitantes) {
    return ListView.builder(
      shrinkWrap: true,
      physics: NeverScrollableScrollPhysics(),
      itemCount: visitantes.length,
      itemBuilder: (context, index) {
        final visitante = visitantes[index];
        final esSeleccionado = _visitanteSeleccionado?.id == visitante.id;

        return Card(
          color: esSeleccionado ? Colors.blue.shade50 : null,
          child: ListTile(
            leading: CircleAvatar(
              child: Text(visitante.nombres[0]),
            ),
            title: Text(visitante.nombreCompleto),
            subtitle: Text(
              '${visitante.identificacion} • ${visitante.tiempoAtras}',
            ),
            trailing: esSeleccionado
                ? Icon(Icons.check_circle, color: Colors.green)
                : null,
            onTap: () => _prerellenarDatos(visitante),
          ),
        );
      },
    );
  }
}
```

---

## 📊 Casos de Uso

### Caso 1: Visitante Frecuente
```
Usuario: "Mi mamá me visita todas las semanas"

1. Abre pantalla de generar QR
2. Ve lista de visitantes
3. Selecciona "María García" (madre)
4. Datos se prellenan automáticamente
5. Solo hace clic en "Generar QR"
6. QR generado en 2 segundos
7. Backend retorna: es_visitante_nuevo = false
```

### Caso 2: Visitante Nuevo
```
Usuario: "Mi amigo viene por primera vez"

1. Abre pantalla de generar QR
2. Ve lista de visitantes anteriores
3. No ve a su amigo en la lista
4. Completa manualmente:
   - Identificación: 1234567890
   - Nombres: Carlos
   - Apellidos: López
5. Hace clic en "Generar QR"
6. Backend retorna: es_visitante_nuevo = true
7. Próxima vez aparecerá en la lista
```

### Caso 3: Vivienda Sin Visitantes
```
Usuario: "Es la primera vez que tengo un visitante"

1. Abre pantalla de generar QR
2. Lista de visitantes está vacía
3. Completa manualmente el formulario
4. Genera QR exitosamente
5. Próximas veces tendrá visitante en la lista
```

---

## ⚡ Optimizaciones Recomendadas

### 1. Caché Local
```dart
class VisitantesCache {
  static const String _key = 'visitantes_cache';
  final SharedPreferences _prefs;

  Future<void> guardar(RespuestaVisitantes respuesta) async {
    await _prefs.setString(
      _key,
      jsonEncode(respuesta),
    );
  }

  Future<RespuestaVisitantes?> obtener() async {
    final json = _prefs.getString(_key);
    if (json == null) return null;
    return RespuestaVisitantes.fromJson(jsonDecode(json));
  }

  Future<void> limpiar() async {
    await _prefs.remove(_key);
  }
}
```

### 2. Búsqueda Local
```dart
List<Visitante> buscarVisitantes(
  List<Visitante> visitantes,
  String query,
) {
  if (query.isEmpty) return visitantes;

  final queryLower = query.toLowerCase();
  return visitantes.where((v) {
    return v.nombreCompleto.toLowerCase().contains(queryLower) ||
        v.identificacion.contains(queryLower);
  }).toList();
}
```

### 3. Paginación (Futuro)
```dart
class VisitantesService {
  Future<RespuestaVisitantes> obtenerVisitantes(
    int personaId, {
    int page = 1,
    int pageSize = 10,
  }) async {
    final response = await http.get(
      Uri.parse('$baseUrl/qr/visitantes/$personaId')
          .replace(queryParameters: {
        'page': page.toString(),
        'page_size': pageSize.toString(),
      }),
      // ...
    );
    // ...
  }
}
```

---

## 📋 Checklist de Implementación

- [ ] Copiar modelos Visitante y RespuestaVisitantes
- [ ] Crear VisitantesService
- [ ] Implementar PantallaGenerarQRVisita
- [ ] Probar carga de visitantes
- [ ] Probar generación de QR
- [ ] Implementar caché local (opcional)
- [ ] Agregar búsqueda de visitantes (opcional)
- [ ] Pruebas de UI/UX

---

## 🐛 Troubleshooting

### Error 403: "La persona no tiene vivienda asociada activa"
```
Causa: persona_id no corresponde a residente o miembro activo

Solución:
1. Verificar que el usuario es residente o miembro
2. Verificar que el estado es "activo"
3. Renovar token de autenticación
```

### Lista de visitantes vacía
```
Normal si:
- Es la primera vivienda
- Todos los visitantes fueron eliminados

Mostrar: "No hay visitantes anteriores. Completa el formulario."
```

### Timeout al cargar visitantes
```
Solución:
1. Verificar conexión de red
2. Implementar reintentos automáticos
3. Usar caché local como fallback
```

---

**Versión:** 1.0.0  
**Última actualización:** 2024  
**Status:** ✅ Listo para implementar
