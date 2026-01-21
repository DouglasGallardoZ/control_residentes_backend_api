#!/usr/bin/env python3
"""
Script de prueba para validar el endpoint GET /perfil/{firebase_uid}

Uso:
    python test_perfil_endpoint.py
"""

import requests
import json
from typing import Optional

# Configuración
API_BASE_URL = "http://localhost:8000/api/v1"
ENDPOINT = "/cuentas/perfil"

# Ejemplos de Firebase UID (reemplazar con valores reales)
TEST_FIREBASE_UID_RESIDENTE = "firebase_uid_example_residente"
TEST_FIREBASE_UID_MIEMBRO = "firebase_uid_example_miembro"
TEST_FIREBASE_UID_INVALIDO = "firebase_uid_inexistente"


def test_perfil_endpoint(firebase_uid: str, esperado_rol: Optional[str] = None):
    """
    Prueba el endpoint de perfil
    
    Args:
        firebase_uid: Firebase UID del usuario
        esperado_rol: Rol esperado (opcional)
    """
    url = f"{API_BASE_URL}{ENDPOINT}/{firebase_uid}"
    
    print(f"\n{'='*60}")
    print(f"Probando: GET {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Respuesta exitosa:")
            print(json.dumps(data, indent=2, default=str))
            
            # Validaciones
            campos_requeridos = [
                'persona_id', 'identificacion', 'nombres', 'apellidos',
                'estado', 'rol', 'vivienda', 'fecha_creado'
            ]
            
            campos_faltantes = [c for c in campos_requeridos if c not in data]
            if campos_faltantes:
                print(f"\n⚠️  Campos faltantes: {campos_faltantes}")
            
            # Validar rol
            if esperado_rol and data.get('rol') != esperado_rol:
                print(f"\n⚠️  Rol inesperado: {data.get('rol')} (esperado: {esperado_rol})")
            
            # Validar vivienda
            vivienda = data.get('vivienda', {})
            if 'manzana' not in vivienda or 'villa' not in vivienda:
                print(f"\n⚠️  Vivienda incompleta: {vivienda}")
            
            # Validar parentesco (debe estar solo si es miembro)
            parentesco = data.get('parentesco')
            if data.get('rol') == 'miembro_familia' and not parentesco:
                print(f"\n⚠️  Parentesco vacío para miembro de familia")
            elif data.get('rol') == 'residente' and parentesco:
                print(f"\n⚠️  Parentesco presente para residente (debe ser null)")
            
            print(f"\n✅ Todas las validaciones pasaron")
            
        elif response.status_code == 404:
            data = response.json()
            print(f"\n❌ Error 404:")
            print(json.dumps(data, indent=2))
            
        else:
            print(f"\n❌ Error {response.status_code}:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error de conexión: No se puede conectar a {API_BASE_URL}")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:8000")
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Error: Timeout después de 10 segundos")
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


def mostrar_schema():
    """Muestra el schema esperado"""
    print("\n" + "="*60)
    print("SCHEMA ESPERADO")
    print("="*60)
    
    schema = {
        "persona_id": "int (ID en BD)",
        "identificacion": "string (cédula/pasaporte)",
        "nombres": "string",
        "apellidos": "string",
        "correo": "string | null (email)",
        "celular": "string | null (teléfono)",
        "estado": "string ('activo' o 'inactivo')",
        "rol": "string ('residente' o 'miembro_familia')",
        "vivienda": {
            "manzana": "string",
            "villa": "string"
        },
        "parentesco": "string | null (padre, madre, hijo, hija, esposo, esposa, otro)",
        "fecha_creado": "datetime"
    }
    
    print(json.dumps(schema, indent=2))


def main():
    print("\n" + "="*60)
    print("PRUEBA DEL ENDPOINT: GET /cuentas/perfil/{firebase_uid}")
    print("="*60)
    
    # Mostrar schema
    mostrar_schema()
    
    # Test 1: Residente válido (si existe en BD)
    print("\n\n[TEST 1] Residente válido")
    test_perfil_endpoint(
        TEST_FIREBASE_UID_RESIDENTE,
        esperado_rol="residente"
    )
    
    # Test 2: Miembro de familia válido (si existe en BD)
    print("\n\n[TEST 2] Miembro de familia válido")
    test_perfil_endpoint(
        TEST_FIREBASE_UID_MIEMBRO,
        esperado_rol="miembro_familia"
    )
    
    # Test 3: Firebase UID inválido
    print("\n\n[TEST 3] Firebase UID inválido (404)")
    test_perfil_endpoint(TEST_FIREBASE_UID_INVALIDO)
    
    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60)
    
    print("\n📝 NOTAS:")
    print("- Reemplaza los valores de TEST_FIREBASE_UID_* con UIDs reales")
    print("- Asegúrate de que el servidor está corriendo: python -m uvicorn app.main:app --reload")
    print("- Los datos deben existir en la base de datos PostgreSQL")
    print("- Si obtienes 404, verifica que el Firebase UID existe en la tabla Cuenta")


if __name__ == "__main__":
    main()
