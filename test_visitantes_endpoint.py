"""
Script de prueba para el endpoint GET /qr/visitantes/{persona_id}

Verifica:
1. Que se retornan visitantes asociados a una vivienda
2. Que funciona tanto para residentes como para miembros de familia
3. Que la respuesta tiene el formato correcto
4. Que maneja errores apropiadamente
"""

import requests
import json
from datetime import datetime
import sys

# Configuración
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your-bearer-token-here"  # Reemplazar con token válido

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_obtener_visitantes_exitoso():
    """Prueba obtener visitantes para un persona_id válido"""
    print("\n" + "="*60)
    print("TEST 1: Obtener visitantes - Caso exitoso")
    print("="*60)
    
    # Usar persona_id conocido (residente o miembro)
    persona_id = 1
    
    try:
        response = requests.get(
            f"{BASE_URL}/qr/visitantes/{persona_id}",
            headers=HEADERS,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validar estructura
            assert "vivienda_id" in data, "Falta vivienda_id"
            assert "manzana" in data, "Falta manzana"
            assert "villa" in data, "Falta villa"
            assert "visitantes" in data, "Falta visitantes"
            assert "total" in data, "Falta total"
            
            print(f"✅ Estructura válida")
            print(f"   Vivienda: Manzana {data['manzana']}, Villa {data['villa']}")
            print(f"   Total visitantes: {data['total']}")
            
            # Validar cada visitante
            if data['visitantes']:
                visitante = data['visitantes'][0]
                assert "visita_id" in visitante, "Falta visita_id en visitante"
                assert "identificacion" in visitante, "Falta identificacion"
                assert "nombres" in visitante, "Falta nombres"
                assert "apellidos" in visitante, "Falta apellidos"
                assert "fecha_creado" in visitante, "Falta fecha_creado"
                
                print(f"✅ Visitantes con estructura correcta")
                print(f"   Ejemplo: {visitante['nombres']} {visitante['apellidos']} ({visitante['identificacion']})")
            
            print(f"\n✅ TEST EXITOSO\n")
            return True
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False


def test_persona_no_encontrada():
    """Prueba cuando persona_id no existe"""
    print("\n" + "="*60)
    print("TEST 2: Persona no encontrada")
    print("="*60)
    
    persona_id = 99999  # ID que no existe
    
    try:
        response = requests.get(
            f"{BASE_URL}/qr/visitantes/{persona_id}",
            headers=HEADERS,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            data = response.json()
            print(f"✅ Retorna 404 como se esperaba")
            print(f"   Detalle: {data.get('detail', 'Sin mensaje')}")
            print(f"\n✅ TEST EXITOSO\n")
            return True
        else:
            print(f"❌ Se esperaba 404, se recibió {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False


def test_persona_sin_vivienda():
    """Prueba cuando la persona no tiene vivienda activa"""
    print("\n" + "="*60)
    print("TEST 3: Persona sin vivienda activa")
    print("="*60)
    
    # Primero crearía una persona sin asignarla a vivienda
    # Por ahora solo documentamos el caso
    persona_id = 2  # Ajustar según el caso real
    
    try:
        response = requests.get(
            f"{BASE_URL}/qr/visitantes/{persona_id}",
            headers=HEADERS,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            data = response.json()
            print(f"✅ Retorna 403 como se esperaba")
            print(f"   Detalle: {data.get('detail', 'Sin mensaje')}")
            print(f"\n✅ TEST EXITOSO\n")
            return True
        elif response.status_code == 200:
            print(f"⚠️  La persona tiene vivienda asociada (no es el caso de prueba)")
            return None
        else:
            print(f"❌ Error inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False


def test_sin_autorizacion():
    """Prueba sin token válido"""
    print("\n" + "="*60)
    print("TEST 4: Sin autorización (sin token)")
    print("="*60)
    
    headers_sin_token = {"Content-Type": "application/json"}
    persona_id = 1
    
    try:
        response = requests.get(
            f"{BASE_URL}/qr/visitantes/{persona_id}",
            headers=headers_sin_token,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"✅ Retorna 401 como se esperaba (no autorizado)")
            print(f"\n✅ TEST EXITOSO\n")
            return True
        else:
            print(f"⚠️  Status code: {response.status_code}")
            print(f"❌ Se esperaba 401")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False


def test_validar_fechas():
    """Valida que las fechas estén en formato ISO 8601"""
    print("\n" + "="*60)
    print("TEST 5: Validación de fechas (ISO 8601)")
    print("="*60)
    
    persona_id = 1
    
    try:
        response = requests.get(
            f"{BASE_URL}/qr/visitantes/{persona_id}",
            headers=HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['visitantes']:
                for visitante in data['visitantes']:
                    fecha_str = visitante['fecha_creado']
                    try:
                        fecha = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                        print(f"✅ Fecha válida: {fecha}")
                    except ValueError:
                        print(f"❌ Fecha inválida: {fecha_str}")
                        return False
                
                print(f"\n✅ TEST EXITOSO\n")
                return True
            else:
                print(f"⚠️  No hay visitantes para validar fechas")
                return None
        else:
            print(f"❌ Error al obtener visitantes: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False


def test_ordenamiento_fechas():
    """Valida que los visitantes estén ordenados por fecha descendente"""
    print("\n" + "="*60)
    print("TEST 6: Ordenamiento de visitantes por fecha")
    print("="*60)
    
    persona_id = 1
    
    try:
        response = requests.get(
            f"{BASE_URL}/qr/visitantes/{persona_id}",
            headers=HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            visitantes = data['visitantes']
            
            if len(visitantes) > 1:
                # Verificar orden descendente
                fechas = [
                    datetime.fromisoformat(v['fecha_creado'].replace('Z', '+00:00'))
                    for v in visitantes
                ]
                
                es_ordenado = all(
                    fechas[i] >= fechas[i+1]
                    for i in range(len(fechas)-1)
                )
                
                if es_ordenado:
                    print(f"✅ Visitantes ordenados correctamente (más recientes primero)")
                    print(f"   Primer visitante: {visitantes[0]['fecha_creado']}")
                    print(f"   Último visitante: {visitantes[-1]['fecha_creado']}")
                    print(f"\n✅ TEST EXITOSO\n")
                    return True
                else:
                    print(f"❌ Visitantes NO están en orden descendente")
                    return False
            else:
                print(f"⚠️  Solo hay 1 visitante, no se puede validar ordenamiento")
                return None
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False


def test_miembro_familia():
    """Prueba que funciona con miembros de familia (no solo residentes)"""
    print("\n" + "="*60)
    print("TEST 7: Endpoint funciona con miembros de familia")
    print("="*60)
    
    # persona_id de un miembro de familia conocido
    persona_id = 2  # Ajustar según el caso real
    
    try:
        response = requests.get(
            f"{BASE_URL}/qr/visitantes/{persona_id}",
            headers=HEADERS,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Funciona para miembros de familia")
            print(f"   Vivienda: {data['manzana']}-{data['villa']}")
            print(f"   Visitantes: {data['total']}")
            print(f"\n✅ TEST EXITOSO\n")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Persona no encontrada (verificar persona_id)")
            return None
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
        return False


def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "PRUEBAS DEL ENDPOINT /visitantes" + " "*10 + "║")
    print("╚" + "="*58 + "╝")
    
    resultados = {
        "Exitoso": 0,
        "Fallido": 0,
        "Omitido": 0
    }
    
    # Ejecutar tests
    tests = [
        test_obtener_visitantes_exitoso(),
        test_persona_no_encontrada(),
        test_sin_autorizacion(),
        test_validar_fechas(),
        test_ordenamiento_fechas(),
        test_miembro_familia(),
    ]
    
    # Contar resultados
    for resultado in tests:
        if resultado is True:
            resultados["Exitoso"] += 1
        elif resultado is False:
            resultados["Fallido"] += 1
        else:
            resultados["Omitido"] += 1
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    print(f"✅ Exitosos:  {resultados['Exitoso']}")
    print(f"❌ Fallidos:  {resultados['Fallido']}")
    print(f"⚠️  Omitidos:  {resultados['Omitido']}")
    print("="*60)
    
    if resultados['Fallido'] == 0:
        print("\n✅ TODAS LAS PRUEBAS PASARON\n")
        return 0
    else:
        print(f"\n❌ {resultados['Fallido']} PRUEBA(S) FALLARON\n")
        return 1


if __name__ == "__main__":
    # Notas de uso
    print("""
INSTRUCCIONES:
1. Actualizar TOKEN en el script con un bearer token válido
2. Ejecutar: python test_visitantes_endpoint.py
3. Revisar los resultados

REQUISITOS:
- El servidor debe estar corriendo en http://localhost:8000
- Debe haber datos de prueba en la BD (viviendas, personas, visitantes)
- El usuario autenticado debe tener permisos adecuados
    """)
    
    # Comentar esta línea si deseas usar este script para validar
    # sys.exit(main())
