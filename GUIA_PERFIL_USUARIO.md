# 📋 Guía de Implementación - Endpoint GET /perfil

## Descripción General

El endpoint `GET /cuentas/perfil/{firebase_uid}` retorna toda la información del usuario necesaria para la app Flutter, incluyendo:

- ✅ Información personal (nombres, identificación, correo, celular)
- ✅ Rol del usuario (Residente o Miembro de Familia)
- ✅ Información de vivienda (Manzana y Villa)
- ✅ Parentesco (si es miembro de familia)
- ✅ Estado y fecha de creación

---

## Endpoint

```
GET /api/v1/cuentas/perfil/{firebase_uid}
```

**Firebase UID:** Se obtiene de `FirebaseAuth.instance.currentUser?.uid` en Flutter

---

## Respuesta Success (200 OK)

### Residente

```json
{
  "persona_id": 1,
  "identificacion": "1234567890",
  "nombres": "Juan",
  "apellidos": "Pérez López",
  "correo": "juan.perez@example.com",
  "celular": "+593987654321",
  "estado": "activo",
  "rol": "residente",
  "vivienda": {
    "manzana": "A",
    "villa": "101"
  },
  "parentesco": null,
  "fecha_creado": "2024-12-20T10:00:00"
}
```

### Miembro de Familia

```json
{
  "persona_id": 4,
  "identificacion": "2222222222",
  "nombres": "Ana",
  "apellidos": "Pérez García",
  "correo": "ana.perez@example.com",
  "celular": "+593987777777",
  "estado": "activo",
  "rol": "miembro_familia",
  "vivienda": {
    "manzana": "A",
    "villa": "101"
  },
  "parentesco": "hija",
  "fecha_creado": "2024-12-24T10:00:00"
}
```

---

## Errores Posibles

| Código | Error | Causa |
|--------|-------|-------|
| **404** | `"Cuenta no encontrada"` | Firebase UID no existe, cuenta está bloqueada o eliminada |
| **404** | `"Usuario no es residente ni miembro de familia activo"` | Persona no tiene relación activa como residente o miembro |
| **500** | `"Persona no encontrada en BD"` | Error de integridad de BD (raro) |
| **500** | `"Vivienda no encontrada"` | Error de relación con vivienda (raro) |

---

## Flujo de Implementación en Flutter

### 1. Obtener Firebase UID

```dart
import 'package:firebase_auth/firebase_auth.dart';

final firebaseUser = FirebaseAuth.instance.currentUser;
if (firebaseUser == null) {
  // Usuario no autenticado
  return;
}

final firebaseUid = firebaseUser.uid;
```

### 2. Llamar el endpoint

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> obtenerPerfil(String firebaseUid) async {
  final url = 'http://localhost:8000/api/v1/cuentas/perfil/$firebaseUid';
  
  try {
    final response = await http.get(Uri.parse(url));
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 404) {
      throw Exception('Usuario no encontrado');
    } else {
      throw Exception('Error: ${response.body}');
    }
  } catch (e) {
    throw Exception('Error de conexión: $e');
  }
}
```

### 3. Usar la información del perfil

```dart
void loadUserProfile() async {
  final firebaseUid = FirebaseAuth.instance.currentUser?.uid;
  if (firebaseUid == null) return;
  
  try {
    final perfil = await obtenerPerfil(firebaseUid);
    
    final nombres = '${perfil['nombres']} ${perfil['apellidos']}';
    final rol = perfil['rol']; // "residente" o "miembro_familia"
    final manzana = perfil['vivienda']['manzana'];
    final villa = perfil['vivienda']['villa'];
    
    print('Nombre: $nombres');
    print('Rol: $rol');
    print('Vivienda: $manzana-$villa');
    
    // Guardar en estado local
    setState(() {
      _perfil = perfil;
    });
    
    // Mostrar/ocultar opciones según rol
    _configurarMenusPorRol(rol);
    
  } catch (e) {
    print('Error: $e');
    mostrarError('No se pudo cargar el perfil');
  }
}

void _configurarMenusPorRol(String rol) {
  if (rol == 'residente') {
    // Opciones para residente
    mostrarOpcion('Generar QR Propio');
    mostrarOpcion('Gestionar Familia');
    mostrarOpcion('Mis QRs Generados');
  } else if (rol == 'miembro_familia') {
    // Opciones para miembro
    mostrarOpcion('Generar QR Propio');
    mostrarOpcion('Mi Parentesco: ${_perfil['parentesco']}');
  }
}
```

### 4. Creación de Modelo Dart (Recomendado)

```dart
class PerfilUsuario {
  final int personaId;
  final String identificacion;
  final String nombres;
  final String apellidos;
  final String? correo;
  final String? celular;
  final String estado;
  final String rol;
  final ViviendaInfo vivienda;
  final String? parentesco;
  final DateTime fechaCreado;

