# Becas IA — Asistente de Recomendación con Huawei MaaS

**Universidad Nova Andes · Oficina de Relaciones Internacionales**

Sistema que filtra y prioriza becas según el perfil de cada estudiante, combinando
**filtros deterministas** en Python con **explicaciones generadas por LLM**
(Huawei MaaS · DeepSeek-V4-Flash).

Entregables:

1. **`reporte_becas.txt`** — formato oficial pedido por el hackatón, top 3 becas por
   estudiante con razones y recomendación del asesor IA.
2. **`reporte_becas.pdf`** — versión estilizada con logo vectorial Nova Andes,
   tarjetas, badges y diseño moderno.
3. **Chat asistente** (Flet/Flutter) — interfaz tipo WhatsApp con burbujas
   interactivas, listas, animaciones y un *harness* que ejecuta acciones
   (matching, LLM, generación de reportes, **upload** de nuevos CSVs y
   **descarga** de reportes) en respuesta a los mensajes del estudiante.
4. **`prompt_maestro.txt`** — prompt único de ingeniería inversa que, entregado
   a un agente codificador capaz (Claude Code, Cursor, Aider…), regenera todo
   el proyecto desde cero.

---

## Arquitectura

```
                ┌──────────────────────────────┐
                │  CSV becas + CSV estudiantes │
                └──────────────┬───────────────┘
                               ▼
              ┌───────────────────────────────────┐
              │ matcher.py — filtros deterministas │
              │ GPA · país · carrera · idioma ·    │
              │ fecha · situación EC               │
              └──────────────┬─────────────────────┘
                             ▼
              ┌───────────────────────────────────┐
              │ Top K candidatas por estudiante   │
              └──────────────┬─────────────────────┘
                             ▼
              ┌───────────────────────────────────┐
              │ llm.py — Huawei MaaS              │
              │ explicación · siguiente paso ·    │
              │ fit_score                         │
              └──────┬────────────┬───────────────┘
                     │            │
        ┌────────────▼───┐   ┌────▼──────────────┐
        │  main.py       │   │  app.py (Flet)    │
        │  TXT + PDF     │   │  Chat asistente   │
        └────────────────┘   └───────────────────┘
```

El LLM **no decide elegibilidad** — solo enriquece. Las reglas duras garantizan
predictibilidad; el LLM aporta el lenguaje natural y el "fit_score".

---

## Estructura de entrega

```
arias/
├── README.md
├── requerimientos.txt
├── prompt_usado.txt
├── prompt_maestro.txt          ← prompt de ingeniería inversa
├── reporte_becas.txt           ← entregable oficial
├── reporte_becas.pdf           ← versión estilizada
└── codigo/
    ├── becas.csv
    ├── estudiantes.csv
    ├── logo.svg                ← logo vectorial Universidad Nova Andes
    ├── matcher.py              ← filtros + scoring
    ├── llm.py                  ← cliente Huawei MaaS
    ├── pdf_report.py           ← generador PDF (reportlab)
    ├── main.py                 ← genera TXT + PDF
    └── app.py                  ← chat asistente (Flet)
```

---

## Instalación

```bash
cd arias
python3 -m venv .venv
source .venv/bin/activate                # Linux/Mac
# .venv\Scripts\activate                 # Windows
pip install -r requerimientos.txt
```

---

## Configuración (variables de entorno)

```bash
export MAAS_URL="https://api-ap-southeast-1.modelarts-maas.com/openai/v1"
export MAAS_API_KEY="<tu-api-key>"
export MAAS_MODEL="deepseek-v4-flash"     # opcional
```

> ⚠️ **No subir la API key al repo.** El `.gitignore` ya excluye `.env`.

---

## Cómo ejecutarlo

### 1. Generar los reportes (TXT + PDF)

```bash
cd codigo
python main.py
# → ../reporte_becas.txt
# → ../reporte_becas.pdf
```

Opciones:

```bash
python main.py --k 5            # top 5 en vez de 3
python main.py --solo-txt       # omitir PDF
python main.py --sin-llm        # solo filtros, sin MaaS
```

Las explicaciones del MaaS se cachean en `codigo/.llm_cache.json` para que
re-ejecuciones sean instantáneas.

### 2. Chat asistente (escritorio o navegador)

**Recomendado — modo web (un solo comando):**

```bash
python codigo/app.py
# Abre automáticamente http://localhost:8550 en tu navegador
```

`app.py` arranca en modo web por defecto (`ft.AppView.WEB_BROWSER`). Si el puerto
8550 ya estaba ocupado por una corrida anterior, libéralo:

```bash
pkill -f "codigo/app.py"
```

**Escritorio nativo (Windows/Mac/Linux con display server):**

```bash
APP_MODE=desktop python codigo/app.py
```

El chat:

- saluda al usuario y le ofrece **opciones tocables** (chips) tipo WhatsApp;
- muestra una **lista seleccionable** de estudiantes con avatares e iniciales;
- al elegir un estudiante, ejecuta el **harness** (`matcher.top_matches`) y
  muestra las 3 becas en tarjetas dentro de una burbuja;
