"""
Ejemplos de Integración - Endpoints de Accesos

Código de ejemplo para integración en Flutter con los nuevos endpoints de accesos.
"""

# ============================================================================
# EJEMPLO 1: Consultar Accesos de una Vivienda (Residente)
# ============================================================================

example_get_accesos_vivienda = """
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> obtenerAccesosVivienda(String token, int viviendaId) async {
  try {
    // URL del endpoint
    String url = 'https://api.residencias.com/api/v1/accesos/vivienda/$viviendaId';
    
    // Parámetros opcionales
    Map<String, String> queryParams = {
      // 'fecha_inicio': '2024-12-01',
      // 'fecha_fin': '2024-12-31',
      // 'tipo': 'qr_residente',
      // 'resultado': 'autorizado',
    };
    
    // Construir URL con query parameters
    Uri uri = Uri.parse(url).replace(queryParameters: queryParams);
    
    // Realizar solicitud GET
    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    ).timeout(Duration(seconds: 30));
    
    // Validar respuesta
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      
      print('Vivienda: ${data['manzana']}-${data['villa']}');
      print('Total de accesos: ${data['total_accesos']}');
      
      // Procesar lista de accesos
      for (var acceso in data['accesos']) {
        print('''
        Acceso: ${acceso['acceso_pk']}
        Tipo: ${acceso['tipo']}
        Resultado: ${acceso['resultado']}
        Fecha: ${acceso['fecha_creado']}
        Visita: ${acceso['visita_nombres'] ?? 'N/A'}
        ''');
      }
      
    } else if (response.statusCode == 404) {
      print('Vivienda no encontrada');
    } else {
      print('Error: ${response.statusCode}');
    }
  } catch (e) {
    print('Excepción: $e');
  }
}

// Uso:
// await obtenerAccesosVivienda(token, 1);
"""

# ============================================================================
# EJEMPLO 2: Consultar Estadísticas de Accesos (Admin)
# ============================================================================

example_get_estadisticas_admin = """
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> obtenerEstadisticasAdmin(String token) async {
  try {
    String url = 'https://api.residencias.com/api/v1/accesos/admin/estadisticas';
    
    // Parámetros opcionales
    Map<String, String> queryParams = {
      // 'fecha_inicio': '2024-12-01',
      // 'fecha_fin': '2024-12-31',
    };
    
    Uri uri = Uri.parse(url).replace(queryParameters: queryParams);
    
    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    ).timeout(Duration(seconds: 30));
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      
      // Estadísticas generales
      final stats = data['estadisticas_generales'];
      print('Total de accesos: ${stats['total']}');
      print('Exitosos: ${stats['exitosos']}');
      print('Rechazados: ${stats['rechazados']}');
      print('Pendientes: ${stats['pendientes']}');
      
      // Visitantes únicos
      print('Visitantes únicos: ${data['cantidad_visitantes_unicos']}');
      
      // Accesos por tipo
      print('\\nAccesos por tipo:');
      for (var tipo in data['accesos_por_tipo']) {
        print('  ${tipo['tipo']}: ${tipo['cantidad']}');
      }
      
      // Accesos por resultado
      print('\\nAccesos por resultado:');
      for (var resultado in data['accesos_por_resultado']) {
        print('  ${resultado['resultado']}: ${resultado['cantidad']}');
      }
      
      // Top viviendas
      print('\\nTop viviendas con más accesos:');
      for (var vivienda in data['viviendas_con_mas_accesos'].take(5)) {
        print('  Manzana ${vivienda['manzana']}, Villa ${vivienda['villa']}: ${vivienda['cantidad_accesos']}');
      }
      
    } else {
      print('Error: ${response.statusCode}');
    }
  } catch (e) {
    print('Excepción: $e');
  }
}

// Uso:
// await obtenerEstadisticasAdmin(token);
"""

# ============================================================================
# EJEMPLO 3: Crear un Widget para mostrar Accesos
# ============================================================================