  PerfilUsuario({
    required this.personaId,
    required this.identificacion,
    required this.nombres,
    required this.apellidos,
    this.correo,
    this.celular,
    required this.estado,
    required this.rol,
    required this.vivienda,
    this.parentesco,
    required this.fechaCreado,
  });

  String get nombreCompleto => '$nombres $apellidos';

  bool get esResidente => rol == 'residente';
  bool get esMiembro => rol == 'miembro_familia';

  factory PerfilUsuario.fromJson(Map<String, dynamic> json) {
    return PerfilUsuario(
      personaId: json['persona_id'],
      identificacion: json['identificacion'],
      nombres: json['nombres'],
      apellidos: json['apellidos'],
      correo: json['correo'],
      celular: json['celular'],
      estado: json['estado'],
      rol: json['rol'],
      vivienda: ViviendaInfo.fromJson(json['vivienda']),
      parentesco: json['parentesco'],
      fechaCreado: DateTime.parse(json['fecha_creado']),
    );
  }
}

class ViviendaInfo {
  final String manzana;
  final String villa;

  ViviendaInfo({
    required this.manzana,
    required this.villa,
  });

  String get direccion => '$manzana-$villa';

  factory ViviendaInfo.fromJson(Map<String, dynamic> json) {
    return ViviendaInfo(
      manzana: json['manzana'],
      villa: json['villa'],
    );
  }
}

// Servicio para obtener perfil
class PerfilService {
  static const String baseUrl = 'http://localhost:8000/api/v1';

  static Future<PerfilUsuario> obtenerMiPerfil(String firebaseUid) async {
    final url = '$baseUrl/cuentas/perfil/$firebaseUid';
    
    try {
      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        return PerfilUsuario.fromJson(json);
      } else if (response.statusCode == 404) {
        throw PerfilNoEncontradoException();
      } else {
        throw Exception('Error ${response.statusCode}: ${response.body}');
      }
    } on SocketException {
      throw ConexionException();
    }
  }
}

// Excepciones personalizadas
class PerfilNoEncontradoException implements Exception {
  final String mensaje = 'Perfil de usuario no encontrado';
}

class ConexionException implements Exception {
  final String mensaje = 'Error de conexión con el servidor';
}
```

### 5. Usar con Provider (Patrón recomendado)

```dart
import 'package:provider/provider.dart';

class PerfilProvider extends ChangeNotifier {
  PerfilUsuario? _perfil;
  bool _cargando = false;
  String? _error;

  PerfilUsuario? get perfil => _perfil;
  bool get cargando => _cargando;
  String? get error => _error;

  bool get esResidente => _perfil?.esResidente ?? false;
  bool get esMiembro => _perfil?.esMiembro ?? false;

  Future<void> cargarPerfil(String firebaseUid) async {
    _cargando = true;
    _error = null;
    notifyListeners();

    try {
      _perfil = await PerfilService.obtenerMiPerfil(firebaseUid);
      _cargando = false;
      notifyListeners();
    } on PerfilNoEncontradoException {
      _error = 'Usuario no encontrado en el sistema';
      _cargando = false;
      notifyListeners();
    } on ConexionException {
      _error = 'No hay conexión con el servidor';
      _cargando = false;
      notifyListeners();
    } catch (e) {
      _error = 'Error: $e';
      _cargando = false;
      notifyListeners();
    }
  }
}

// En main.dart
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => PerfilProvider()),
      ],
      child: MyApp(),
    ),
  );
}

// En pantalla
class MiPantalla extends StatefulWidget {
  @override
  State<MiPantalla> createState() => _MiPantallaState();
}

