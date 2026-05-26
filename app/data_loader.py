"""
Módulo de carga de datos desde archivos CSV.
Maneja la lectura y parseo de becas y estudiantes.
"""

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')


def load_becas(filepath=None):
    """Carga el archivo CSV de becas y retorna una lista de diccionarios."""
    if filepath is None:
        filepath = os.path.join(DOCS_DIR, 'becas.csv')

    df = pd.read_csv(filepath)

    becas = []
    for _, row in df.iterrows():
        beca = {
            'id_beca': int(row['id_beca']),
            'nombre_beca': str(row['nombre_beca']).strip(),
            'pais': str(row['pais']).strip(),
            'monto': float(row['monto']),
            'carreras_aceptadas': _parse_list(row['carreras_aceptadas']),
            'gpa_minimo': float(row['gpa_minimo']),
            'idioma_requerido': _parse_idiomas(row['idioma_requerido']),
            'fecha_cierre': str(row['fecha_cierre']).strip(),
            'requiere_carta': _parse_bool(row['requiere_carta']),
            'situacion_ec': str(row.get('situacion_ec', '')).strip() if pd.notna(row.get('situacion_ec', '')) else '',
        }
        becas.append(beca)

    return becas


def load_estudiantes(filepath=None):
    """Carga el archivo CSV de estudiantes y retorna una lista de diccionarios."""
    if filepath is None:
        filepath = os.path.join(DOCS_DIR, 'estudiantes.csv')

    df = pd.read_csv(filepath)

    estudiantes = []
    for _, row in df.iterrows():
        estudiante = {
            'id_estudiante': int(row['id_estudiante']),
            'nombre': str(row['nombre']).strip(),
            'carrera': str(row['carrera']).strip(),
            'gpa': float(row['gpa']),
            'idiomas': _parse_idiomas(row['idiomas']),
            'pais_interes': _parse_list(row['pais_interes']),
            'situacion_economica': str(row['situacion_economica']).strip(),
            'email': str(row['email']).strip(),
        }
        estudiantes.append(estudiante)

    return estudiantes


def _parse_list(value):
    """Parsea un string separado por comas en una lista limpia."""
    if pd.isna(value):
        return []
    items = str(value).split(',')
    return [item.strip() for item in items if item.strip()]


def _parse_idiomas(value):
    """
    Parsea un string de idiomas en una lista de diccionarios.
    Ejemplo: 'Ingles C1, Frances A2' -> [{'idioma': 'Ingles', 'nivel': 'C1'}, ...]
    """
    if pd.isna(value):
        return []

    idiomas = []
    parts = str(value).split(',')

    for part in parts:
        part = part.strip()
        if not part:
            continue

        tokens = part.rsplit(' ', 1)
        if len(tokens) == 2 and _is_level(tokens[1]):
            idiomas.append({
                'idioma': tokens[0].strip(),
                'nivel': tokens[1].strip()
            })
        else:
            idiomas.append({
                'idioma': part.strip(),
                'nivel': 'Nativo'
            })

    return idiomas


def _is_level(token):
    """Verifica si un token es un nivel de idioma válido."""
    valid_levels = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'N1', 'N2', 'N3', 'N4', 'N5'}
    return token.upper() in valid_levels


def _parse_bool(value):
    """Parsea un valor booleano desde CSV."""
    if pd.isna(value):
        return False
    return str(value).strip().lower() in ('si', 'sí', 'yes', 'true', '1')