example_widget_accesos = """
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class AccesosScreen extends StatefulWidget {
  final String token;
  final int viviendaId;
  
  AccesosScreen({required this.token, required this.viviendaId});
  
  @override
  _AccesosScreenState createState() => _AccesosScreenState();
}

class _AccesosScreenState extends State<AccesosScreen> {
  late Future<Map<String, dynamic>> futureAccesos;
  
  @override
  void initState() {
    super.initState();
    futureAccesos = fetchAccesos();
  }
  
  Future<Map<String, dynamic>> fetchAccesos() async {
    final response = await http.get(
      Uri.parse('https://api.residencias.com/api/v1/accesos/vivienda/${widget.viviendaId}'),
      headers: {
        'Authorization': 'Bearer ${widget.token}',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error al cargar accesos');
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: futureAccesos,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        } else if (snapshot.hasData) {
          final data = snapshot.data!;
          final accesos = data['accesos'] as List;
          
          return Column(
            children: [
              Padding(
                padding: EdgeInsets.all(16),
                child: Text(
                  'Vivienda ${data['manzana']}-${data['villa']}',
                  style: Theme.of(context).textTheme.headline6,
                ),
              ),
              Expanded(
                child: ListView.builder(
                  itemCount: accesos.length,
                  itemBuilder: (context, index) {
                    final acceso = accesos[index];
                    final color = acceso['resultado'] == 'autorizado'
                        ? Colors.green
                        : Colors.red;
                    
                    return Card(
                      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: ListTile(
                        leading: Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: color,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Icon(
                            acceso['resultado'] == 'autorizado'
                                ? Icons.check
                                : Icons.close,
                            color: Colors.white,
                          ),
                        ),
                        title: Text(acceso['tipo'].replaceAll('_', ' ').toUpperCase()),
                        subtitle: Text(acceso['fecha_creado']),
                        trailing: Chip(
                          label: Text(acceso['resultado']),
                          backgroundColor: color.withOpacity(0.3),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          );
        } else {
          return Center(child: Text('No hay datos'));
        }
      },
    );
  }
}

// Uso:
// AccesosScreen(token: 'your_token', viviendaId: 1)
"""

# ============================================================================
# EJEMPLO 4: Servicio Reutilizable para Accesos
# ============================================================================

example_service = """
import 'package:http/http.dart' as http;
import 'dart:convert';

class AccesosService {
  final String baseUrl = 'https://api.residencias.com/api/v1';
  final String token;
  
  AccesosService({required this.token});
  
  /// Obtiene accesos de una vivienda
  Future<Map<String, dynamic>> getAccesosVivienda({
    required int viviendaId,
    DateTime? fechaInicio,
    DateTime? fechaFin,
    String? tipo,
    String? resultado,
  }) async {
    Map<String, String> queryParams = {};
    
    if (fechaInicio != null) {
      queryParams['fecha_inicio'] = fechaInicio.toIso8601String().split('T')[0];
    }
    if (fechaFin != null) {
      queryParams['fecha_fin'] = fechaFin.toIso8601String().split('T')[0];
    }
    if (tipo != null) queryParams['tipo'] = tipo;
    if (resultado != null) queryParams['resultado'] = resultado;
    
    Uri uri = Uri.parse('$baseUrl/accesos/vivienda/$viviendaId')
        .replace(queryParameters: queryParams);
    
    final response = await http.get(
      uri,
      headers: {'Authorization': 'Bearer $token'},
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error: ${response.statusCode}');
    }
  }
  
  /// Obtiene estadísticas para admin
  Future<Map<String, dynamic>> getEstadisticasAdmin({
    DateTime? fechaInicio,
    DateTime? fechaFin,
  }) async {
    Map<String, String> queryParams = {};
    
    if (fechaInicio != null) {
      queryParams['fecha_inicio'] = fechaInicio.toIso8601String().split('T')[0];
    }
    if (fechaFin != null) {
      queryParams['fecha_fin'] = fechaFin.toIso8601String().split('T')[0];
    }
    
    Uri uri = Uri.parse('$baseUrl/accesos/admin/estadisticas')
        .replace(queryParameters: queryParams);
    
    final response = await http.get(
      uri,
      headers: {'Authorization': 'Bearer $token'},
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error: ${response.statusCode}');
    }
  }
  
  /// Obtiene solo accesos exitosos
  Future<List<Map<String, dynamic>>> getAccesosExitosos(int viviendaId) async {
    final data = await getAccesosVivienda(
      viviendaId: viviendaId,
      resultado: 'autorizado',
    );
    return List<Map<String, dynamic>>.from(data['accesos']);
  }
  
  /// Obtiene accesos de visitas
  Future<List<Map<String, dynamic>>> getAccesosVisitas(int viviendaId) async {
    final data = await getAccesosVivienda(viviendaId: viviendaId);
    final accesos = data['accesos'] as List;
    return accesos
        .where((a) => a['visita_nombres'] != null)
        .cast<Map<String, dynamic>>()
        .toList();
  }
}

// Uso:
// final service = AccesosService(token: 'your_token');
// final accesos = await service.getAccesosVivienda(viviendaId: 1);
// final stats = await service.getEstadisticasAdmin();
"""

