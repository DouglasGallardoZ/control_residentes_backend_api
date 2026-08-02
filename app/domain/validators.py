"""
Validadores de negocio para Guardin.
Implementa CV-01 (cédula), CV-02 (extranjero), CV-04 (edad), CV-06 (celular).
"""
import re
from datetime import date
from typing import Optional


def validar_cedula_ecuatoriana(cedula: str) -> bool:
    """CV-01: Valida cédula ecuatoriana usando algoritmo módulo 10."""
    if not cedula or not cedula.isdigit() or len(cedula) != 10:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0

    for i in range(9):
        producto = int(cedula[i]) * coeficientes[i]
        suma += producto if producto < 10 else producto - 9

    digito_verificador = 10 - (suma % 10)
    if digito_verificador == 10:
        digito_verificador = 0

    return digito_verificador == int(cedula[9])


def validar_identificacion(
    identificacion: str,
    tipo_identificacion: str = "Cedula",
) -> Optional[str]:
    """
    Valida identificación. Retorna mensaje de error o None si es válida.
    CV-01 para cédula, CV-02 para extranjero.
    """
    if not identificacion or not identificacion.strip():
        return "Error: la identificacion no puede estar vacia"

    if tipo_identificacion.lower() in ("Cedula", "ced"):
        if not identificacion.isdigit():
            return "Error: la cédula debe contener solo dígitos"
        if len(identificacion) != 10:
            return "Error: la cédula debe tener 10 dígitos"
        if not validar_cedula_ecuatoriana(identificacion):
            return "Error: número de cédula no válido"
    elif tipo_identificacion.lower() in ("pasaporte", "extranjera"):
        if len(identificacion) < 3 or len(identificacion) > 20:
            return "Error: identificación extranjera debe tener entre 3 y 20 caracteres"
    return None


def validar_edad_minima(fecha_nacimiento: date) -> Optional[str]:
    """CV-04: Valida edad >= 18 años y fecha no futura."""
    if fecha_nacimiento is None:
        return None

    hoy = date.today()

    if fecha_nacimiento > hoy:
        return (
            "Error: la fecha de nacimiento debe corresponder a una persona "
            "mayor de 18 años y no puede ser futura"
        )

    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1

    if edad < 18:
        return (
            "Error: la fecha de nacimiento debe corresponder a una persona "
            "mayor de 18 años y no puede ser futura"
        )
    return None


def validar_celular(celular: Optional[str]) -> Optional[str]:
    """CV-06: Valida formato de celular ecuatoriano (09XXXXXXXX)."""
    if celular is None or celular == "" or celular.strip() == "":
        return None

    if not re.match(r"^09\d{8}$", celular):
        return "Error: el celular debe tener formato 09XXXXXXXX (10 dígitos)"
    return None
