#!/usr/bin/env python3
"""
Script de verificación para la configuración de zona horaria (genérico)
Ejecutar: python3 verificar_zona_horaria.py
"""

from datetime import datetime, timedelta
import pytz
import sys
import os

# Agregar el proyecto al path
sys.path.insert(0, os.path.dirname(__file__))

# Importar las funciones de utilidad
try:
    from app.infrastructure.utils.time_utils import (
        ahora,
        ahora_sin_tz,
        ahora_utc,
        convertir_a_local,
        convertir_de_local_a_utc,
        fecha_hoy,
        es_vigente,
        ha_expirado,
        obtener_zona_horaria
    )
    from app.config import get_settings
    print("✓ Módulos importados correctamente\n")
except ImportError as e:
    print(f"✗ Error al importar módulos: {e}")
    sys.exit(1)

def verificar_zona_horaria():
    """Verifica que la zona horaria esté configurada correctamente"""
    settings = get_settings()
    
    print("=" * 70)
    print("VERIFICACIÓN DE ZONA HORARIA (GENÉRICA Y CONFIGURABLE)")
    print("=" * 70)
    
    # Test 1: Zona horaria configurada
    print("\n1. CONFIGURACIÓN:")
    print("-" * 70)
    
    try:
        tz = obtener_zona_horaria()
        print(f"   Zona configurada: {settings.TIMEZONE}")
        print(f"   Objeto timezone: {tz}")
        print("   ✓ CORRECTO: Zona horaria válida")
    except ValueError as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    # Test 2: Hora actual en diferentes zonas
    print("\n2. HORA ACTUAL EN DIFERENTES ZONAS:")
    print("-" * 70)
    
    ahora_utc_actual = ahora_utc()
    ahora_local = ahora()
    ahora_local_sin_tz = ahora_sin_tz()
    
    print(f"   UTC:              {ahora_utc_actual}")
    print(f"   Local (con TZ):   {ahora_local}")
    print(f"   Local (sin TZ):   {ahora_local_sin_tz}")
    
    # Verificar diferencia
    diferencia = ahora_utc_actual.replace(tzinfo=None) - ahora_local_sin_tz
    diferencia_horas = diferencia.total_seconds() / 3600
    
    print(f"\n   Diferencia UTC - Local: {diferencia_horas:.1f} horas")
    print("   ✓ CORRECTO: Conversión consistente")
    
    # Test 3: Fecha hoy
    print("\n3. FECHA HOY (MEDIANOCHE EN ZONA LOCAL):")
    print("-" * 70)
    
    hoy = fecha_hoy()
    print(f"   Fecha actual: {hoy}")
    print(f"   Hora:        {hoy.hour}:{hoy.minute}:{hoy.second}")
    
    if hoy.hour == 0 and hoy.minute == 0 and hoy.second == 0:
        print("   ✓ CORRECTO: Es medianoche")
    else:
        print("   ✗ ERROR: No es medianoche")
        return False
    
    # Test 4: Validación de vigencia
    print("\n4. VALIDACIÓN DE VIGENCIA:")
    print("-" * 70)
    
    inicio = ahora_sin_tz()
    fin = inicio + timedelta(hours=2)
    
    print(f"   Inicio: {inicio}")
    print(f"   Fin:    {fin}")
    
    if es_vigente(inicio, fin):
        print("   ✓ CORRECTO: Rango es vigente")
    else:
        print("   ✗ ERROR: Rango no es vigente")
        return False
    
    # Test 5: Validación de expiración
    print("\n5. VALIDACIÓN DE EXPIRACIÓN:")
    print("-" * 70)
    
    pasado = ahora_sin_tz() - timedelta(hours=1)
    futuro = ahora_sin_tz() + timedelta(hours=1)
    
    print(f"   Hace 1 hora: {pasado}")
    print(f"   En 1 hora:   {futuro}")
    
    if ha_expirado(pasado):
        print("   ✓ CORRECTO: Pasado ha expirado")
    else:
        print("   ✗ ERROR: Pasado no ha expirado")
        return False
    
    if not ha_expirado(futuro):
        print("   ✓ CORRECTO: Futuro no ha expirado")
    else:
        print("   ✗ ERROR: Futuro ha expirado")
        return False
    
    # Test 6: Conversión UTC ↔ Local
    print("\n6. CONVERSIÓN UTC ↔ ZONA HORARIA LOCAL:")
    print("-" * 70)
    
    # Crear un UTC datetime conocido
    utc_time = pytz.UTC.localize(datetime(2026, 1, 19, 19, 30, 0))
    local_time = convertir_a_local(utc_time)
    
    print(f"   UTC:      {utc_time}")
    print(f"   Local:    {local_time}")
    
    # Convertir de vuelta
    back_to_utc = convertir_de_local_a_utc(local_time)
    
    if back_to_utc.hour == 19 and back_to_utc.minute == 30:
        print("   ✓ CORRECTO: Conversión bidireccional")
    else:
        print("   ✗ ERROR: Conversión bidireccional inconsistente")
        return False
    
    # Test 7: Verificar que ahora() y ahora_sin_tz() son consistentes
    print("\n7. CONSISTENCIA ahora() vs ahora_sin_tz():")
    print("-" * 70)
    
    con_tz = ahora()
    sin_tz = ahora_sin_tz()
    
    con_tz_sin_tz = con_tz.replace(tzinfo=None)
    
    # Permitir pequeña diferencia de tiempo (algunos milisegundos)
    diff = abs((con_tz_sin_tz - sin_tz).total_seconds())
    
    print(f"   ahora() - TZ:         {con_tz}")
    print(f"   ahora_sin_tz():       {sin_tz}")
    print(f"   Diferencia:           {diff:.3f} segundos")
    
    if diff < 1:  # Tolerancia de 1 segundo
        print("   ✓ CORRECTO: Funciones son consistentes")
    else:
        print("   ✗ ERROR: Funciones no son consistentes")
        return False
    
    return True

def main():
    try:
        success = verificar_zona_horaria()
        
        print("\n" + "=" * 70)
        if success:
            print("✓ TODAS LAS VERIFICACIONES PASARON")
            print("=" * 70)
            print("\nLa zona horaria está correctamente configurada.")
            print(f"Puede cambiarla en .env: TIMEZONE=America/New_York")
            return 0
        else:
            print("✗ ALGUNAS VERIFICACIONES FALLARON")
            print("=" * 70)
            return 1
    except Exception as e:
        print(f"\n✗ ERROR durante verificación: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
