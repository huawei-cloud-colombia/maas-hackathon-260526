"""Motor de matching beca-estudiante: filtros duros + score base."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable

import pandas as pd

LEVEL_ORDER_CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_ORDER_JLPT = ["N5", "N4", "N3", "N2", "N1"]

EUROPA_PAISES = {
    "alemania", "espana", "francia", "italia", "reino unido", "belgica",
    "portugal", "paises bajos", "suecia", "noruega", "dinamarca", "finlandia",
    "polonia", "austria", "suiza", "irlanda", "grecia", "republica checa",
}


@dataclass
class Match:
    beca: dict
    score: float
    razones: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    explicacion_llm: str = ""


def _norm(s: str) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = str(s).strip().lower()
    repl = str.maketrans("áéíóúñü", "aeiounu")
    return s.translate(repl)


def _split_csv_field(s: str) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in str(s).split(",") if p.strip()]


def _parse_idiomas(spec: str) -> list[tuple[str, str]]:
    """'Ingles B2, Aleman A2' -> [('ingles','B2'), ('aleman','A2')]"""
    out = []
    for part in _split_csv_field(spec):
        m = re.match(r"^(.+?)\s+([A-C][12]|N[1-5])\s*$", part.strip(), re.IGNORECASE)
        if m:
            out.append((_norm(m.group(1)), m.group(2).upper()))
        else:
            out.append((_norm(part), ""))
    return out


def _nivel_suficiente(req_idioma: str, req_nivel: str, est_idiomas: list[tuple[str, str]]) -> bool:
    if not req_nivel:
        return any(req_idioma == i for i, _ in est_idiomas)
    order = LEVEL_ORDER_JLPT if req_nivel.startswith("N") else LEVEL_ORDER_CEFR
    if req_nivel not in order:
        return any(req_idioma == i for i, _ in est_idiomas)
    req_idx = order.index(req_nivel)
    for idioma, nivel in est_idiomas:
        if idioma != req_idioma:
            continue
        if not nivel or nivel not in order:
            continue
        if order.index(nivel) >= req_idx:
            return True
    return False


def _carrera_match(carrera_est: str, carreras_aceptadas: str) -> bool:
    aceptadas = _norm(carreras_aceptadas)
    if "todas las carreras" in aceptadas:
        return True
    carrera_est_n = _norm(carrera_est)
    tokens_est = set(carrera_est_n.split())
    for c in _split_csv_field(carreras_aceptadas):
        c_n = _norm(c)
        if c_n in carrera_est_n or carrera_est_n in c_n:
            return True
        tokens_c = set(c_n.split())
        if tokens_c & tokens_est:
            return True
    return False


def _pais_match(pais_beca: str, paises_interes: str) -> bool:
    pb = _norm(pais_beca)
    intereses = [_norm(p) for p in _split_csv_field(paises_interes)]
    if pb in intereses:
        return True
    if pb == "europa":
        return any(p in EUROPA_PAISES for p in intereses)
    if pb in EUROPA_PAISES and "europa" in intereses:
        return True
    return False


def _parse_fecha(s: str) -> date | None:
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def evaluar(estudiante: dict, beca: dict, hoy: date | None = None) -> Match:
    """Aplica filtros duros y devuelve un Match con score y razones.

    Un Match con score=0 y advertencias significa que NO pasa los filtros.
    """
    hoy = hoy or date.today()
    razones: list[str] = []
    advertencias: list[str] = []
    score = 0.0

    gpa_est = float(estudiante.get("gpa") or 0)
    gpa_min = float(beca.get("gpa_minimo") or 0)
    if gpa_est < gpa_min:
        advertencias.append(f"GPA insuficiente ({gpa_est} < {gpa_min})")
    else:
        margen = gpa_est - gpa_min
        score += 20 + min(margen * 10, 15)
        razones.append(f"GPA {gpa_est} cumple el mínimo de {gpa_min}")

    if _pais_match(beca["pais"], estudiante["pais_interes"]):
        score += 25
        razones.append(f"País destino ({beca['pais']}) está en tus intereses")
    else:
        advertencias.append(f"País {beca['pais']} fuera de tus intereses ({estudiante['pais_interes']})")

    if _carrera_match(estudiante["carrera"], beca["carreras_aceptadas"]):
        score += 20
        if "todas" in _norm(beca["carreras_aceptadas"]):
            razones.append("Beca abierta a todas las carreras")
        else:
            razones.append(f"Tu carrera ({estudiante['carrera']}) está dentro del área aceptada")
    else:
        advertencias.append(f"Carrera {estudiante['carrera']} no encaja con {beca['carreras_aceptadas']}")

    est_idiomas = _parse_idiomas(estudiante["idiomas"])
    req_idiomas = _parse_idiomas(beca["idioma_requerido"])
    faltan_idiomas = []
    for req_id, req_nv in req_idiomas:
        if not _nivel_suficiente(req_id, req_nv, est_idiomas):
            faltan_idiomas.append(f"{req_id.title()} {req_nv}".strip())
    if not faltan_idiomas:
        score += 20
        razones.append(f"Cumples todos los idiomas requeridos ({beca['idioma_requerido']})")
    else:
        advertencias.append("Te faltan idiomas: " + ", ".join(faltan_idiomas))

    sit_req = str(beca.get("situacion_ec") or "").strip().upper()
    sit_est = str(estudiante.get("situacion_economica") or "").strip().upper()
    if sit_req:
        if sit_req == sit_est:
            score += 10
            razones.append(f"Tu situación económica ({sit_est}) coincide con el perfil de la beca")
        else:
            advertencias.append(f"La beca está dirigida a situación {sit_req}, tu perfil es {sit_est}")
    else:
        score += 5
        razones.append("La beca no restringe por situación económica")

    fecha = _parse_fecha(beca.get("fecha_cierre"))
    if fecha and fecha < hoy:
        advertencias.append(f"Convocatoria cerrada el {fecha.isoformat()}")
        score -= 15
    elif fecha:
        dias = (fecha - hoy).days
        if dias <= 30:
            razones.append(f"Cierra pronto ({fecha.isoformat()}, en {dias} días)")
        else:
            razones.append(f"Cierra el {fecha.isoformat()}")

    monto = float(beca.get("monto") or 0)
    score += min(monto / 5000.0, 8)

    return Match(beca=beca, score=round(score, 2), razones=razones, advertencias=advertencias)


def top_matches(estudiante: dict, becas: Iterable[dict], k: int = 3, hoy: date | None = None) -> list[Match]:
    """Devuelve top-K matches priorizando becas válidas. Si no hay K válidas, completa con near-misses."""
    todos = [evaluar(estudiante, b, hoy=hoy) for b in becas]
    validos = [m for m in todos if not m.advertencias]
    near = [m for m in todos if m.advertencias]
    validos.sort(key=lambda m: m.score, reverse=True)
    near.sort(key=lambda m: m.score, reverse=True)
    seleccion = validos[:k]
    if len(seleccion) < k:
        seleccion += near[: k - len(seleccion)]
    return seleccion


def cargar_csvs(becas_path: str, estudiantes_path: str) -> tuple[list[dict], list[dict]]:
    becas = pd.read_csv(becas_path, dtype=str).fillna("").to_dict(orient="records")
    estudiantes = pd.read_csv(estudiantes_path, dtype=str).fillna("").to_dict(orient="records")
    return becas, estudiantes
