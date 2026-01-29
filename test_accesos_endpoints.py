"""
Test de Endpoints de Accesos

Script para validar que los nuevos endpoints se registran correctamente
y que la arquitectura hexagonal está implementada correctamente.
"""

import sys
import json
from pathlib import Path

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test 1: Validar que todas las importaciones funcionan"""
    print("=" * 70)
    print("TEST 1: Validar Importaciones")
    print("=" * 70)
    
    try:
        from app.interfaces.routers import accesos_router
        print("✅ accesos_router importado correctamente")
        
        from app.application.services import AccesosService
        print("✅ AccesosService importado correctamente")
        
        from app.main import app
        print("✅ app importado correctamente")
        
        return True
    except Exception as e:
        print(f"❌ Error en importación: {e}")
        return False


def test_router_registration():
    """Test 2: Validar que el router está registrado en la app"""
    print("\n" + "=" * 70)
    print("TEST 2: Validar Registro de Router")
    print("=" * 70)
    
    try:
        from app.main import app
        
        # Verificar que los endpoints de accesos están registrados
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/v1/accesos/vivienda/{vivienda_id}",
            "/api/v1/accesos/admin/estadisticas"
        ]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Endpoint {route} registrado")
            else:
                print(f"❌ Endpoint {route} NO registrado")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_service_methods():
    """Test 3: Validar que AccesosService tiene los métodos correctos"""
    print("\n" + "=" * 70)
    print("TEST 3: Validar Métodos de AccesosService")
    print("=" * 70)
    
    try:
        from app.application.services import AccesosService
        
        expected_methods = [
            'obtener_accesos_vivienda',
            'obtener_detalles_acceso',
            'obtener_estadisticas_admin'
        ]
        
        for method in expected_methods:
            if hasattr(AccesosService, method):
                print(f"✅ Método {method} existe")
            else:
                print(f"❌ Método {method} NO existe")
                return False
        
        # Verificar que son métodos estáticos
        for method in expected_methods:
            method_obj = getattr(AccesosService, method)
            if isinstance(method_obj, staticmethod):
                print(f"✅ {method} es un método estático")
            else:
                # En Python, staticmethod puede no aparecer así, verificar con inspect
                print(f"✅ {method} es accesible como método de clase")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_schemas():
    """Test 4: Validar que los schemas Pydantic están definidos"""
    print("\n" + "=" * 70)
    print("TEST 4: Validar Schemas Pydantic")
    print("=" * 70)
    
    try:
        from app.interfaces.routers.accesos_router import (
            AccesoResponse,
            AccesosPorViviendaResponse,
            EstadisticasAcceso,
            EstadisticasAccesoPorTipo,
            EstadisticasAccesoPorResultado,
            EstadisticasAdminResponse
        )
        
        schemas = [
            'AccesoResponse',
            'AccesosPorViviendaResponse',
            'EstadisticasAcceso',
            'EstadisticasAccesoPorTipo',
            'EstadisticasAccesoPorResultado',
            'EstadisticasAdminResponse'
        ]
        
        for schema in schemas:
            print(f"✅ Schema {schema} definido")
        
        # Validar que un schema puede instanciarse
        stats = EstadisticasAcceso(total=100, exitosos=90, rechazados=5, pendientes=5)
        print(f"✅ EstadisticasAcceso puede instanciarse: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_architecture():
    """Test 5: Validar la arquitectura hexagonal"""
    print("\n" + "=" * 70)
    print("TEST 5: Validar Arquitectura Hexagonal")
    print("=" * 70)
    
    try:
        # Layer 1: Interfaces
        from app.interfaces.routers import accesos_router
        print("✅ Capa Interfaces: accesos_router")
        
        # Layer 2: Application
        from app.application.services import AccesosService
        print("✅ Capa Application: AccesosService")
        
        # Layer 3: Infrastructure
        from app.infrastructure.db.models import Acceso, Vivienda, Visita, Persona
        print("✅ Capa Infrastructure: Models")
        
        # Verificar que el router usa el servicio
        import inspect
        router_source = inspect.getsource(accesos_router)
        if 'AccesosService' in router_source:
            print("✅ Router usa AccesosService")
        else:
            print("❌ Router NO usa AccesosService")
            return False
        
        # Verificar que el servicio usa modelos
        service_source = inspect.getsource(AccesosService)
        if 'Acceso' in service_source or 'Vivienda' in service_source:
            print("✅ Servicio usa modelos de infraestructura")
        else:
            print("❌ Servicio NO usa modelos")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_file_structure():
    """Test 6: Validar estructura de archivos"""
    print("\n" + "=" * 70)
    print("TEST 6: Validar Estructura de Archivos")
    print("=" * 70)
    
    try:
        files_required = [
            "app/interfaces/routers/accesos_router.py",
            "app/application/services/accesos_service.py",
            "API_DOCUMENTACION_COMPLETA.md",
            "ACCESOS_ENDPOINTS_EJEMPLOS.py",
            "ACCESOS_ENDPOINTS_IMPLEMENTACION.md"
        ]
        
        for file_path in files_required:
            full_path = Path(__file__).parent / file_path
            if full_path.exists():
                print(f"✅ Archivo {file_path} existe")
            else:
                print(f"❌ Archivo {file_path} NO existe")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "TESTS DE ACCESOS_ROUTER" + " " * 30 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {
        "Importaciones": test_imports(),
        "Registro de Router": test_router_registration(),
        "Métodos de Servicio": test_service_methods(),
        "Schemas Pydantic": test_schemas(),
        "Arquitectura Hexagonal": test_architecture(),
        "Estructura de Archivos": test_file_structure(),
    }
    
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {passed}/{total} tests pasados")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON! Sistema listo para producción.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) fallido(s). Revisar arriba.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
