"""
Motor de Recomendacion de Becas.

Implementa la logica de scoring y ranking basada en:
1. Coincidencia de carrera (exacta o afin)
2. GPA del estudiante vs minimo de la beca
3. Nivel de idioma del estudiante vs requerido
4. Pais de interes del estudiante
5. Prioridad por fecha de cierre (becas que cierran pronto primero)
"""

from datetime import datetime, date

# Mapeo de afinidad entre carreras
CARRERAS_AFINES = {
    'Ingenieria Informatica': ['Ingenieria', 'Ciencias de la Computacion', 'Ciencias Exactas', 'Matematicas'],
    'Ciencias de la Computacion': ['Ingenieria', 'Ingenieria Informatica', 'Matematicas', 'Ciencias Exactas'],
    'Ingenieria Civil': ['Ingenieria', 'Ciencias Exactas'],
    'Robotica': ['Ingenieria', 'Ciencias de la Computacion', 'Ciencias Exactas'],
    'Matematicas': ['Ciencias Exactas', 'Ciencias', 'Ingenieria Informatica', 'Ciencias de la Computacion'],
    'Biologia': ['Ciencias', 'Medicina'],
    'Medicina': ['Ciencias', 'Biologia'],
    'Arquitectura': ['Urbanismo', 'Ingenieria Civil'],
    'Administracion de Empresas': ['Economia', 'Desarrollo'],
    'Psicologia': ['Ciencias Sociales', 'Desarrollo'],
    'Economia': ['Administracion de Empresas', 'Ciencias Sociales'],
}

# Jerarquia de niveles de idioma
NIVELES_JERARQUIA = {
    'A1': 1, 'A2': 2,
    'B1': 3, 'B2': 4,
    'C1': 5, 'C2': 6,
    'N5': 1, 'N4': 2, 'N3': 3, 'N2': 4, 'N1': 5,
    'Nativo': 7,
}

# Pesos del scoring
PESOS = {
    'carrera': 30,
    'gpa': 20,
    'idioma': 25,
    'pais': 15,
    'fecha': 10,
}


def recomendar_becas(estudiante, becas, top_n=None):
    recomendaciones = []
    for beca in becas:
        scoring = calcular_scoring(estudiante, beca)
        if scoring['gpa_cumple'] and scoring['idioma_parcial']:
            recomendaciones.append({
                'beca': beca,
                'score_total': scoring['score_total'],
                'detalle': scoring,
            })
    recomendaciones.sort(key=lambda x: x['score_total'], reverse=True)
    if top_n is not None:
        recomendaciones = recomendaciones[:top_n]
    return recomendaciones


def calcular_scoring(estudiante, beca):
    score_carrera, carrera_tipo = _score_carrera(estudiante['carrera'], beca['carreras_aceptadas'])
    score_gpa, gpa_cumple = _score_gpa(estudiante['gpa'], beca['gpa_minimo'])
    score_idioma, idioma_detalle, idioma_parcial = _score_idioma(
        estudiante['idiomas'], beca['idioma_requerido']
    )
    score_pais = _score_pais(estudiante['pais_interes'], beca['pais'])
    score_fecha = _score_fecha(beca['fecha_cierre'])

    score_total = (
        PESOS['carrera'] * score_carrera +
        PESOS['gpa'] * score_gpa +
        PESOS['idioma'] * score_idioma +
        PESOS['pais'] * score_pais +
        PESOS['fecha'] * score_fecha
    )

    return {
        'score_carrera': round(score_carrera, 2),
        'carrera_tipo': carrera_tipo,
        'score_gpa': round(score_gpa, 2),
        'gpa_cumple': gpa_cumple,
        'score_idioma': round(score_idioma, 2),
        'idioma_detalle': idioma_detalle,
        'idioma_parcial': idioma_parcial,
        'score_pais': round(score_pais, 2),
        'score_fecha': round(score_fecha, 2),
        'score_total': round(score_total, 2),
        'score_maximo': sum(PESOS.values()),
    }


def _score_carrera(carrera_estudiante, carreras_aceptadas):
    carrera_norm = carrera_estudiante.strip()
    if any(c.lower().strip() == 'todas las carreras' for c in carreras_aceptadas):
        return 0.4, 'todas'
    for c in carreras_aceptadas:
        if carrera_norm.lower() == c.strip().lower():
            return 1.0, 'exacta'
    for c in carreras_aceptadas:
        c_norm = c.strip()
        if c_norm.lower() in carrera_norm.lower() or carrera_norm.lower() in c_norm.lower():
            return 0.85, 'exacta'
    carreras_afines = CARRERAS_AFINES.get(carrera_norm, [])
    for c in carreras_aceptadas:
        if c.strip() in carreras_afines:
            return 0.7, 'afin'
    for c in carreras_aceptadas:
        c_norm = c.strip()
        if carrera_norm in CARRERAS_AFINES.get(c_norm, []):
            return 0.7, 'afin'
    return 0.0, 'no_coincide'


