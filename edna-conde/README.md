# Sistema de Recomendacion de Becas Personalizado

Sistema de recomendacion de becas que cruza datos de convocatorias de becas con perfiles de estudiantes, generando un reporte personalizado con las 3 becas mas afines por estudiante. Potenciado con **Deepseek v3.2** via **MaaS Huawei Cloud** para explicaciones personalizadas con IA.

## Estructura del Proyecto

```
edna-conde/
├── README.md              # Este archivo - Instrucciones para ejecutar el proyecto
├── requerimientos.txt     # Levantamiento de requerimientos y dependencias
├── prompt_usado.txt       # Prompts utilizados en Huawei MaaS (Deepseek v3.2)
├── reporte_becas.txt      # Reporte generado con las 3 becas mas afines por estudiante
└── codigo/                # Codigo fuente del desarrollo
    ├── recomendador_becas.py   # Script principal del sistema de recomendacion
    ├── maas_client.py          # Cliente de integracion con MaaS (Deepseek v3.2)
    ├── becas.csv               # Datos de convocatorias de becas (15 becas)
    └── estudiantes.csv         # Datos de estudiantes (10 estudiantes)
```

## Requisitos Previos

- **Python 3.8+** instalado en el sistema
- **Conexion a internet** (para la integracion con Deepseek v3.2 via MaaS)
- Libreria `requests` de Python (viene preinstalada en la mayoria de distribuciones)

## Instalacion de Dependencias

```bash
pip install requests
```

## Como Ejecutar

1. Abrir una terminal y navegar a la carpeta `codigo/`:

```bash
cd edna-conde/codigo
```

2. Ejecutar el script principal:

```bash
python recomendador_becas.py
```

3. El sistema generara el archivo `reporte_recomendaciones.txt` en la misma carpeta `codigo/`.

## Que Hace el Sistema

1. **Lee los datos** de `becas.csv` y `estudiantes.csv`
2. **Evalua cada beca** contra cada estudiante usando 5 criterios de coincidencia:
   - **Carrera** (exacta +30, afin +20, todas +15 pts)
   - **GPA** (cumple +25 pts, no cumple = no elegible)
   - **Idioma** (completo +20, parcial +10 pts)
   - **Pais de interes** (+15 pts si coincide)
   - **Situacion economica** (coincide +10, abierta +5 pts)
3. **Ordena** por puntuacion descendente, luego por fecha de cierre ascendente
4. **Selecciona las top 3** becas elegibles por estudiante
5. **Enriquece con IA** usando Deepseek v3.2 (explicaciones personalizadas + resumen)
6. **Genera el reporte** en formato `.txt`

## Integracion con Deepseek v3.2 (MaaS Huawei Cloud)

El sistema utiliza el modelo **Deepseek v3.2** via la API de MaaS de Huawei Cloud para:

- Generar **explicaciones personalizadas** de por que cada beca es recomendada
- Generar un **resumen del perfil** del estudiante y sus oportunidades

**Configuracion MaaS:**
- API URL: `https://api-ap-southeast-1.modelarts-maas.com/openai/v1`
- Modelo: `deepseek-v3.2`
- Formato: OpenAI-compatible chat completions

Si MaaS no esta disponible, el sistema funciona en **modo fallback** sin las explicaciones de IA.

## Configuracion Alternativa

Las credenciales de MaaS se pueden configurar via variables de entorno:

```bash
set MAAS_BASE_URL=https://api-ap-southeast-1.modelarts-maas.com/openai/v1
set MAAS_API_KEY=tu_api_key_aqui
set MAAS_MODEL=deepseek-v3.2
```

## Ejemplo de Salida

```
  ESTUDIANTE: Ana Lopez (ID: 1001)
  Carrera: Ingenieria Informatica  |  GPA: 3.7

  ** RESUMEN IA (Deepseek v3.2):
    Ana, tu perfil es competitivo para las mejores becas...

  +--- RECOMENDACION #1 ---
  | Beca: Beca Fulbright Maestria (ID: 101)
  | Pais: Estados Unidos  |  Monto: $35000
  | ** PUNTUACION TOTAL: 90/100
  | Desglose de puntuacion:
  |   - carrera: Afin (Ingenieria Informatica) -> +20
  |   - gpa: GPA 3.7 >= 3.5 -> +25
  |   - idioma: Completo -> +20
  |   - pais: Estados Unidos en intereses -> +15
  |   - situacion_ec: Coincide (A) -> +10
  | ** Explicacion IA (Deepseek v3.2):
  |   Ana, tu perfil encaja excepcionalmente con la Beca Fulbright...
```

## Autor

Desarrollado para la Hackathon MaaS Huawei Cloud.