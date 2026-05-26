import os
from dotenv import load_dotenv

load_dotenv()

MAAS_BASE_URL = os.getenv("MAAS_BASE_URL", "https://api-ap-southeast-1.modelarts-maas.com/v2")
MAAS_API_KEY = os.getenv("MAAS_API_KEY", "")
MAAS_MODEL = os.getenv("MAAS_MODEL", "deepseek-v3.2")
FECHA_EVALUACION = os.getenv("FECHA_EVALUACION", "")
MAAS_TIMEOUT = int(os.getenv("MAAS_TIMEOUT", "15"))

BECAS_REQUIRED_COLS = [
    "id_beca", "nombre_beca", "pais", "monto", "carreras_aceptadas",
    "gpa_minimo", "idioma_requerido", "fecha_cierre", "requiere_carta", "situacion_ec"
]

ESTUDIANTES_REQUIRED_COLS = [
    "id_estudiante", "nombre", "carrera", "gpa", "idiomas",
    "pais_interes", "situacion_economica", "email"
]

CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

EC_ORDER = {"baja": 1, "media": 2, "alta": 3}

SCORING = {
    "carrera_exacta": 60,
    "carrera_afin": 40,
    "pais_interes": 20,
    "fecha_proxima_max": 20,
}
