#!/usr/bin/env python3
"""
Script para validar contraseñas y verificar límite de 72 bytes UTF-8
"""

def validar_contraseña(password: str) -> tuple[bool, str]:
    """Valida que la contraseña cumpla con la política de seguridad"""
    password_bytes = password.encode('utf-8')
    
    if len(password) < 8:
        return False, "❌ Contraseña debe tener al menos 8 caracteres"
    if len(password_bytes) > 72:
        return False, f"❌ Contraseña demasiado larga. Máximo 72 bytes UTF-8 (tienes {len(password_bytes)}). Usa menos caracteres especiales/acentos."
    if not any(c.isupper() for c in password):
        return False, "❌ Contraseña debe contener al menos una mayúscula"
    if not any(c.isdigit() for c in password):
        return False, "❌ Contraseña debe contener al menos un número"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "❌ Contraseña debe contener al menos un carácter especial"
    
    return True, f"✅ Contraseña válida ({len(password_bytes)} bytes UTF-8)"


def analizar_contraseña(password: str):
    """Analiza una contraseña y muestra detalles"""
    password_bytes = password.encode('utf-8')
    
    print(f"\n{'='*60}")
    print(f"Contraseña: {password}")
    print(f"{'='*60}")
    print(f"Caracteres visuales: {len(password)}")
    print(f"Bytes UTF-8: {len(password_bytes)}")
    print(f"Límite bcrypt: 72 bytes")
    print(f"Espacio restante: {72 - len(password_bytes)} bytes")
    print()
    
    # Mostrar análisis de caracteres
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    print("Requisitos:")
    print(f"  {'✅' if len(password) >= 8 else '❌'} Mínimo 8 caracteres: {len(password)}")
    print(f"  {'✅' if len(password_bytes) <= 72 else '❌'} Máximo 72 bytes: {len(password_bytes)}")
    print(f"  {'✅' if has_upper else '❌'} Al menos 1 mayúscula")
    print(f"  {'✅' if has_digit else '❌'} Al menos 1 número")
    print(f"  {'✅' if has_special else '❌'} Al menos 1 carácter especial")
    
    valid, msg = validar_contraseña(password)
    print(f"\nResultado: {msg}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Ejemplos a probar
    ejemplos = [
        # Válidos
        ("MiPass@123", True),
        ("Secure#Password2024", True),
        ("TestPass123!", True),
        ("MyP@ssw0rd", True),
        
        # Inválidos - caracteres especiales que ocupan múltiples bytes
        ("MiP@ssw0rdÑoño2024", False),  # Ñ = 2 bytes
        ("Contraseña#123@", False),     # á = 2 bytes, ñ = 2 bytes
        
        # Inválidos - muy corto
        ("Pass@1", False),
        ("Short!", False),
        
        # Inválidos - sin mayúscula
        ("mypassword@123", False),
        
        # Inválidos - sin número
        ("MyPassword@Test", False),
        
        # Inválidos - sin carácter especial
        ("MyPassword123", False),
    ]
    
    print("\n" + "="*60)
    print("VALIDADOR DE CONTRASEÑAS - BACKEND API")
    print("="*60)
    
    for password, should_be_valid in ejemplos:
        analizar_contraseña(password)
    
    # Mostrar cómo caracteres UTF-8 afectan el límite
    print("\n" + "="*60)
    print("ANÁLISIS DE BYTES UTF-8")
    print("="*60 + "\n")
    
    caracteres_utf8 = {
        "ASCII (a)": "a",
        "Tilde (á)": "á",
        "Ñ": "ñ",
        "Emoji (😊)": "😊",
    }
    
    for desc, char in caracteres_utf8.items():
        bytes_count = len(char.encode('utf-8'))
        print(f"{desc}: {bytes_count} byte(s) - '{char}'")
    
    print("\n" + "="*60)
    print("EJEMPLOS DE CONTRASEÑAS MÁXIMAS")
    print("="*60 + "\n")
    
    # Crear contraseñas que usan exactamente 72 bytes
    max_ascii = "MiP@ssword" + "1" * 50 + "!"  # ~63 chars = 63 bytes
    max_mixed = "MiP@ssw0rd" + "A" * 50 + "!"  # 63 bytes
    
    analizar_contraseña(max_ascii)
    analizar_contraseña(max_mixed)
    
    # Mostrar contador
    print(f"\n{'='*60}")
    print(f"Total de ejemplos probados: {len(ejemplos)}")
    print(f"{'='*60}\n")
