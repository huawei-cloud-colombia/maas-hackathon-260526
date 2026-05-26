"""
=============================================================================
 SISTEMA DE RECOMENDACIÓN DE BECAS — Hackaton Huawei
 Modelo IA: DeepSeek v3.2 vía Huawei MaaS API
=============================================================================
 Autor : Generado para Hackaton Huawei
 Fecha : 2026-05-26
 Descripción:
     Lee perfiles de estudiantes y convocatorias de becas desde CSV,
     aplica pre-filtrado por reglas duras (fecha y GPA), y luego invoca
     la API de DeepSeek v3.2 para obtener las 3 mejores becas por estudiante
     basándose en afinidad semántica, idioma, país y urgencia de fecha.
=============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CARGA DE VARIABLES DE ENTORNO
# ---------------------------------------------------------------------------
load_dotenv()

API_URL = os.getenv(
    "DEEPSEEK_API_URL",
    "https://api-ap-southeast-1.modelarts-maas.com/openai/v1/chat/completions",
)
API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
API_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  # DeepSeek v3.2 vía Huawei MaaS

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------
MAX_BECAS_RECOMENDADAS = 3
BASE_DIR = Path(__file__).resolve().parent
ESTUDIANTES_CSV = BASE_DIR / "estudiantes.csv"
BECAS_CSV = BASE_DIR / "becas.csv"
REPORTE_TXT = BASE_DIR / "reporte_becas.txt"


# ===========================================================================
# 1. CARGA DE DATOS
# ===========================================================================
def cargar_csv(ruta: Path, nombre: str) -> pd.DataFrame:
    """Carga un archivo CSV y devuelve un DataFrame.

    Args:
        ruta: Ruta al archivo CSV.
        nombre: Nombre descriptivo para mensajes de log.

    Returns:
        DataFrame con los datos del CSV.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    if not ruta.exists():
        logger.error("No se encontró el archivo %s en: %s", nombre, ruta)
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    df = pd.read_csv(ruta)
    logger.info("Cargados %d registros de '%s'.", len(df), nombre)
    return df


# ===========================================================================
# 2. PRE-FILTRO: BECAS VIGENTES (fecha_cierre no vencida)
# ===========================================================================
def filtrar_becas_vigentes(df_becas: pd.DataFrame) -> pd.DataFrame:
    """Elimina las becas cuya fecha de cierre ya pasó.

    Args:
        df_becas: DataFrame de becas con columna 'fecha_cierre'.

    Returns:
        DataFrame filtrado solo con becas vigentes.
    """
    hoy = datetime.now().date()
    # Convertir fecha_cierre a tipo date para comparar
    fechas = pd.to_datetime(df_becas["fecha_cierre"], errors="coerce").dt.date
    vigentes = df_becas[fechas >= hoy].copy()
    descartadas = len(df_becas) - len(vigentes)
    logger.info("Pre-filtro fecha: %d becas vigentes, %d descartadas.", len(vigentes), descartadas)
    return vigentes


# ===========================================================================
# 3. PRE-FILTRO: GPA DEL ESTUDIANTE >= GPA MÍNIMO DE LA BECA
# ===========================================================================
def filtrar_becas_por_gpa(
    df_becas: pd.DataFrame, gpa_estudiante: float
) -> pd.DataFrame:
    """Filtra las becas donde el GPA del estudiante no alcanza el mínimo.

    Args:
        df_becas: DataFrame de becas con columna 'gpa_minimo'.
        gpa_estudiante: GPA del estudiante.

    Returns:
        DataFrame con becas cuyo gpa_minimo <= gpa_estudiante.
    """
    aptas = df_becas[df_becas["gpa_minimo"] <= gpa_estudiante].copy()
    logger.info(
        "Pre-filtro GPA %.2f: %d becas aptas de %d.",
        gpa_estudiante,
        len(aptas),
        len(df_becas),
    )
    return aptas


