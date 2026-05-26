#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Recomendación de Becas Personalizado
Cruza datos de convocatorias de becas con perfiles de estudiantes
y genera un reporte con las 3 becas más afines por estudiante.
Integrado con Deepseek v3.2 via MaaS Huawei Cloud.
"""

import csv
import os
from datetime import datetime
from collections import defaultdict
from maas_client import MaaSClient, enriquecer_reporte_con_ia, MaaSError

# =============================================================================
# CONFIGURACIÓN DE AFINIDAD DE CARRERAS
# =============================================================================
AFINIDAD_CARRERAS = {
    "Ingenieria Informatica": ["Ciencias de la Computacion", "Ingenieria", "Matematicas", "Robotica"],
    "Ciencias de la Computacion": ["Ingenieria Informatica", "Ingenieria", "Matematicas", "Robotica"],
    "Matematicas": ["Ciencias de la Computacion", "Ingenieria Informatica", "Ciencias Exactas", "Ciencias"],
    "Ingenieria Civil": ["Arquitectura", "Urbanismo", "Ingenieria"],
    "Arquitectura": ["Urbanismo", "Ingenieria Civil", "Ingenieria"],
    "Urbanismo": ["Arquitectura", "Ingenieria Civil"],
    "Ingenieria": ["Ingenieria Informatica", "Ingenieria Civil", "Robotica", "Ciencias Exactas", "Arquitectura"],
    "Robotica": ["Ingenieria", "Ingenieria Informatica", "Ciencias de la Computacion"],
    "Biologia": ["Ciencias", "Ciencias Exactas", "Medicina"],
    "Ciencias": ["Biologia", "Ciencias Exactas", "Matematicas", "Ingenieria"],
    "Ciencias Exactas": ["Matematicas", "Ciencias", "Biologia", "Ingenieria", "Fisica"],
    "Ciencias Sociales": ["Psicologia", "Desarrollo", "Economia", "Administracion de Empresas"],
    "Medicina": ["Biologia", "Ciencias"],
    "Administracion de Empresas": ["Economia", "Ciencias Sociales"],
    "Economia": ["Administracion de Empresas", "Ciencias Sociales", "Matematicas"],
    "Psicologia": ["Ciencias Sociales", "Desarrollo"],
    "Desarrollo": ["Ciencias Sociales", "Psicologia"],
    "Fisica": ["Ciencias Exactas", "Matematicas", "Ingenieria"],
}

# =============================================================================
# JERARQUÍA DE NIVELES DE IDIOMA
# =============================================================================
NIVELES_IDIOMA = {
    "A1": 1, "A2": 2,
    "B1": 3, "B2": 4,
    "C1": 5, "C2": 6,
    "N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5,
}

# =============================================================================
# PESOS DE PUNTUACIÓN
# =============================================================================
PESO_CARRERA_EXACTA = 30
PESO_CARRERA_AFIN = 20
PESO_CARRERA_TODAS = 15
PESO_GPA_CUMPLE = 25
PESO_IDIOMA_COMPLETO = 20
PESO_IDIOMA_PARCIAL = 10
PESO_PAIS_INTERES = 15
PESO_SITUACION_EC_EXACTA = 10
PESO_SITUACION_EC_ABIERTA = 5

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def normalizar_texto(texto):
    """Normaliza texto para comparacion: minusculas y sin espacios extra."""
    return texto.strip().lower()


def parsear_lista(texto):
    """Parsea un campo CSV que contiene una lista separada por comas."""
    if not texto or texto.strip() == "":
        return []
    return [item.strip() for item in texto.split(",") if item.strip()]


def parsear_idioma(idioma_str):
    """
    Parsea un string de idioma como 'Ingles C1' o 'Frances B2'.
    Retorna (idioma, nivel) o (idioma_str, None) si no se puede parsear.
    """
    partes = idioma_str.strip().split()
    if len(partes) >= 2:
        idioma = " ".join(partes[:-1])
        nivel = partes[-1].upper()
        return (idioma, nivel)
    return (idioma_str.strip(), None)


def comparar_nivel_idioma(nivel_estudiante, nivel_requerido):
    """Compara si el nivel de idioma del estudiante cumple o supera el requerido."""
    val_est = NIVELES_IDIOMA.get(nivel_estudiante.upper(), 0)
    val_req = NIVELES_IDIOMA.get(nivel_requerido.upper(), 0)
    return val_est >= val_req


def es_carrera_afin(carrera_estudiante, carrera_beca):
    """
    Determina si la carrera del estudiante es afin a la carrera de la beca.
    Retorna: 'exacta', 'afin', o 'no_afin'
    """
    ce = carrera_estudiante.strip()
    cb = carrera_beca.strip()

    if normalizar_texto(ce) == normalizar_texto(cb):
        return "exacta"

    afines = AFINIDAD_CARRERAS.get(ce, [])
    if any(normalizar_texto(cb) == normalizar_texto(a) for a in afines):
        return "afin"

    if normalizar_texto(cb) in normalizar_texto(ce) or normalizar_texto(ce) in normalizar_texto(cb):
        return "afin"

    return "no_afin"


def verificar_idiomas(idiomas_estudiante, idiomas_requeridos):
    """
    Verifica cuantos idiomas requeridos cumple el estudiante.
    Retorna: 'completo', 'parcial', o 'ninguno'
    """
    if not idiomas_requeridos:
        return "completo"

    idiomas_est_dict = {}
    for id_str in idiomas_estudiante:
        idioma, nivel = parsear_idioma(id_str)
        if idioma not in idiomas_est_dict:
            idiomas_est_dict[idioma] = []
        if nivel:
            idiomas_est_dict[idioma].append(nivel)

    cumplidos = 0
    total = len(idiomas_requeridos)

    for req_str in idiomas_requeridos:
        req_idioma, req_nivel = parsear_idioma(req_str)
        if not req_nivel:
            if any(normalizar_texto(req_idioma) in normalizar_texto(k) for k in idiomas_est_dict.keys()):
                cumplidos += 1
            continue

        for est_idioma, est_niveles in idiomas_est_dict.items():
            if normalizar_texto(est_idioma) == normalizar_texto(req_idioma):
                for est_nivel in est_niveles:
                    if comparar_nivel_idioma(est_nivel, req_nivel):
                        cumplidos += 1
                        break
                break

    if cumplidos == total:
        return "completo"
    elif cumplidos > 0:
        return "parcial"
    else:
        return "ninguno"


def calcular_puntuacion(estudiante, beca):
    """
    Calcula la puntuacion de afinidad entre un estudiante y una beca.
    Retorna un diccionario con la puntuacion total y el desglose.
    """
    desglose = {}
    puntuacion_total = 0
    elegible = True

    # ----- 1. Coincidencia de carrera -----
    carreras_beca = parsear_lista(beca["carreras_aceptadas"])
    carrera_est = estudiante["carrera"].strip()

    mejor_coincidencia = "no_afin"
    for cb in carreras_beca:
        if normalizar_texto(cb) == normalizar_texto("Todas las carreras"):
            mejor_coincidencia = "todas"
            break
        coincidencia = es_carrera_afin(carrera_est, cb)
        if coincidencia == "exacta":
            mejor_coincidencia = "exacta"
            break
        elif coincidencia == "afin" and mejor_coincidencia != "exacta":
            mejor_coincidencia = "afin"

    if mejor_coincidencia == "exacta":
        pts = PESO_CARRERA_EXACTA
        desglose["carrera"] = f"Exacta ({carrera_est}) -> +{pts}"
    elif mejor_coincidencia == "afin":
        pts = PESO_CARRERA_AFIN
        desglose["carrera"] = f"Afin ({carrera_est}) -> +{pts}"
    elif mejor_coincidencia == "todas":
        pts = PESO_CARRERA_TODAS
        desglose["carrera"] = f"Todas las carreras -> +{pts}"
    else:
        pts = 0
        desglose["carrera"] = f"Sin coincidencia -> +0"
        elegible = False

    puntuacion_total += pts

    # ----- 2. GPA -----
    try:
        gpa_est = float(estudiante["gpa"])
        gpa_min = float(beca["gpa_minimo"])
    except (ValueError, KeyError):
        gpa_est = 0
        gpa_min = 0

    if gpa_est >= gpa_min:
        pts = PESO_GPA_CUMPLE
        desglose["gpa"] = f"GPA {gpa_est} >= {gpa_min} -> +{pts}"
    else:
        pts = 0
        desglose["gpa"] = f"GPA {gpa_est} < {gpa_min} -> +0"
        elegible = False

    puntuacion_total += pts

    # ----- 3. Idiomas -----
    idiomas_est = parsear_lista(estudiante["idiomas"])
    idiomas_req = parsear_lista(beca["idioma_requerido"])
    resultado_idioma = verificar_idiomas(idiomas_est, idiomas_req)

    if resultado_idioma == "completo":
        pts = PESO_IDIOMA_COMPLETO
        desglose["idioma"] = f"Completo -> +{pts}"
    elif resultado_idioma == "parcial":
        pts = PESO_IDIOMA_PARCIAL
        desglose["idioma"] = f"Parcial -> +{pts}"
    else:
        pts = 0
        desglose["idioma"] = f"No cumple -> +0"

    puntuacion_total += pts

    # ----- 4. Pais de interes -----
    paises_interes = parsear_lista(estudiante["pais_interes"])
    pais_beca = beca["pais"].strip()

    if any(normalizar_texto(p) == normalizar_texto(pais_beca) for p in paises_interes):
        pts = PESO_PAIS_INTERES
        desglose["pais"] = f"{pais_beca} en intereses -> +{pts}"
    else:
        pts = 0
        desglose["pais"] = f"{pais_beca} no en intereses -> +0"

    puntuacion_total += pts

    # ----- 5. Situacion economica -----
    sit_ec_beca = beca.get("situacion_ec", "").strip()
    sit_ec_est = estudiante.get("situacion_economica", "").strip()

    if sit_ec_beca and sit_ec_est:
        if normalizar_texto(sit_ec_beca) == normalizar_texto(sit_ec_est):
            pts = PESO_SITUACION_EC_EXACTA
            desglose["situacion_ec"] = f"Coincide ({sit_ec_est}) -> +{pts}"
        else:
            pts = 0
            desglose["situacion_ec"] = f"No coincide (est:{sit_ec_est}, beca:{sit_ec_beca}) -> +0"
    elif not sit_ec_beca:
        pts = PESO_SITUACION_EC_ABIERTA
        desglose["situacion_ec"] = f"Beca abierta (sin filtro) -> +{pts}"
    else:
        pts = 0
        desglose["situacion_ec"] = f"No aplica -> +0"

    puntuacion_total += pts

    return {
        "puntuacion": puntuacion_total,
        "desglose": desglose,
        "elegible": elegible,
    }


# =============================================================================
# LECTURA DE DATOS
# =============================================================================

def leer_csv(filepath):
    """Lee un archivo CSV y retorna una lista de diccionarios."""
    registros = []
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            registros.append(row)
    return registros


# =============================================================================
# GENERACION DEL REPORTE
# =============================================================================

def generar_reporte(recomendaciones, filepath, usa_ia=False):
    """
    Genera un reporte en formato .txt con las 3 becas mas afines por estudiante.
    Incluye explicaciones de Deepseek v3.2 si estan disponibles.
    """
    with open(filepath, mode="w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("  SISTEMA DE RECOMENDACION DE BECAS - REPORTE PERSONALIZADO\n")
        if usa_ia:
            f.write("  ** Potenciado con Deepseek v3.2 (MaaS Huawei Cloud) **\n")
        f.write(f"  Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for rec in recomendaciones:
            est = rec["estudiante"]
            f.write("-" * 80 + "\n")
            f.write(f"  ESTUDIANTE: {est['nombre']} (ID: {est['id_estudiante']})\n")
            f.write(f"  Carrera: {est['carrera']}  |  GPA: {est['gpa']}  |  "
                    f"Sit. Economica: {est.get('situacion_economica', 'N/A')}\n")
            f.write(f"  Idiomas: {est['idiomas']}\n")
            f.write(f"  Paises de interes: {est['pais_interes']}\n")
            f.write(f"  Email: {est.get('email', 'N/A')}\n")
            f.write("-" * 80 + "\n\n")

            # Resumen IA del estudiante
            if usa_ia and rec.get("resumen_ia"):
                f.write("  ** RESUMEN IA (Deepseek v3.2):\n")
                for linea in rec["resumen_ia"].strip().split("\n"):
                    f.write(f"    {linea.strip()}\n")
                f.write("\n")

            if not rec["becas_recomendadas"]:
                f.write("  !! No se encontraron becas elegibles para este estudiante.\n\n")
                continue

            for i, bec_rec in enumerate(rec["becas_recomendadas"], 1):
                beca = bec_rec["beca"]
                punt = bec_rec["puntuacion"]
                desglose = bec_rec["desglose"]

                f.write(f"  +--- RECOMENDACION #{i} ---\n")
                f.write(f"  | Beca: {beca['nombre_beca']} (ID: {beca['id_beca']})\n")
                f.write(f"  | Pais: {beca['pais']}  |  Monto: ${beca['monto']}\n")
                f.write(f"  | Carreras aceptadas: {beca['carreras_aceptadas']}\n")
                f.write(f"  | GPA minimo: {beca['gpa_minimo']}  |  Idioma requerido: {beca['idioma_requerido']}\n")
                f.write(f"  | Fecha de cierre: {beca['fecha_cierre']}  |  Requiere carta: {beca['requiere_carta']}\n")
                sit_ec = beca.get('situacion_ec', '').strip()
                f.write(f"  | Situacion economica beca: {sit_ec if sit_ec else 'Abierta (sin filtro)'}\n")
                f.write(f"  |\n")
                f.write(f"  | ** PUNTUACION TOTAL: {punt}/100\n")
                f.write(f"  |\n")
                f.write(f"  | Desglose de puntuacion:\n")
                for clave, detalle in desglose.items():
                    f.write(f"  |   - {clave}: {detalle}\n")

                # Explicacion IA de la recomendacion
                if usa_ia and bec_rec.get("explicacion_ia"):
                    f.write(f"  |\n")
                    f.write(f"  | ** Explicacion IA (Deepseek v3.2):\n")
                    for linea in bec_rec["explicacion_ia"].strip().split("\n"):
                        f.write(f"  |   {linea.strip()}\n")

                f.write(f"  +{'-' * 40}\n\n")

            f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("  FIN DEL REPORTE\n")
        f.write("=" * 80 + "\n")


# =============================================================================
# FUNCION PRINCIPAL
# =============================================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Rutas de archivos
    becas_path = os.path.join(base_dir, "becas.csv")
    estudiantes_path = os.path.join(base_dir, "estudiantes.csv")
    reporte_path = os.path.join(base_dir, "reporte_recomendaciones.txt")

    # Inicializar cliente MaaS (Deepseek v3.2)
    print("\n[Deepseek v3.2 MaaS] Inicializando cliente...")
    maas_client = MaaSClient()
    usa_ia = maas_client.is_configured
    if usa_ia:
        print("  OK Cliente MaaS configurado - Modo IA activado")
    else:
        print("  WARNING: Cliente MaaS no configurado - Modo fallback (sin IA)")

    # Leer datos
    print("\nLeyendo archivo de becas...")
    becas = leer_csv(becas_path)
    print(f"   OK {len(becas)} becas cargadas")

    print("Leyendo archivo de estudiantes...")
    estudiantes = leer_csv(estudiantes_path)
    print(f"   OK {len(estudiantes)} estudiantes cargados")

    # Procesar recomendaciones para cada estudiante
    recomendaciones = []

    for est in estudiantes:
        print(f"\nProcesando: {est['nombre']} ({est['carrera']}, GPA: {est['gpa']})")

        becas_evaluadas = []

        for beca in becas:
            resultado = calcular_puntuacion(est, beca)

            try:
                fecha_cierre = datetime.strptime(beca["fecha_cierre"].strip(), "%Y-%m-%d")
            except (ValueError, KeyError):
                fecha_cierre = datetime.max

            becas_evaluadas.append({
                "beca": beca,
                "puntuacion": resultado["puntuacion"],
                "desglose": resultado["desglose"],
                "elegible": resultado["elegible"],
                "fecha_cierre": fecha_cierre,
            })

        becas_elegibles = [b for b in becas_evaluadas if b["elegible"]]
        becas_elegibles.sort(key=lambda x: (-x["puntuacion"], x["fecha_cierre"]))

        top_3 = becas_elegibles[:3]

        for i, b in enumerate(top_3, 1):
            dias_restantes = (b["fecha_cierre"] - datetime.now()).days
            print(f"   #{i}: {b['beca']['nombre_beca']} "
                  f"(Puntaje: {b['puntuacion']}, "
                  f"Cierra: {b['beca']['fecha_cierre']} ({dias_restantes} dias restantes))")

        if not top_3:
            print("   WARNING: Sin becas elegibles")

        recomendaciones.append({
            "estudiante": est,
            "becas_recomendadas": top_3,
        })

    # Enriquecer con IA (Deepseek v3.2)
    if usa_ia:
        recomendaciones = enriquecer_reporte_con_ia(maas_client, recomendaciones)

    # Generar reporte
    print(f"\nGenerando reporte en: {reporte_path}")
    generar_reporte(recomendaciones, reporte_path, usa_ia=usa_ia)
    print("   OK Reporte generado exitosamente")

    # Resumen
    print("\n" + "=" * 60)
    print("  RESUMEN")
    print("=" * 60)
    for rec in recomendaciones:
        est = rec["estudiante"]
        n = len(rec["becas_recomendadas"])
        if n > 0:
            mejor = rec["becas_recomendadas"][0]
            print(f"  {est['nombre']}: {n} becas recomendadas "
                  f"(Mejor: {mejor['beca']['nombre_beca']} - {mejor['puntuacion']} pts)")
        else:
            print(f"  {est['nombre']}: Sin becas elegibles")
    print("=" * 60)


if __name__ == "__main__":
    main()