- cada tarjeta tiene botones *Por qué encaja* (dispara LLM) y *Detalles*;
- un botón **Generar / regenerar reporte** dispara `main.py` desde el chat;
- transiciones de opacidad/offset, indicador de typing con tres puntos
  animados, gradientes y sombras tipo glassmorphism.

#### Descargar los reportes desde el chat

`app.py` se inicia con `assets_dir=arias/`, por lo que el servidor de Flet
expone `reporte_becas.pdf` y `reporte_becas.txt` como archivos estáticos
(`/reporte_becas.pdf`, `/reporte_becas.txt`) con su `Content-Type` correcto.

- Si los reportes ya existen, el saludo muestra el chip **"Descargar
  reportes"** arriba del todo.
- Tras *Generar / regenerar reporte*, la burbuja de éxito muestra
  **"Descargar PDF"** y **"Descargar TXT"**.
- Los botones llaman a `UrlLauncher().launch_url(url, web_only_window_name="_blank")`
  para abrir el archivo en una pestaña nueva (Chrome muestra el PDF inline
  con su propio botón de descarga; el TXT lo muestra inline).

#### Cargar tus propios CSVs desde el chat

El chip **"Cargar mis CSVs"** abre el selector de archivos del navegador
(`FilePicker`, registrado en `page.services`). Puedes seleccionar uno o
varios CSV al mismo tiempo:

1. El asistente lee los bytes (`with_data=True`) y detecta el tipo por
   las columnas de la cabecera:
   - `id_beca, nombre_beca, pais, monto, …` ⇒ **becas**
   - `id_estudiante, nombre, carrera, gpa, …` ⇒ **estudiantes**
2. Cada CSV reconocido sobrescribe `codigo/becas.csv` o
   `codigo/estudiantes.csv`, y el `Harness` recarga el motor (limpiando
   el cache LLM porque el dataset cambió).
3. Los archivos con cabeceras desconocidas se reportan en la misma
   burbuja con un `!`.
4. La burbuja de confirmación ofrece accesos rápidos para
   **Buscar becas con estos datos** y **Regenerar reporte**.

Esto permite trabajar con múltiples datasets en la misma sesión sin tocar
disco a mano.

---

## Reglas de filtrado

| Campo | Regla |
|---|---|
| GPA | `gpa_estudiante >= gpa_minimo` |
| País | `pais_beca` ∈ `pais_interes` (o `Europa` ↔ países europeos) |
| Carrera | `carreras_aceptadas` contiene la carrera o dice "Todas" |
| Idioma | estudiante cumple nivel CEFR (A1<…<C2) o JLPT (N5<…<N1) |
| Fecha | `fecha_cierre > hoy` (las cerradas se marcan, no se descartan) |
| Situación EC | si está definida, debe coincidir con la del estudiante |

Si menos de 3 becas pasan los filtros, completamos con "near misses"
marcados como tales.

---

## Tecnologías

- **Python 3.10+** — base
- **pandas** — carga y normalización de CSVs
- **requests** — cliente HTTP para Huawei MaaS (compatible OpenAI)
- **reportlab** — generación del PDF estilizado (vector nativo, sin deps C)
- **Flet** — UI multiplataforma sobre Flutter (Windows, macOS, Linux, web, iOS,
  Android) — un solo `app.py`

### Por qué Flet

- Una sola base de código corre en **escritorio, navegador y móvil**.
- Construido sobre **Flutter** → animaciones, blur, gradientes y tipografía
  pulida sin trucos CSS.
- Solo Python — sin npm, sin webpack, sin separación frontend/backend.

---

## Modelo Huawei MaaS

| Parámetro | Valor |
|---|---|
| Endpoint | `https://api-ap-southeast-1.modelarts-maas.com/openai/v1` |
| Modelo | `deepseek-v4-flash` |
| Temperature | `0.3` |
| max_tokens | `400` |
| Retry | 4 intentos con backoff exponencial (2, 4, 8, 16 s) en 429 |

Los prompts completos están en `prompt_usado.txt`.

---

## Limitaciones conocidas

- El MaaS aplica **rate limit** (HTTP 429). Implementamos retry con backoff
  exponencial; aun así, una corrida completa fría toma varios minutos. El
  `.llm_cache.json` evita repetir trabajo.
- El dataset de prueba tiene fechas de 2025 (vencidas a la fecha de hoy).
  Las marcamos como "Vencida" pero no las descartamos del top 3 — el reporte
  muestra igual cómo habría matcheado el estudiante (útil para análisis).
- Flet 0.85+ usa **colores ARGB** (`#AARRGGBB`) en vez del clásico CSS
  `#RRGGBBAA`. Si modificas paletas, recuerda poner el alpha al principio,
  no al final.
- En Flet 0.85+, `FilePicker` es un **service** (va en `page.services`,
  no en `page.overlay`) y `pick_files()` es **coroutine** — debe esperarse
  con `await` dentro de una tarea registrada vía `page.run_task(...)`.
- `page.launch_url()` está deprecado desde Flet 0.90. Usa
  `UrlLauncher().launch_url(url)` registrado como service.

---

## Créditos

Reto: **Sistema de recomendación de becas personalizado para universidades**
Hackatón: **Huawei Cloud Colombia · MaaS · 26 mayo 2026**
Universidad ficticia: **Nova Andes**