# ===========================================================================
# 4. INTEGRADOR IA — Llamada a DeepSeek v3.2
# ===========================================================================
def construir_prompt_ia(
    estudiante: pd.Series, df_becas_candidatas: pd.DataFrame
) -> str:
    """Construye el prompt que se enviará a la API de DeepSeek.

    Args:
        estudiante: Fila del DataFrame del estudiante.
        df_becas_candidatas: Becas que pasaron el pre-filtro.

    Returns:
        String con el prompt completo para la IA.
    """
    perfil = (
        f"Perfil del estudiante:\n"
        f"  - Nombre: {estudiante['nombre']}\n"
        f"  - Carrera: {estudiante['carrera']}\n"
        f"  - GPA: {estudiante['gpa']}\n"
        f"  - Idiomas: {estudiante['idiomas']}\n"
        f"  - País de interés: {estudiante['pais_interes']}\n"
    )

    becas_texto = "Becas candidatas:\n"
    for _, beca in df_becas_candidatas.iterrows():
        becas_texto += (
            f"  [{beca['id_beca']}] {beca['nombre_beca']} — "
            f"País: {beca['pais']}, "
            f"Carreras: {beca['carreras_aceptadas']}, "
            f"GPA mín: {beca['gpa_minimo']}, "
            f"Idioma req: {beca['idioma_requerido']}, "
            f"Fecha cierre: {beca['fecha_cierre']}\n"
        )

    instrucciones = (
        f"\nINSTRUCCIONES:\n"
        f"1. Evalúa cada beca contra el perfil del estudiante.\n"
        f"2. Criterios de evaluación (en orden de importancia):\n"
        f"   a) AFINIDAD DE CARRERA: ¿La carrera del estudiante está dentro de las carreras aceptadas?\n"
        f"   b) IDIOMA: ¿El estudiante cumple con el idioma requerido? (nivel >= al requerido)\n"
        f"   c) PAÍS: Prioridad extra si el país de interés del estudiante coincide con el país de la beca.\n"
        f"   d) URGENCIA: Prioridad extra si la fecha de cierre está próxima.\n"
        f"3. Selecciona MÁXIMO {MAX_BECAS_RECOMENDADAS} becas, ordenadas de mejor a peor match.\n"
        f"4. Responde SOLO en formato JSON con esta estructura exacta:\n"
        f'   {{"recomendaciones": [{{"id_beca": <int>, "razon": "<texto>"}}]}}\n'
        f"5. Si ninguna beca es compatible, responde: "
        f'{{"recomendaciones": [], "motivo": "No se encontraron becas compatibles"}}'
    )

    return perfil + becas_texto + instrucciones


def llamar_api_deepseek(prompt: str) -> dict:
    """Envía el prompt a la API de DeepSeek v3.2 y devuelve la respuesta.

    Args:
        prompt: Texto del prompt construido.

    Returns:
        Diccionario con las recomendaciones parseadas del JSON de la IA.
    """
    if not API_KEY:
        logger.warning("DEEPSEEK_API_KEY no configurada. Usando modo simulación.")
        return _simular_respuesta_ia()

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": API_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un asistente experto en recomendación de becas universitarias. "
                    "Siempre respondes en JSON válido según las instrucciones del usuario."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        logger.info("Enviando solicitud a DeepSeek API (%s)...", API_MODEL)
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        contenido = response.json()["choices"][0]["message"]["content"]
        logger.info("Respuesta recibida de DeepSeek API.")

        # Intentar parsear el JSON de la respuesta
        return _parsear_respuesta_ia(contenido)

    except requests.exceptions.RequestException as e:
        logger.error("Error al llamar a la API de DeepSeek: %s", e)
        return {"recomendaciones": [], "motivo": f"Error de API: {e}"}
    except (KeyError, IndexError) as e:
        logger.error("Respuesta inesperada de la API: %s", e)
        return {"recomendaciones": [], "motivo": f"Respuesta inesperada: {e}"}


def _parsear_respuesta_ia(contenido: str) -> dict:
    """Parsea el contenido JSON de la respuesta de la IA.

    Args:
        contenido: Texto de respuesta de la IA.

    Returns:
        Diccionario con las recomendaciones.
    """
    # Extraer JSON si viene envuelto en markdown code blocks
    contenido_limpio = contenido.strip()
    if contenido_limpio.startswith("```"):
        lineas = contenido_limpio.split("\n")
        lineas_json = [l for l in lineas if not l.strip().startswith("```")]
        contenido_limpio = "\n".join(lineas_json)

    try:
        return json.loads(contenido_limpio)
    except json.JSONDecodeError:
        logger.warning("La IA no devolvió JSON válido. Contenido: %s", contenido[:200])
        return {"recomendaciones": [], "motivo": "Respuesta IA no es JSON válido"}


def _simular_respuesta_ia() -> dict:
    """Simula una respuesta de la IA cuando no hay API key configurada.

    Returns:
        Diccionario simulado indicando modo demo.
    """
    logger.info("Modo simulación activado — se requiere API key para IA real.")
    return {
        "recomendaciones": [],
        "motivo": "Modo simulación: configure DEEPSEEK_API_KEY para activar IA",
    }


# ===========================================================================
# 5. ORQUESTADOR PRINCIPAL POR ESTUDIANTE
# ===========================================================================
def recomendar_becas_estudiante(
    estudiante: pd.Series, df_becas_vigentes: pd.DataFrame
) -> dict:
    """Pipeline completo de recomendación para un estudiante.

    Args:
        estudiante: Fila del DataFrame del estudiante.
        df_becas_vigentes: Becas que pasaron el filtro de fecha.

    Returns:
        Diccionario con el resultado de la recomendación.
    """
    resultado = {
        "id_estudiante": int(estudiante["id_estudiante"]),
        "nombre": estudiante["nombre"],
        "carrera": estudiante["carrera"],
        "gpa": float(estudiante["gpa"]),
    }

    # Pre-filtro GPA
    becas_aptas = filtrar_becas_por_gpa(df_becas_vigentes, estudiante["gpa"])

    # Caso especial: sin becas disponibles
    if becas_aptas.empty:
        logger.warning(
            "Estudiante %s (GPA %.2f) no tiene becas disponibles tras pre-filtro.",
            estudiante["nombre"],
            estudiante["gpa"],
        )
        resultado["recomendaciones"] = []
        resultado["motivo"] = (
            "No se encontraron becas disponibles después del pre-filtro "
            "(ninguna beca vigente cumple con el GPA mínimo requerido)."
        )
        return resultado

    # Llamada a la IA
    prompt = construir_prompt_ia(estudiante, becas_aptas)
    respuesta_ia = llamar_api_deepseek(prompt)

    resultado["recomendaciones"] = respuesta_ia.get("recomendaciones", [])
    if "motivo" in respuesta_ia:
        resultado["motivo"] = respuesta_ia["motivo"]

    return resultado


