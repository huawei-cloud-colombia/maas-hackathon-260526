from datetime import datetime, timedelta
from config import SCORING


def score_fecha_proxima(fecha_cierre_dt, fecha_evaluacion, max_days=90):
    if fecha_cierre_dt is None or fecha_evaluacion is None:
        return 0
    delta = (fecha_cierre_dt - fecha_evaluacion).days
    if delta < 0:
        return 0
    if delta == 0:
        return SCORING["fecha_proxima_max"]
    if delta <= max_days:
        return round(SCORING["fecha_proxima_max"] * (1 - delta / max_days), 1)
    return 0


def score_pais_interes(estudiante_pais_interes, beca_pais):
    if not estudiante_pais_interes or not beca_pais:
        return 0
    paises = [p.strip().lower() for p in str(estudiante_pais_interes).split(";") if p.strip()]
    if beca_pais.strip().lower() in paises:
        return SCORING["pais_interes"]
    return 0


def rank_becas(eligibility_results, fecha_evaluacion_str=None, afinidades_cache=None):
    if afinidades_cache is None:
        afinidades_cache = {}

    fecha_eval = None
    if fecha_evaluacion_str:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                fecha_eval = datetime.strptime(fecha_evaluacion_str.strip(), fmt)
                break
            except ValueError:
                continue

    eligible = [r for r in eligibility_results if r["eligible"]]

    scored = []
    for r in eligible:
        score = 0
        criteria = []

        if r["carrera_exacta"]:
            score += SCORING["carrera_exacta"]
            criteria.append("Carrera exacta")
        else:
            key = (r["estudiante_carrera"], r["id_beca"])
            afinidad = afinidades_cache.get(key)
            if afinidad and afinidad.get("es_afin"):
                score += SCORING["carrera_afin"]
                criteria.append(f"Carrera afín: {afinidad.get('razon_breve', 'validada por IA')}")
            else:
                score += 0
                criteria.append("Carrera no coincide")

        pais_score = score_pais_interes(r["estudiante_pais_interes"], r["beca_pais"])
        if pais_score > 0:
            score += pais_score
            criteria.append("País preferido")
        else:
            criteria.append("País no coincide")

        fecha_score = score_fecha_proxima(r["beca_fecha_cierre_dt"], fecha_eval)
        if fecha_score > 0:
            score += fecha_score
            criteria.append(f"Cierre próximo (+{fecha_score}pts)")
        else:
            criteria.append("Cierre no próximo")

        scored.append({
            **r,
            "score": score,
            "criteria": criteria,
            "ia_aplicada": key in afinidades_cache and afinidades_cache[key].get("es_afin") if not r["carrera_exacta"] else False,
        })

    scored.sort(key=lambda x: (
        -x["score"],
        x["beca_fecha_cierre_dt"] if x["beca_fecha_cierre_dt"] else datetime.max,
        -x["beca_monto"] if x["beca_monto"] else 0,
        x["id_beca"],
    ))

    results_by_student = {}
    for s in scored:
        eid = s["id_estudiante"]
        if eid not in results_by_student:
            results_by_student[eid] = {
                "id_estudiante": eid,
                "nombre_estudiante": s["nombre_estudiante"],
                "carrera": s["estudiante_carrera"],
                "gpa": s["estudiante_gpa"],
                "pais_interes": s["estudiante_pais_interes"],
                "situacion_ec": s["estudiante_situacion_ec"],
                "top_becas": [],
            }
        if len(results_by_student[eid]["top_becas"]) < 3:
            results_by_student[eid]["top_becas"].append(s)

    return scored, results_by_student
