# BecaMatch AI

Plataforma web inteligente para recomendación explicable de becas, desarrollada para el Hackatón Huawei Cloud MaaS 2026.

## Descripción

BecaMatch AI carga archivos `becas.csv` y `estudiantes.csv`, determina elegibilidad mediante un motor determinístico, y presenta las 3 becas más afines por estudiante con explicación verificable. Integra DeepSeek en Huawei Cloud MaaS para validar afinidades de carrera ambiguas y generar explicaciones enriquecidas.

## Requisitos

- Python 3.8+
- pip

## Instalación

```bash
cd andres-sierra/codigo
pip install -r requirements.txt
```

## Configuración MaaS/DeepSeek

1. Copiar `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
2. Editar `.env` y agregar tu API key de Huawei Cloud MaaS:
   ```
   MAAS_API_KEY=tu-api-key-aqui
   ```
3. Sin API key, la aplicación funciona en modo fallback (solo coincidencias exactas de carrera).

## Ejecución

```bash
cd andres-sierra/codigo
python app.py
```

Abrir http://localhost:5000 en el navegador.

## Uso

1. Cargar `becas.csv` y `estudiantes.csv` (se incluyen ejemplos en `data/`).
2. Opcionalmente configurar fecha de evaluación para filtrar becas cerradas.
3. Presionar "Generar recomendaciones".
4. Ver resultados con top 3 por estudiante, badges de criterios, puntajes.
5. Descargar reporte en .txt o .csv.

## Pruebas

```bash
cd andres-sierra/codigo
python -m pytest tests/ -v
```

## Estructura

```
andres-sierra/
├── README.md
├── requerimientos.txt
├── prompt_usado.txt
├── reporte_becas.txt
├── .gitignore
└── codigo/
    ├── app.py                    # Aplicación Flask
    ├── config.py                 # Configuración
    ├── requirements.txt
    ├── .env.example
    ├── services/
    │   ├── data_loader.py        # Carga y validación CSV
    │   ├── eligibility.py        # Filtros de elegibilidad
    │   ├── ranking.py            # Scoring y ranking
    │   └── maas_client.py        # Cliente MaaS/DeepSeek
    ├── templates/
    │   ├── base.html
    │   ├── index.html
    │   └── results.html
    ├── static/
    │   └── styles.css
    ├── data/
    │   ├── becas.csv
    │   └── estudiantes.csv
    ├── tests/
    │   ├── test_data_loader.py
    │   ├── test_eligibility.py
    │   ├── test_ranking.py
    │   └── test_maas_client.py
    └── outputs/
        └── reporte_recomendaciones.txt
```

## Motor de elegibilidad

Filtros obligatorios antes de puntuar:
- GPA del estudiante >= gpa_minimo de la beca
- Idioma del estudiante con nivel CEFR >= requerido (A1 < A2 < B1 < B2 < C1 < C2)
- Beca no cerrada respecto a FECHA_EVALUACION
- Situación económica compatible (baja < media < alta)

## Scoring

| Criterio | Puntos |
|----------|--------|
| Carrera exacta | 60 |
| Carrera afín (validada por IA) | 40 |
| País de interés coincide | 20 |
| Fecha de cierre próxima | Hasta 20 |

Desempates: mayor puntaje > fecha más próxima > mayor monto > id_beca ascendente.

## Integración MaaS/DeepSeek

- Cliente compatible con OpenAI SDK apuntando a Huawei Cloud MaaS V2
- Model: deepseek-v3.2 (configurable)
- temperature=0 para respuestas deterministas
- JSON estructurado: es_afin, nivel_afinidad, razon_breve, confianza
- Fallback automático si MaaS no disponible

## Guion de demo (2 minutos)

1. **Problema**: Estudiantes pierden becas relevantes; la oficina procesa convocatorias manualmente.
2. **Carga**: Subir becas.csv y estudiantes.csv con fecha de evaluación 6/1/2025.
3. **Resultados**: Top 3 por estudiante con puntaje y badges verificables.
4. **Carrera afín**: Mostrar caso donde DeepSeek valida afinidad (si MaaS configurado) o indicar modo fallback.
5. **Exportación**: Descargar reporte .txt.
6. **Cierre**: Reglas auditables, IA donde aporta valor, lista para escalar.

## Seguridad

- API keys solo en variables de entorno (.env en .gitignore)
- No se envían datos personales al modelo
- .env.example sin secretos reales

## Autor

Andres Sierra - Hackatón Huawei Cloud MaaS 2026
