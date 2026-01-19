# Guía de Contribución

¡Gracias por tu interés en contribuir a Residencial API! Este documento proporciona pautas y instrucciones para contribuir al proyecto.

## 📋 Tabla de Contenidos

1. [Código de Conducta](#código-de-conducta)
2. [Primeros Pasos](#primeros-pasos)
3. [Cómo Reportar Problemas](#cómo-reportar-problemas)
4. [Cómo Sugerir Mejoras](#cómo-sugerir-mejoras)
5. [Proceso de Pull Request](#proceso-de-pull-request)
6. [Estándares de Código](#estándares-de-código)
7. [Proceso de Commit](#proceso-de-commit)

---

## Código de Conducta

### Nuestro Compromiso

Nos comprometemos a proporcionar un ambiente acogedor y libre de acoso para todos, independientemente de edad, tamaño corporal, discapacidad, etnia, identidad y expresión de género, nivel de experiencia, nacionalidad, apariencia personal, raza, religión o identidad y orientación sexual.

### Nuestras Normas

Ejemplos de comportamiento que contribuyen a crear un ambiente positivo:

- Usar un lenguaje acogedor e inclusivo
- Ser respetuoso con los puntos de vista y experiencias diferentes
- Aceptar crítica constructiva
- Enfocarse en lo que es mejor para la comunidad
- Mostrar empatía hacia otros miembros de la comunidad

Ejemplos de comportamiento inaceptable:

- Uso de lenguaje o imágenes sexualizadas
- Ataques personales
- Trolling o comentarios insultos/degradantes
- Acoso público o privado
- Publicación de información privada de otros

---

## Primeros Pasos

### Configuración del Entorno de Desarrollo

```bash
# 1. Fork el repositorio en GitHub
# 2. Clona tu fork
git clone https://github.com/tu-usuario/backend-api.git
cd backend-api

# 3. Agrega upstream remoto
git remote add upstream https://github.com/original-repo/backend-api.git

# 4. Crea rama de desarrollo
git checkout -b develop
git pull upstream develop

# 5. Crea entorno virtual
python3.12 -m venv venv
source venv/bin/activate

# 6. Instala dependencias de desarrollo
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black flake8 pylint isort mypy

# 7. Inicia servicios con Docker
docker-compose up -d

# 8. Ejecuta migraciones
alembic upgrade head
```

---

## Cómo Reportar Problemas

### Antes de Reportar un Problema

- Verifica que el problema no ha sido reportado
- Verifica que usas la última versión
- Revisa la documentación

### Cómo Enviar un Buen Reporte de Problema

Use el template de issue en GitHub:

```markdown
**Descripción del problema**
Breve descripción del problema

**Pasos para reproducir**
1. ...
2. ...

**Comportamiento esperado**
¿Qué debería haber sucedido?

**Comportamiento actual**
¿Qué sucedió realmente?

**Entorno**
- OS: [Linux/macOS/Windows]
- Versión Python: [3.12]
- Versión Docker: [X.XX]

**Logs relevantes**
```python
# Pegue los logs aquí
```

---

## Cómo Sugerir Mejoras

### Antes de Sugerir una Mejora

- Verifica que la mejora no ha sido sugerida
- Revisa los requisitos del sistema

### Cómo Enviar una Buena Sugerencia de Mejora

Use el template:

```markdown
**Descripción de la mejora**
Descripción clara de lo que quieres que cambie

**Solución propuesta**
Cómo crees que debería implementarse

**Alternativas consideradas**
Otras soluciones que consideraste

**Contexto adicional**
Cualquier información adicional
```

---

## Proceso de Pull Request

### 1. Crear Rama de Feature

```bash
# Actualiza develop
git checkout develop
git pull upstream develop

# Crea rama de feature
git checkout -b feature/description-breve
# O para bugfix
git checkout -b fix/description-breve
```

### 2. Realizar Cambios

```bash
# Edita archivos
# Prueba localmente
make test
make lint

# Commit regularmente
git add .
git commit -m "Descripción clara del cambio"
```

### 3. Mantener Rama Actualizada

```bash
# Trae cambios del upstream
git fetch upstream
git rebase upstream/develop

# En caso de conflictos, resuelve y:
git rebase --continue
```

### 4. Enviar Pull Request

```bash
# Push tu rama
git push origin feature/description-breve

# En GitHub, crea PR desde tu fork
# Use el template de PR
```

### Template de Pull Request

```markdown
## Descripción
Breve descripción de los cambios

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva feature
- [ ] Mejora
- [ ] Refactoring

## Cambios Realizados
- Cambio 1
- Cambio 2

## Testing
- [ ] Tests unitarios agregados/actualizados
- [ ] Tests de integración agregados
- [ ] Código testeado manualmente

## Checklist
- [ ] El código sigue los estándares del proyecto
- [ ] He actualizado la documentación
- [ ] Los tests pasan
- [ ] Sin nuevas warnings

## Screenshots (si aplica)

## Issues Relacionados
Cierra #XXX
```

---

## Estándares de Código

### Python Style Guide

Seguimos [PEP 8](https://www.python.org/dev/peps/pep-0008/) con algunas personalizaciones:

```python
# ✅ Bueno
def crear_usuario(nombre: str, email: str) -> Usuario:
    """
    Crea un nuevo usuario.
    
    Args:
        nombre: Nombre del usuario
        email: Email del usuario
    
    Returns:
        Usuario creado
    
    Raises:
        ValueError: Si el email es inválido
    """
    if not email:
        raise ValueError("Email requerido")
    
    return Usuario(nombre=nombre, email=email)

# ❌ Malo
def crear_usuario(nombre, email):
    if not email:
        raise ValueError
    return Usuario(nombre, email)
```

### Type Hints

```python
# ✅ Usar type hints
from typing import Optional, List

def procesar_items(items: List[str]) -> Optional[str]:
    if not items:
        return None
    return items[0]

# ❌ Sin type hints
def procesar_items(items):
    if not items:
        return None
    return items[0]
```

### Docstrings

```python
# ✅ Google style docstrings
def validar_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
    
    Returns:
        True si es válido, False en otro caso
    
    Raises:
        TypeError: Si email no es string
    """
    if not isinstance(email, str):
        raise TypeError("Email debe ser string")
    return "@" in email
```

### Herramientas de Formato

```bash
# Format con Black
black app

# Organizar imports
isort app

# Verificar todo
make validate
```

---

## Proceso de Commit

### Mensaje de Commit

Sigue el formato:

```
<tipo>(<alcance>): <asunto>

<cuerpo>

<footer>
```

**Tipos válidos:**
- `feat`: Nueva feature
- `fix`: Bug fix
- `docs`: Cambios en documentación
- `style`: Cambios de formato
- `refactor`: Refactoring de código
- `perf`: Mejoras de performance
- `test`: Agregar/actualizar tests
- `chore`: Cambios en build, dependencias, etc.

**Ejemplos:**

```
feat(qr): agregar generación de QR con código de seguridad

Implementa la generación de códigos QR para acceso de residentes.
Incluye validación de duración y generación segura de tokens.

Closes #123
```

```
fix(auth): corregir validación de token Firebase

Se corrigió el bug donde tokens inválidos no eran rechazados.
Ahora se valida correctamente la firma del token.

Fixes #456
```

```
docs: actualizar guía de deployment

Se actualizó la sección de SSL/TLS con ejemplos.
```

---

## Revisión de Código

### Lo que Revisamos

1. **Funcionalidad**: ¿Funciona correctamente?
2. **Tests**: ¿Está bien testeado?
3. **Documentación**: ¿Está bien documentado?
4. **Performance**: ¿Hay impacto en performance?
5. **Seguridad**: ¿Hay vulnerabilidades?
6. **Estilo**: ¿Sigue los estándares?

### Cómo Responder a Reviews

```bash
# Si hay cambios solicitados:
# 1. Haz los cambios
git add .
git commit -m "Respuesta a review: ..."

# 2. Push (sin force push)
git push origin feature/description

# 3. Marca conversaciones como resueltas en GitHub
```

---

## Preguntas?

- **Documentación**: Ver [README.md](README.md)
- **Arquitectura**: Ver [ARQUITECTURA.md](ARQUITECTURA.md)
- **Deployment**: Ver [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: Abrir un issue en GitHub
- **Discussions**: Usar GitHub Discussions

---

## Reconocimiento

Al contribuir, aceptas que tus cambios serán licensiados bajo la misma licencia que el proyecto.

¡Gracias por contribuir! 🎉