class _MiPantallaState extends State<MiPantalla> {
  @override
  void initState() {
    super.initState();
    final firebaseUid = FirebaseAuth.instance.currentUser?.uid;
    if (firebaseUid != null) {
      Future.microtask(
        () => context.read<PerfilProvider>().cargarPerfil(firebaseUid),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<PerfilProvider>(
      builder: (context, provider, _) {
        if (provider.cargando) {
          return CircularProgressIndicator();
        }

        if (provider.error != null) {
          return Text('Error: ${provider.error}');
        }

        final perfil = provider.perfil;
        if (perfil == null) {
          return Text('No hay datos');
        }

        return Column(
          children: [
            Text('Nombre: ${perfil.nombreCompleto}'),
            Text('Rol: ${perfil.rol}'),
            Text('Vivienda: ${perfil.vivienda.direccion}'),
            if (perfil.esMiembro) 
              Text('Parentesco: ${perfil.parentesco}'),
          ],
        );
      },
    );
  }
}
```

---

## Casos de Uso Comunes

### 1. Cargar datos al iniciar sesión

```dart
Future<void> handleLogin() async {
  try {
    // Firebase Auth
    await FirebaseAuth.instance.signInWithEmailAndPassword(
      email: emailController.text,
      password: passwordController.text,
    );
    
    // Obtener Firebase UID
    final firebaseUid = FirebaseAuth.instance.currentUser?.uid;
    if (firebaseUid != null) {
      // Cargar perfil
      final perfil = await PerfilService.obtenerMiPerfil(firebaseUid);
      
      // Guardar localmente
      await SharedPreferences.getInstance().then((prefs) {
        prefs.setString('perfil_json', jsonEncode(perfil));
      });
      
      // Navegar según rol
      if (perfil.esResidente) {
        Navigator.of(context).pushReplacementNamed('/home_residente');
      } else if (perfil.esMiembro) {
        Navigator.of(context).pushReplacementNamed('/home_miembro');
      }
    }
  } catch (e) {
    mostrarError('Error al iniciar sesión: $e');
  }
}
```

### 2. Mostrar información de perfil

```dart
Widget mostrarTarjetaPerfil() {
  return Consumer<PerfilProvider>(
    builder: (context, provider, _) {
      final perfil = provider.perfil;
      if (perfil == null) return SizedBox();

      return Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                perfil.nombreCompleto,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('ID: ${perfil.identificacion}'),
              Text('Email: ${perfil.correo ?? "N/A"}'),
              Text('Teléfono: ${perfil.celular ?? "N/A"}'),
              Text('Vivienda: ${perfil.vivienda.direccion}'),
              Text('Rol: ${perfil.rol}'),
              if (perfil.esMiembro)
                Text('Parentesco: ${perfil.parentesco}'),
            ],
          ),
        ),
      );
    },
  );
}
```

### 3. Validar permisos según rol

```dart
bool tienePermisoPara(String accion, PerfilUsuario perfil) {
  switch (accion) {
    case 'generar_qr_propio':
      return perfil.esResidente || perfil.esMiembro;
    
    case 'gestionar_familia':
      return perfil.esResidente;
    
    case 'modificar_datos':
      return perfil.esResidente;
    
    default:
      return false;
  }
}
```

---

## Variables de Entorno

Para producción, usar variables de entorno para la URL base:

```dart
const String API_BASE_URL = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000/api/v1',
);
```

Lanzar app con:
```bash
flutter run --dart-define=API_BASE_URL=https://api.production.com/api/v1
```

---

## Testing

### Test Unitario

```dart
test('PerfilUsuario se crea desde JSON correctamente', () {
  final json = {
    'persona_id': 1,
    'identificacion': '1234567890',
    'nombres': 'Juan',
    'apellidos': 'Pérez',
    'correo': 'juan@example.com',
    'celular': '+593987654321',
    'estado': 'activo',
    'rol': 'residente',
    'vivienda': {
      'manzana': 'A',
      'villa': '101',
    },
    'parentesco': null,
    'fecha_creado': '2024-12-20T10:00:00',
  };

  final perfil = PerfilUsuario.fromJson(json);

  expect(perfil.personaId, 1);
  expect(perfil.nombres, 'Juan');
  expect(perfil.rol, 'residente');
  expect(perfil.esResidente, true);
  expect(perfil.esMiembro, false);
});
```

### Test de Integración

```dart
testWidgets('Cargar y mostrar perfil', (WidgetTester tester) async {
  await tester.pumpWidget(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => PerfilProvider()),
      ],
      child: MaterialApp(home: MiPantalla()),
    ),
  );

  // Simular carga
  await tester.pumpAndSettle();

  // Verificar que se muestran los datos
  expect(find.text('Nombre: Juan Pérez'), findsOneWidget);
  expect(find.text('Rol: residente'), findsOneWidget);
});
```

---

## Performance Tips

1. **Cache local:** Guardar el perfil en SharedPreferences o Hive para evitar requests repetidos
2. **Lazy loading:** Cargar el perfil solo cuando sea necesario (después de login)
3. **Timeout:** Establecer timeout en las requests HTTP (máximo 10 segundos)
4. **Retry logic:** Reintentar en caso de fallo de conexión

```dart
Future<PerfilUsuario> obtenerPerfilConReintento(
  String firebaseUid, {
  int maxReintentos = 3,
}) async {
  int intento = 0;
  
  while (intento < maxReintentos) {
    try {
      return await PerfilService.obtenerMiPerfil(firebaseUid)
          .timeout(Duration(seconds: 10));
    } catch (e) {
      intento++;
      if (intento >= maxReintentos) rethrow;
      await Future.delayed(Duration(seconds: 2)); // Esperar antes de reintentar
    }
  }
  
  throw Exception('Máximo de reintentos alcanzado');
}
```

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `404 - Cuenta no encontrada` | Verificar que el Firebase UID es correcto y la cuenta existe en BD |
| `404 - Usuario no es residente` | La persona no tiene un registro como ResidenteVivienda activo |
| Conexión rechazada | Verificar que el servidor está corriendo en `localhost:8000` |
| CORS error | Verificar configuración de CORS en FastAPI |
| Firebase UID inválido | Asegurar que el usuario está autenticado en Firebase antes de llamar el endpoint |