# ============================================================================
# DOCUMENTACIÓN DE ARQUITECTURA
# ============================================================================

example_architecture = """
## Arquitectura Hexagonal - Accesos

### Capas Implementadas:

1. **Interfaces (Presentación)**
   - Archivo: `app/interfaces/routers/accesos_router.py`
   - Responsabilidad: Definir endpoints HTTP y validar requests
   - Endpoints:
     - GET /api/v1/accesos/vivienda/{vivienda_id}
     - GET /api/v1/accesos/admin/estadisticas

2. **Application (Servicios)**
   - Archivo: `app/application/services/accesos_service.py`
   - Responsabilidad: Lógica de negocio
   - Métodos:
     - obtener_accesos_vivienda(): Consulta accesos con filtros
     - obtener_detalles_acceso(): Enriquece datos de acceso
     - obtener_estadisticas_admin(): Calcula KPIs globales

3. **Infrastructure (Persistencia)**
   - Modelos: `app/infrastructure/db/models.py`
     - Acceso: Registro de entrada/salida
     - Vivienda: Ubicación
     - Persona: Guardia, residente
     - Visita: Información de visita
   - Database: PostgreSQL con SQLAlchemy ORM

### Flujo de Datos:

```
Frontend (Flutter)
    ↓
[accesos_router.py] - Endpoint HTTP
    ↓
[AccesosService] - Lógica de negocio
    ↓
[SQLAlchemy Models] - ORM
    ↓
[PostgreSQL] - Base de datos
    ↑
[Response] - JSON con datos enriquecidos
```

### Características:

- ✅ Separación de responsabilidades
- ✅ Fácil de testear
- ✅ Reutilizable (servicios independientes)
- ✅ Mantenible (cambios en BD no afectan endpoints)
- ✅ Escalable (agregar funcionalidad es sencillo)

### Ejemplo: Agregar un nuevo filtro

1. Agregar parámetro en `accesos_router.py`
2. Pasar a `AccesosService.obtener_accesos_vivienda()`
3. Aplicar filtro en la consulta SQLAlchemy
4. No requiere cambios en modelos

"""

if __name__ == "__main__":
    print("Ejemplos de integración para endpoints de Accesos")
    print("\n" + "="*70)
    print("EJEMPLO 1: Consultar Accesos por Vivienda")
    print("="*70)
    print(example_get_accesos_vivienda)
    
    print("\n" + "="*70)
    print("EJEMPLO 2: Estadísticas para Admin")
    print("="*70)
    print(example_get_estadisticas_admin)
    
    print("\n" + "="*70)
    print("EJEMPLO 3: Widget Flutter")
    print("="*70)
    print(example_widget_accesos)
    
    print("\n" + "="*70)
    print("EJEMPLO 4: Servicio Reutilizable")
    print("="*70)
    print(example_service)
    
    print("\n" + "="*70)
    print("ARQUITECTURA HEXAGONAL")
    print("="*70)
    print(example_architecture)
