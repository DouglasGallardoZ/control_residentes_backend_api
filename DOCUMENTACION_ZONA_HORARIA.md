# Documentación de Zona Horaria - Índice

## 📋 Archivos de Documentación

### 1. **ZONA_HORARIA_CONFIGURABLE.md** (Principal - Comienza aquí)
- Explicación detallada del problema y solución
- Configuración en diferentes ambientes (.env, Docker, etc.)
- Tabla completa de 30+ zonas horarias soportadas
- Ejemplos de uso
- FAQ detallado
- Consideraciones de seguridad y migraciones

**Para**: Entender completamente cómo funciona y cómo configurarlo

---

### 2. **ZONA_HORARIA_README.md** (Resumen Rápido)
- Resumen ejecutivo en 1 página
- Tabla de cambios principales
- Cómo cambiar de zona rápidamente
- Lista de funciones genéricas disponibles

**Para**: Referencia rápida, onboarding rápido

---

### 3. **REFACTORING_ZONA_HORARIA.md** (Detalles Técnicos)
- Problema identificado y solución implementada
- Comparación antes/después del código
- Matriz de cambios
- Tabla de configuración por región
- Ejemplo de migración de código
- Comparación visual

**Para**: Entender el cambio de específico a genérico

---

## 🔧 Script de Verificación

### **verificar_zona_horaria.py**
Script con 7 tests para verificar la configuración:
1. Zona horaria válida
2. Hora en diferentes zonas
3. Fecha hoy (medianoche)
4. Validación de vigencia
5. Validación de expiración
6. Conversión UTC ↔ Local
7. Consistencia de funciones

```bash
python3 verificar_zona_horaria.py
```

---

## 📦 Módulo Importado

### **/app/infrastructure/utils/time_utils.py**
Módulo genérico con funciones:

| Función | Descripción |
|---------|-------------|
| `ahora()` | Hora actual con timezone |
| `ahora_sin_tz()` | Hora actual para BD (recomendado) |
| `ahora_utc()` | Hora en UTC |
| `fecha_hoy()` | Fecha actual a medianoche |
| `obtener_zona_horaria()` | Obtiene zona configurada |
| `convertir_a_local(utc)` | UTC → Zona local |
| `convertir_de_local_a_utc(local)` | Zona local → UTC |
| `es_vigente(inicio, fin)` | ¿Está vigente? |
| `ha_expirado(fin)` | ¿Ha expirado? |

**Deprecated (pero todavía funcionan)**:
- `ahora_sin_tz()` → use `ahora_sin_tz()`
- `fecha_hoy()` → use `fecha_hoy()`
- `convertir_a_colombia()` → use `convertir_a_local()`
- `convertir_de_colombia_a_utc()` → use `convertir_de_local_a_utc()`

---

## ⚙️ Configuración

### En **config.py**
```python
class Settings(BaseSettings):
    TIMEZONE: str = "America/Bogota"  # Configurable
```

### En **.env** (Recomendado)
```bash
TIMEZONE=America/Bogota      # Por defecto (Colombia)
TIMEZONE=America/Quito       # Ecuador
TIMEZONE=America/Lima        # Perú
TIMEZONE=Europe/Madrid       # España
TIMEZONE=UTC                 # UTC
```

### En **docker-compose.yml**
```yaml
environment:
  TIMEZONE: "America/Bogota"
```

---

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencia
pip install pytz

# 2. Resetear BD
docker-compose down -v
docker-compose up -d

# 3. Verificar
python3 verificar_zona_horaria.py

