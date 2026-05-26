from datetime import datetime
from config import CEFR_ORDER, EC_ORDER


def cefr_sufficient(student_level, required_level):
    s = CEFR_ORDER.get(student_level, 0)
    r = CEFR_ORDER.get(required_level, 0)
    return s >= r


def idioma_sufficient(estudiante_idiomas, req_lang, req_nivel):
    if not req_lang or not req_nivel:
        return True
    for idioma in estudiante_idiomas:
        if idioma["idioma"].lower() == req_lang.lower() and idioma["nivel"]:
            if cefr_sufficient(idioma["nivel"], req_nivel):
                return True
    return False


def gpa_eligible(estudiante_gpa, beca_gpa_min):
    if estudiante_gpa is None or beca_gpa_min is None:
        return False
    return estudiante_gpa >= beca_gpa_min


def beca_abierta(fecha_cierre_dt, fecha_evaluacion):
    if fecha_cierre_dt is None:
        return True
    if fecha_evaluacion is None:
        return True
    return fecha_cierre_dt >= fecha_evaluacion


def situacion_ec_eligible(estudiante_ec, beca_ec):
    if not beca_ec:
        return True, False
    if not estudiante_ec:
        return False, True
    s_order = EC_ORDER.get(estudiante_ec, 0)
    b_order = EC_ORDER.get(beca_ec, 0)
    if b_order == 0:
        return True, False
    eligible = s_order <= b_order
    pendiente = False
    return eligible, pendiente


def carrera_exacta(estudiante_carrera, beca_carreras):
    if not estudiante_carrera or not beca_carreras:
        return False
    return estudiante_carrera.strip() in [c.strip() for c in beca_carreras]


def filter_eligibility(estudiantes_df, becas_df, fecha_evaluacion_str=None):
    fecha_eval = None
    if fecha_evaluacion_str:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                fecha_eval = datetime.strptime(fecha_evaluacion_str.strip(), fmt)
                break
            except ValueError:
                continue

    results = []
    warnings = []

    for _, est in estudiantes_df.iterrows():
        for _, beca in becas_df.iterrows():
            reasons = []
            eligible = True
            pendiente_confirmar = False

            if not gpa_eligible(est["gpa"], beca["gpa_minimo"]):
                eligible = False
                reasons.append(f"GPA {est['gpa']} < {beca['gpa_minimo']} requerido")
            else:
                reasons.append("GPA cumple")

            if not idioma_sufficient(est["idiomas_lista"], beca["idioma_req_lang"], beca["idioma_req_nivel"]):
                eligible = False
                reasons.append(f"Idioma insuficiente: requiere {beca['idioma_req_lang']}-{beca['idioma_req_nivel']}")
            else:
                reasons.append("Idioma cumple")

            if not beca_abierta(beca["fecha_cierre_dt"], fecha_eval):
                eligible = False
                reasons.append(f"Beca cerrada: cierre {beca['fecha_cierre']}")
            else:
                reasons.append("Beca abierta")

            ec_eligible, ec_pendiente = situacion_ec_eligible(est["situacion_ec_norm"], beca["situacion_ec_norm"])
            if not ec_eligible:
                eligible = False
                reasons.append(f"Situación económica no elegible: estudiante={est['situacion_ec_norm']}, beca={beca['situacion_ec_norm']}")
            else:
                reasons.append("Situación económica cumple")
            if ec_pendiente:
                pendiente_confirmar = True
                warnings.append(f"PENDIENTE_DE_CONFIRMAR: relación situacion_ec entre estudiante '{est['situacion_ec_norm']}' y beca '{beca['situacion_ec_norm']}'")

            is_exact = carrera_exacta(est["carrera"], beca["carreras_lista"])

            results.append({
                "id_estudiante": est["id_estudiante"],
                "nombre_estudiante": est["nombre"],
                "id_beca": beca["id_beca"],
                "nombre_beca": beca["nombre_beca"],
                "eligible": eligible,
                "carrera_exacta": is_exact,
                "pendiente_confirmar": pendiente_confirmar,
                "reasons": reasons,
                "estudiante_carrera": est["carrera"],
                "estudiante_gpa": est["gpa"],
                "estudiante_pais_interes": est["pais_interes"],
                "estudiante_situacion_ec": est["situacion_ec_norm"],
                "beca_pais": beca["pais"],
                "beca_monto": beca["monto"],
                "beca_gpa_minimo": beca["gpa_minimo"],
                "beca_idioma_req": f"{beca['idioma_req_lang']}-{beca['idioma_req_nivel']}" if beca["idioma_req_lang"] else "",
                "beca_fecha_cierre": beca["fecha_cierre"],
                "beca_fecha_cierre_dt": beca["fecha_cierre_dt"],
                "beca_requiere_carta": beca["requiere_carta_bool"],
                "beca_situacion_ec": beca["situacion_ec_norm"],
            })

    return results, list(set(warnings))
