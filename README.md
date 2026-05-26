# maas-hackathon-260526
Repositorio oficial para recopilar las soluciones y retos de los participantes del Hackatón Huawei Colombia MaaS *Nivel avanzado e intermedio* — 26 de Mayo, 2026.

# 🚀 Guía de Entrega de Retos

Para mantener el repositorio organizado y facilitar la evaluación de los proyectos, todos los participantes deben seguir los siguientes pasos para subir sus soluciones.

---

# ⏰ Fecha límite de entrega

> ⚠️ **IMPORTANTE:**  
> Las soluciones podrán enviarse únicamente hasta las **11:20 AM del día 26 de mayo de 2026**.  
> Después de esa hora, **no se permitirán más submits ni pushes al repositorio**.

Se recomienda realizar la entrega con anticipación para evitar inconvenientes de última hora.

---

## 1. Clonar el repositorio

Si aún no lo has hecho, clona este repositorio en tu máquina local:

```bash
git clone https://github.com/hwcc2025-rgb/maas-hackathon-260526.git
cd maas-hackathon-260526
```

---

## 2. Crear una rama propia

Antes de realizar cualquier cambio, crea una rama independiente utilizando tu primer nombre y primer apellido en minúsculas, separados por un guion y sin caracteres especiales (sin tildes ni `ñ`).

### Ejemplo

```text
Juan Rodríguez → juan-rodriguez
```

### Crear la rama

```bash
git checkout -b tu-nombre-apellido
```

---

## 3. Estructura del proyecto

Dentro de tu rama, debes crear una carpeta en la raíz del repositorio con el mismo nombre de tu rama.

La estructura interna debe verse de la siguiente manera:

```text
📂 tu-nombre-apellido/
├── 📄 README.md              # Instrucciones claras de cómo ejecutar tu proyecto
├── 📄 requerimientos.txt     # Dependencias y librerías del proyecto
├── 📄 prompt_usado.txt       # Prompts utilizados en Huawei MaaS
├── 📄 reporte_becas.txt      # Reporte con las 3 becas más afines por estudiante
└── 📂 codigo/                # Carpeta o archivos con el código fuente del desarrollo
```

### Detalle de los archivos requeridos

| Archivo              | Descripción                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------- |
| `README.md`          | Explica claramente cómo instalar y ejecutar tu proyecto.                                          |
| `requerimientos.txt` | Lista de dependencias necesarias para correr el proyecto.                                         |
| `prompt_usado.txt`   | Incluye los prompts utilizados en Huawei MaaS.                                                    |
| `reporte_becas.txt`  | Reporte con las 3 becas más afines por estudiante. Puede entregarse también en `.docx` o `.pptx`. |
| `codigo/`            | Contiene el código fuente completo del proyecto.                                                  |

---

## 4. Subir los cambios a GitHub

Una vez tengas lista tu estructura y archivos, guarda los cambios, realiza el commit y sube únicamente tu rama al repositorio remoto.

```bash
git add tu-nombre-apellido/
git commit -m "feat: entrega de reto de Tu Nombre"
git push origin tu-nombre-apellido
```

---

# ⚠️ Notas importantes

## Seguridad

Está estrictamente prohibido subir:

- Archivos `.env`
- Credenciales
- Tokens
- Claves privadas
- Datos sensibles

Asegúrate de agregar estos archivos al `.gitignore`.

---

## Formato del reporte

El reporte de las 3 becas más afines para cada estudiante puede entregarse en cualquiera de estos formatos:

- `.txt`
- `.docx`
- `.pptx`

---

# 💡 Recomendación: agregar un `.gitignore`

Se recomienda crear un archivo `.gitignore` desde el inicio para evitar subir archivos innecesarios o información sensible.

## Ejemplo básico de `.gitignore`

```gitignore
# Variables de entorno
.env
*.env

# Entornos virtuales
.venv/
venv/

# Caché de Python
__pycache__/

# Archivos del sistema
.DS_Store
```

---

# ✅ Resumen rápido del flujo de trabajo

```bash
# 1. Clonar repositorio
git clone https://github.com/hwcc2025-rgb/maas-hackathon-260526.git

# 2. Entrar al proyecto
cd maas-hackathon-260526

# 3. Crear rama personal
git checkout -b tu-nombre-apellido

# 4. Crear estructura del proyecto
# (Agregar carpeta y archivos requeridos)

# 5. Guardar cambios
git add tu-nombre-apellido/

# 6. Crear commit
git commit -m "feat: entrega de reto de Tu Nombre"

# 7. Subir rama
git push origin tu-nombre-apellido
```

---