def _score_gpa(gpa_estudiante, gpa_minimo):
    if gpa_estudiante >= gpa_minimo:
        excedente = gpa_estudiante - gpa_minimo
        bonus = min(excedente * 0.1, 0.2)
        return 1.0 + bonus, True
    return 0.0, False


def _score_idioma(idiomas_estudiante, idiomas_requeridos):
    if not idiomas_requeridos:
        return 1.0, [], True
    detalle = []
    cumplimientos = []
    for req in idiomas_requeridos:
        req_idioma = req['idioma']
        req_nivel = req['nivel']
        mejor_match = 0.0
        cumple = False
        for est_idioma in idiomas_estudiante:
            if _idiomas_compatibles(est_idioma['idioma'], req_idioma):
                nivel_est = NIVELES_JERARQUIA.get(est_idioma['nivel'], 0)
                nivel_req = NIVELES_JERARQUIA.get(req_nivel, 0)
                if nivel_est >= nivel_req:
                    cumple = True
                    excedente = nivel_est - nivel_req
                    match = 1.0 + min(excedente * 0.1, 0.2)
                    mejor_match = max(mejor_match, match)
                elif nivel_est > 0:
                    ratio = nivel_est / nivel_req if nivel_req > 0 else 0
                    mejor_match = max(mejor_match, ratio * 0.5)
        cumplimientos.append(mejor_match if cumple else mejor_match)
        detalle.append({
            'idioma': req_idioma,
            'nivel_requerido': req_nivel,
            'cumple': cumple,
            'match': round(mejor_match, 2),
        })
    score_promedio = sum(cumplimientos) / len(cumplimientos) if cumplimientos else 0
    score_normalizado = min(score_promedio, 1.2)
    parcial = any(d['cumple'] for d in detalle)
    return score_normalizado, detalle, parcial


def _idiomas_compatibles(idioma1, idioma2):
    i1 = idioma1.lower().strip()
    i2 = idioma2.lower().strip()
    if i1 == i2:
        return True
    sinonimos = {
        'ingles': {'english', 'ingles', 'ing'},
        'espanol': {'espanol', 'spanish', 'esp', 'castellano'},
        'frances': {'frances', 'french', 'fra'},
        'aleman': {'aleman', 'german', 'deu'},
        'japones': {'japones', 'japanese', 'jpn'},
        'italiano': {'italiano', 'italian', 'ita'},
        'portugues': {'portugues', 'portuguese', 'por'},
        'neerlandes': {'neerlandes', 'dutch', 'nld', 'holandes'},
    }
    for key, syns in sinonimos.items():
        if i1 in syns and i2 in syns:
            return True
    return False


def _score_pais(paises_interes, pais_beca):
    pais_beca_norm = pais_beca.strip().lower()
    for pais in paises_interes:
        if pais.strip().lower() == pais_beca_norm:
            return 1.0
    regiones = {
        'europa': {'alemania', 'espana', 'francia', 'belgica', 'reino unido', 'italia'},
    }
    for region, paises in regiones.items():
        if pais_beca_norm == region:
            for pais in paises_interes:
                if pais.strip().lower() in paises:
                    return 0.8
        for pais in paises_interes:
            if pais.strip().lower() == region and pais_beca_norm in paises:
                return 0.8
    return 0.0


def _score_fecha(fecha_cierre_str):
    try:
        fecha_cierre = datetime.strptime(fecha_cierre_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return 0.5
    hoy = date.today()
    dias_restantes = (fecha_cierre - hoy).days
    if dias_restantes <= 0:
        return 0.0
    elif dias_restantes <= 30:
        return 1.0
    elif dias_restantes <= 90:
        return 0.8
    elif dias_restantes <= 180:
        return 0.6
    elif dias_restantes <= 365:
        return 0.4
    else:
        return 0.2


def obtener_estadisticas(recomendaciones):
    if not recomendaciones:
        return {'total': 0, 'score_promedio': 0, 'score_max': 0, 'score_min': 0}
    scores = [r['score_total'] for r in recomendaciones]
    return {
        'total': len(recomendaciones),
        'score_promedio': round(sum(scores) / len(scores), 2),
        'score_max': round(max(scores), 2),
        'score_min': round(min(scores), 2),
    }