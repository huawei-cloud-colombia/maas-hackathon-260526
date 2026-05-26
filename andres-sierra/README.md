# Solución Hackathon Huawei Colombia MaaS

## 📋 Descripción

Solución integrada con **OpenCode** y **Huawei Cloud MaaS ModelArts** para el Hackatón Huawei Colombia MaaS - 26 de mayo de 2026.

### Características
- Integración con API de Huawei MaaS ModelArts
- Cliente Python para modelos GLM-5
- Soporte para generación y análisis de código
- Configuración segura con variables de entorno

## 📦 Requisitos previos

### Obligatorio
- **Python 3.8+**
- **Node.js 18+** (para OpenCode)
- **pip** (gestor de paquetes Python)
- Cuenta de Huawei Cloud con acceso a MaaS

### Opcional
- Visual Studio Code (para usar extensión OpenCode)

## ⚙️ Instalación y configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/huawei-cloud-colombia/maas-hackathon-260526.git
cd maas-hackathon-260526/andres-sierra
```

### 2. Crear entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar dependencias Python
```bash
pip install -r requerimientos.txt
```

### 4. Instalar OpenCode (global)
```bash
npm install -g opencode-ai
```

### 5. Configurar Huawei MaaS API

#### Opción A: Variable de entorno (recomendado)
```bash
export HUAWEI_MAAS_API_KEY="tu-api-key-aqui"
```

En Windows (PowerShell):
```powershell
$env:HUAWEI_MAAS_API_KEY = "tu-api-key-aqui"
```

#### Opción B: Archivo de configuración OpenCode
1. Copia `opencode-config-template.json` a `~/.config/opencode/opencode.json`
2. Reemplaza `${HUAWEI_MAAS_API_KEY}` con tu clave API real
3. Asegúrate de que el archivo tenga permisos seguros:
```bash
chmod 600 ~/.config/opencode/opencode.json
```

### 6. Obtener API Key de Huawei Cloud

1. Accede a [Huawei Cloud Console](https://www.huaweicloud.com/)
2. Navega a **API Management** → **My Credentials**
3. Genera una nueva **API Key**
4. Descárgala y almacénala de forma segura
5. Usa la clave en tu configuración

## 🚀 Ejecución

### Ejecutar solución principal
```bash
python codigo/main.py
```

### Usar OpenCode directamente
```bash
opencode
# Dentro de OpenCode, usa /models para seleccionar GLM-5
```

### Usar cliente MaaS en Python
```python
from codigo.huawei_maas_client import HuaweiMaaSClient

client = HuaweiMaaSClient()

# Chat
response = client.chat_completion([
    {"role": "user", "content": "¿Qué es Huawei Cloud?"}
])
print(response)

# Generación de código
code = client.code_generation("Función para sumar dos números")
print(code)

# Análisis de código
analysis = client.analyze_code("def add(a, b): return a + b")
print(analysis)
```

## 📁 Estructura del proyecto

```
andres-sierra/
├── README.md                      # Este archivo
├── requerimientos.txt             # Dependencias Python
├── prompt_usado.txt               # Prompts utilizados en MaaS
├── reporte_becas.txt              # Reporte de becas
├── opencode-config-template.json  # Template de configuración OpenCode
├── .gitignore                     # Archivos a ignorar
└── codigo/
    ├── main.py                    # Punto de entrada principal
    └── huawei_maas_client.py      # Cliente para MaaS API
```

## 🔐 Seguridad

- **Nunca** subir `API_KEY` al repositorio
- Usar `.gitignore` para archivos sensibles
- Almacenar credenciales en variables de entorno
- Usar `opencode.json` con permisos `600`

## 📚 Referencias

- [Huawei Cloud MaaS Documentation](https://support.huaweicloud.com/intl/en-us/model-call-maas/maas-modelarts-0909.html)
- [OpenCode AI Documentation](https://opencode.ai/)
- [OpenAI Python Client](https://github.com/openai/openai-python)

## 🧪 Troubleshooting

### Error: "HUAWEI_MAAS_API_KEY no configurada"
```bash
export HUAWEI_MAAS_API_KEY="tu-clave-api"
```

### Error: "opencode not found"
```bash
npm install -g opencode-ai
which opencode  # Verifica instalación
```

### Error de conexión a API
- Verifica que la región sea **CN-Hong Kong**
- Comprueba que tu API key sea válida
- Asegúrate de tener acceso a MaaS en tu cuenta Huawei

## 👤 Autor

**Andres Sierra**  
Participante del Hackatón Huawei Colombia MaaS  
Fecha: 26 de mayo de 2026

---

*Para soporte, consulta la documentación oficial de Huawei Cloud MaaS*
