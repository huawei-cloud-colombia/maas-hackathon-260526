# BecaMatch - Sistema de Recomendacion de Becas

Sistema personalizado de recomendacion de becas para universidades, desarrollado con **Python + Flask + Pandas**.

## Problema que resuelve

La Oficina de Relaciones Internacionales recibe cientos de convocatorias de becas cada semestre. Los estudiantes no encuentran becas relevantes y pierden oportunidades. **BecaMatch** filtra y prioriza becas segun el perfil academico de cada estudiante.

---

## Requisitos previos

- **Python 3.9+** instalado en el sistema
- **pip3** (gestor de paquetes de Python)

---

## Instalacion y ejecucion

### 1. Clonar/ir al directorio del proyecto

```bash
cd /ruta/al/proyecto/retoHuawei
  BecaMatch - Sistema de Recomendacion de Becas
 * Running on http://127.0.0.1:5000
  Iniciando servidor en http://localhost:5001
 * Running on http://127.0.0.1:5001
 * Running on http://127.0.0.1:5000
```

### 4. Abrir en el navegador

Abre tu navegador en: **http://localhost:5000**
```
  BecaMatch - Sistema de Recomendacion de Becas
  Iniciando servidor en http://localhost:5001
 * Running on http://127.0.0.1:5001
```

### 4. Abrir en el navegador

Abre tu navegador en: **http://localhost:5001**

### 2. Instalar dependencias

```bash
pip3 install flask pandas
```

O usando el archivo de requirements:

```bash
pip3 install -r requirements.txt
```

### 3. Ejecutar el servidor

```bash
python3 run.py
```

Veras la salida:

```
==================================================
  BecaMatch - Sistema de Recomendacion de Becas
 * Running on http://127.0.0.1:5000
  Iniciando servidor en http://localhost:5001
 * Running on http://127.0.0.1:5001
==================================================
 * Running on http://127.0.0.1:5000
```

### 4. Abrir en el navegador

Abre tu navegador en: **http://localhost:5000**

### 5. Detener el servidor

Presiona `CTRL + C` en la terminal donde esta corriendo.

---

## Estructura del proyecto

```
retoHuawei/
├── run.py                     # Punto de entrada principal
├── requirements.txt           # Dependencias (flask, pandas)
├── README.md                  # Esta documentacion
├── docs/
│   ├── becas.csv              # Base de datos de becas (15 becas)
│   └── estudiantes.csv        # Base de datos de estudiantes (10 estudiantes)
└── app/
    ├── __init__.py            # Inicializador del paquete
    ├── app.py                 # Aplicacion Flask: rutas web + API REST
    ├── data_loader.py         # Carga y parseo de archivos CSV
    ├── recommender.py         # Motor de scoring y ranking
    ├── templates/             # Plantillas HTML (Jinja2)
    │   ├── base.html          # Template base con navbar y footer
    │   ├── index.html         # Pagina principal: lista de estudiantes
    │   ├── recomendaciones.html # Recomendaciones por estudiante
    │   ├── becas.html         # Lista de todas las becas
    │   ├── beca.html          # Detalle de una beca especifica
    │   └── error.html         # Pagina de error
    └── static/
        └── css/
            └── style.css      # Estilos de la interfaz
```

---

## Motor de Recomendacion

El sistema calcula un **score de compatibilidad** (maximo 100 puntos) basado en 5 criterios ponderados:

| Criterio | Peso | Descripcion |
|----------|------|-------------|
| **Carrera** | 30 pts | Coincidencia exacta (1.0), parcial (0.85), afin (0.7), todas las carreras (0.4) |
| **GPA** | 20 pts | Cumple requisito (1.0) + bonus de hasta 0.2 por exceder el minimo |
| **Idioma** | 25 pts | Compara niveles CEFR (A1-C2) y JLPT (N5-N1), bonus por exceder |
| **Pais** | 15 pts | Match exacto con pais de interes (1.0), region (0.8), no coincide (0.0) |
| **Fecha de cierre** | 10 pts | Urgencia: <=30 dias (1.0), <=90 (0.8), <=180 (0.6), <=365 (0.4), >365 (0.2) |