# ===========================================================================
# 6. GENERACIÓN DEL REPORTE
# ===========================================================================
def generar_reporte(resultados: list[dict], df_becas: pd.DataFrame) -> None:
    """Genera el archivo 'reporte_becas.txt' con los resultados.

    Args:
        resultados: Lista de diccionarios con recomendaciones por estudiante.
        df_becas: DataFrame completo de becas (para buscar datos adicionales).
    """
    lineas: list[str] = []
    separador = "=" * 72

    lineas.append(separador)
    lineas.append("  REPORTE DE RECOMENDACIÓN DE BECAS")
    lineas.append(f"  Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lineas.append(f"  Modelo IA: {API_MODEL}")
    lineas.append(separador)
    lineas.append("")

    for res in resultados:
        lineas.append("-" * 72)
        lineas.append(f"  Estudiante: {res['nombre']} (ID: {res['id_estudiante']})")
        lineas.append(f"  Carrera: {res['carrera']}  |  GPA: {res['gpa']:.2f}")
        lineas.append("-" * 72)

        recomendaciones = res.get("recomendaciones", [])

        if not recomendaciones:
            motivo = res.get("motivo", "Sin becas compatibles.")
            lineas.append(f"  ⚠ SIN RECOMENDACIONES: {motivo}")
        else:
            for i, rec in enumerate(recomendaciones, 1):
                id_beca = rec.get("id_beca")
                razon = rec.get("razon", "Sin razón especificada")

                # Buscar datos de la beca en el DataFrame
                fila_beca = df_becas[df_becas["id_beca"] == id_beca]
                if not fila_beca.empty:
                    beca = fila_beca.iloc[0]
                    lineas.append(f"  {i}. {beca['nombre_beca']} (ID: {id_beca})")
                    lineas.append(f"     País: {beca['pais']}  |  Monto: {beca.get('monto', 'N/A')}")
                    lineas.append(f"     Carreras: {beca['carreras_aceptadas']}")
                    lineas.append(f"     Fecha cierre: {beca['fecha_cierre']}")
                else:
                    lineas.append(f"  {i}. Beca ID {id_beca}")

                lineas.append(f"     💡 Razón: {razon}")
                lineas.append("")

        lineas.append("")

    # Resumen estadístico
    lineas.append(separador)
    lineas.append("  RESUMEN ESTADÍSTICO")
    lineas.append(separador)
    total_estudiantes = len(resultados)
    con_recomendacion = sum(1 for r in resultados if r.get("recomendaciones"))
    sin_recomendacion = total_estudiantes - con_recomendacion
    lineas.append(f"  Total estudiantes evaluados: {total_estudiantes}")
    lineas.append(f"  Con recomendación:           {con_recomendacion}")
    lineas.append(f"  Sin recomendación:           {sin_recomendacion}")
    lineas.append("")

    # Escribir archivo
    with open(REPORTE_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    logger.info("Reporte generado en: %s", REPORTE_TXT)


# ===========================================================================
# 7. FUNCIÓN PRINCIPAL (ENTRY POINT)
# ===========================================================================
def main() -> None:
    """Función principal que orquesta todo el pipeline de recomendación."""
    logger.info("=" * 50)
    logger.info("INICIO — Sistema de Recomendación de Becas")
    logger.info("=" * 50)

    # --- Paso 1: Carga de datos ---
    try:
        df_estudiantes = cargar_csv(ESTUDIANTES_CSV, "estudiantes")
        df_becas = cargar_csv(BECAS_CSV, "becas")
    except FileNotFoundError as e:
        logger.critical("No se pudo iniciar: %s", e)
        sys.exit(1)

    # --- Paso 2: Pre-filtro de becas vigentes ---
    df_becas_vigentes = filtrar_becas_vigentes(df_becas)

    if df_becas_vigentes.empty:
        logger.warning("No hay becas vigentes. No se pueden generar recomendaciones.")
        sys.exit(0)

    # --- Paso 3-5: Recomendación por estudiante ---
    resultados: list[dict] = []
    for _, estudiante in df_estudiantes.iterrows():
        logger.info("--- Procesando estudiante: %s ---", estudiante["nombre"])
        resultado = recomendar_becas_estudiante(estudiante, df_becas_vigentes)
        resultados.append(resultado)

    # --- Paso 6: Generación del reporte ---
    generar_reporte(resultados, df_becas)

    logger.info("=" * 50)
    logger.info("FIN — Proceso completado exitosamente")
    logger.info("=" * 50)


# ---------------------------------------------------------------------------
# EJECUCIÓN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