# 4. Para cambiar zona: editar .env y reiniciar
TIMEZONE=America/Quito
docker-compose restart
```

---

## 📊 Cambios Realizados

| Componente | Tipo de Cambio | Detalles |
|-----------|--------|---------|
| **config.py** | 📝 Modificado | +1 setting TIMEZONE |
| **time_utils.py** | 🆕 Creado | Módulo genérico (240 líneas) |
| **models.py** | 📝 Modificado | 20+ defaults → `lambda: ahora_sin_tz()` |
| **Routers** (9) | 📝 Modificado | `datetime.utcnow()` → `ahora_sin_tz()` |
| **auth.py** | 📝 Modificado | JWT expiry → `ahora_sin_tz()` |
| **domain/entities** | 📝 Modificado | Validaciones → `ahora_sin_tz()` |
| **requirements.txt** | 📝 Modificado | +pytz |

---

## 🌍 Zonas Horarias Soportadas (Ejemplos)

| Región | TIMEZONE | UTC |
|--------|----------|-----|
| Colombia (Bogotá) | `America/Bogota` | UTC-5 |
| Ecuador (Quito) | `America/Quito` | UTC-5 |
| Perú (Lima) | `America/Lima` | UTC-5 |
| México | `America/Mexico_City` | UTC-6 (UTC-5 verano) |
| Nueva York | `America/New_York` | UTC-5 (UTC-4 verano) |
| Los Ángeles | `America/Los_Angeles` | UTC-8 (UTC-7 verano) |
| Brasil (São Paulo) | `America/Sao_Paulo` | UTC-3 |
| España (Madrid) | `Europe/Madrid` | UTC+1 (UTC+2 verano) |
| Londres | `Europe/London` | UTC+0 (UTC+1 verano) |
| Francia (París) | `Europe/Paris` | UTC+1 (UTC+2 verano) |
| Japón (Tokio) | `Asia/Tokyo` | UTC+9 |
| India (Delhi) | `Asia/Kolkata` | UTC+5:30 |
| UTC | `UTC` | UTC+0 |

**Ver lista completa**: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

---

## ✅ Verificación de Instalación

```bash
# Verificar que pytz está instalado
python3 -c "import pytz; print('✓ pytz instalado')"

# Verificar que el módulo se importa correctamente
python3 -c "
from app.infrastructure.utils.time_utils import ahora, obtener_zona_horaria
from app.config import get_settings
settings = get_settings()
print(f'✓ TIMEZONE configurado: {settings.TIMEZONE}')
print(f'✓ Zona horaria actual: {obtener_zona_horaria()}')
print(f'✓ Hora actual: {ahora()}')
"

# Ejecutar script de verificación completo
python3 verificar_zona_horaria.py
```

---

## 🔄 Cambiar de Zona Horaria (Ejemplo: De Colombia a Perú)

```bash
# 1. Editar .env
TIMEZONE=America/Lima

# 2. Reiniciar container
docker-compose restart

# 3. Verificar
python3 verificar_zona_horaria.py

# ✓ Hecho. Toda la aplicación ahora usa hora de Perú.
# Sin cambios de código.
```

---

## 📝 Notas Importantes

### Colombia y Ecuador NO tienen DST (Daylight Saving Time)
- Zona horaria permanece UTC-5 todo el año
- Más zonas (como Nueva York, Madrid) sí cambian con DST
- `pytz` maneja automáticamente estos cambios

### Cambiar zona afecta:
- ✅ Nuevos timestamps (BD, logs, API)
- ✅ Validación de vigencia de QR
- ✅ Expiración de JWT
- ❌ Datos históricos (ya tienen su zona)

### Compatibilidad hacia atrás:
- Funciones antiguas (`ahora_sin_tz`) aún funcionan
- Se marcan como DEPRECADAS
- Migración gradual, no obligatoria

---

## 📞 Soporte

Si necesitas:
- **Entender cómo funciona**: Lee `ZONA_HORARIA_CONFIGURABLE.md`
- **Cambiar de zona rápido**: Lee `ZONA_HORARIA_README.md`
- **Entender el refactoring**: Lee `REFACTORING_ZONA_HORARIA.md`
- **Verificar que funciona**: Ejecuta `python3 verificar_zona_horaria.py`

---

## 📚 Documentación Relacionada

- **Código**: `/app/infrastructure/utils/time_utils.py`
- **Configuración**: `/app/config.py` (setting `TIMEZONE`)
- **Modelos**: `/app/infrastructure/db/models.py` (20+ defaults)
- **Tests**: `pytest` con diferentes `TIMEZONE` en fixtures

---

**Última actualización**: 2026-01-19
**Versión**: 2.0 (Genérica y Configurable)