### Filtros minimos

Solo se muestran becas donde el estudiante:
- Cumple con el **GPA minimo** requerido
- Cumple con **al menos un idioma** al nivel requerido

### Afinidad entre carreras

El sistema reconoce carreras afines, por ejemplo:
- Ingenieria Informatica ↔ Ingenieria, Ciencias de la Computacion, Matematicas
- Robotica ↔ Ingenieria, Ciencias de la Computacion
- Arquitectura ↔ Urbanismo, Ingenieria Civil
- Biologia ↔ Ciencias, Medicina

---

## Rutas de la aplicacion

### Interfaz Web

| Ruta | Descripcion |
|------|-------------|
| `/` | Pagina principal con lista de estudiantes |
| `/estudiante/<id>` | Recomendaciones de becas para un estudiante |
| `/becas` | Lista de todas las becas disponibles |
| `/beca/<id>` | Detalle de una beca especifica |

### API REST (JSON)

| Endpoint | Descripcion |
|----------|-------------|
| `GET /api/estudiantes` | Lista todos los estudiantes |
| `GET /api/becas` | Lista todas las becas |
| `GET /api/recomendar/<id_estudiante>` | Recomendaciones para un estudiante |
| `GET /api/recomendar/<id_estudiante>?top_n=5` | Top N recomendaciones |

#### Ejemplo de uso de la API:

```bash
# Obtener recomendaciones para el estudiante 1001 (Ana Lopez)
curl http://localhost:5000/api/recomendar/1001

# Obtener solo las top 3 recomendaciones
curl http://localhost:5000/api/recomendar/1001?top_n=3

# Listar todos los estudiantes
curl http://localhost:5000/api/estudiantes
```

---

## Datos de entrada

### Formato de `becas.csv`

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_beca | int | Identificador unico |
| nombre_beca | string | Nombre de la beca |
| pais | string | Pais de destino |
| monto | float | Monto en USD |
| carreras_aceptadas | string (comma-sep) | Carreras elegibles o "Todas las carreras" |
| gpa_minimo | float | GPA minimo requerido |
| idioma_requerido | string (comma-sep) | Idiomas y niveles requeridos |
| fecha_cierre | date (YYYY-MM-DD) | Fecha limite de aplicacion |
| requiere_carta | bool (Si/No) | Si requiere carta de recomendacion |
| situacion_ec | string | Situacion economica objetivo (A-D) |

### Formato de `estudiantes.csv`

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id_estudiante | int | Identificador unico |
| nombre | string | Nombre completo |
| carrera | string | Carrera que estudia |
| gpa | float | Promedio academico |
| idiomas | string (comma-sep) | Idiomas y niveles del estudiante |
| pais_interes | string (comma-sep) | Paises de interes |
| situacion_economica | string (A-D) | Nivel socioeconomico |
| email | string | Correo institucional |

---

## Ejemplo de resultado

Para **Ana Lopez** (Ingenieria Informatica, GPA 3.7, Ingles C1):

| # | Beca | Score | Carrera | GPA | Idioma | Pais | Fecha |
|---|------|-------|---------|-----|--------|------|-------|
| 1 | Beca Fulbright Maestria | 85.9 | Exacta | Si | Si | Si | 0.4 |
| 2 | Beca Eiffel | 64.42 | Afin | Si | Parcial | No | 0.6 |
| 3 | Beca OAS | 63.7 | Afin | Si | Si | Si | 0.4 |
| 4 | Beca MEXT Japon | 61.5 | Exacta | Si | Si | No | 0.8 |
| 5 | Beca DAAD | 59.85 | Afin | Si | Si | No | 0.6 |

---

## Tecnologias utilizadas

- **Python 3.9** - Lenguaje principal
- **Flask 3.1** - Framework web ligero
- **Pandas 2.3** - Procesamiento de datos CSV
- **Jinja2** - Motor de plantillas HTML
- **HTML/CSS/JS** - Interfaz de usuario responsiva

---

## Licencia

Proyecto academico - Universidad