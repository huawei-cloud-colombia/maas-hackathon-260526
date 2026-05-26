import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.data_loader import load_becas, load_estudiantes
from services.eligibility import filter_eligibility
from services.ranking import rank_becas
from services.maas_client import MaaSClient, resolve_afinidades
from config import FECHA_EVALUACION

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "becamatch-dev-key-change-in-prod")
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/load-default", methods=["POST"])
def load_default():
    becas_path = os.path.join(UPLOAD_FOLDER, "becas.csv")
    estudiantes_path = os.path.join(UPLOAD_FOLDER, "estudiantes.csv")
    if not os.path.exists(becas_path) or not os.path.exists(estudiantes_path):
        return jsonify({"error": "No se encontraron becas.csv o estudiantes.csv en data/"}), 404
    fecha_eval = request.form.get("fecha_evaluacion", FECHA_EVALUACION or "") if request.form else (FECHA_EVALUACION or "")
    try:
        becas_df = load_becas(becas_path)
        estudiantes_df = load_estudiantes(estudiantes_path)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error procesando CSV: {str(e)}"}), 400
    try:
        eligibility_results, warnings = filter_eligibility(estudiantes_df, becas_df, fecha_eval)
    except Exception as e:
        return jsonify({"error": f"Error en elegibilidad: {str(e)}"}), 500
    maas_client = MaaSClient()
    ia_available = maas_client.available
    afinidades_cache = {}
    if ia_available:
        eligible_non_exact = [r for r in eligibility_results if r["eligible"] and not r["carrera_exacta"]]
        if eligible_non_exact:
            afinidades_cache = resolve_afinidades(eligibility_results, becas_df, maas_client)
    scored, results_by_student = rank_becas(eligibility_results, fecha_eval, afinidades_cache)
    ia_enriched_count = sum(1 for s in scored if s.get("ia_aplicada"))
    explanations = {}
    if ia_available:
        for sid, sdata in results_by_student.items():
            for b in sdata["top_becas"]:
                exp = maas_client.generar_explicacion(
                    b["nombre_estudiante"], b["estudiante_carrera"],
                    b["nombre_beca"], b["beca_pais"],
                    b["criteria"], b["score"]
                )
                if exp:
                    explanations[(sid, b["id_beca"])] = exp
    session["results"] = {
        "by_student": {k: _serialize_student(v) for k, v in results_by_student.items()},
        "all_scored": [_serialize_scored(s) for s in scored],
        "warnings": warnings,
        "fecha_evaluacion": fecha_eval,
        "metrics": {
            "estudiantes": len(estudiantes_df),
            "becas": len(becas_df),
            "elegibles": len(scored),
            "ia_enriched": ia_enriched_count,
            "ia_available": ia_available,
        },
        "explanations": {f"{k[0]}|{k[1]}": v for k, v in explanations.items()},
    }
    return jsonify({"success": True, "data": session["results"]})


@app.route("/upload", methods=["POST"])
def upload_files():
    becas_file = request.files.get("becas_csv")
    estudiantes_file = request.files.get("estudiantes_csv")
    fecha_eval = request.form.get("fecha_evaluacion", FECHA_EVALUACION or "")

    if not becas_file or not estudiantes_file:
        return jsonify({"error": "Debe subir ambos archivos CSV"}), 400

    try:
        becas_content = becas_file.read().decode("utf-8")
        estudiantes_content = estudiantes_file.read().decode("utf-8")
        becas_df = load_becas(becas_content)
        estudiantes_df = load_estudiantes(estudiantes_content)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error procesando CSV: {str(e)}"}), 400

    try:
        eligibility_results, warnings = filter_eligibility(estudiantes_df, becas_df, fecha_eval)
    except Exception as e:
        return jsonify({"error": f"Error en elegibilidad: {str(e)}"}), 500

    maas_client = MaaSClient()
    ia_available = maas_client.available

    afinidades_cache = {}
    if ia_available:
        eligible_non_exact = [r for r in eligibility_results if r["eligible"] and not r["carrera_exacta"]]
        if eligible_non_exact:
            afinidades_cache = resolve_afinidades(eligibility_results, becas_df, maas_client)

    scored, results_by_student = rank_becas(eligibility_results, fecha_eval, afinidades_cache)

    ia_enriched_count = sum(1 for s in scored if s.get("ia_aplicada"))

    explanations = {}
    if ia_available:
        for sid, sdata in results_by_student.items():
            for b in sdata["top_becas"]:
                exp = maas_client.generar_explicacion(
                    b["nombre_estudiante"], b["estudiante_carrera"],
                    b["nombre_beca"], b["beca_pais"],
                    b["criteria"], b["score"]
                )
                if exp:
                    explanations[(sid, b["id_beca"])] = exp

    session["results"] = {
        "by_student": {k: _serialize_student(v) for k, v in results_by_student.items()},
        "all_scored": [_serialize_scored(s) for s in scored],
        "warnings": warnings,
        "fecha_evaluacion": fecha_eval,
        "metrics": {
            "estudiantes": len(estudiantes_df),
            "becas": len(becas_df),
            "elegibles": len(scored),
            "ia_enriched": ia_enriched_count,
            "ia_available": ia_available,
        },
        "explanations": {f"{k[0]}|{k[1]}": v for k, v in explanations.items()},
    }

    return jsonify({"success": True, "data": session["results"]})


@app.route("/results")
def results_page():
    data = session.get("results")
    if not data:
        return render_template("index.html", error="No hay resultados. Cargue los CSV primero.")
    return render_template("results.html", data=data)


@app.route("/download/txt")
def download_txt():
    data = session.get("results")
    if not data:
        return jsonify({"error": "No hay resultados"}), 404
    report = _generate_report(data)
    filepath = os.path.join(OUTPUT_FOLDER, "reporte_recomendaciones.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    return send_file(filepath, as_attachment=True, download_name="reporte_recomendaciones.txt")


@app.route("/download/csv")
def download_csv():
    data = session.get("results")
    if not data:
        return jsonify({"error": "No hay resultados"}), 404
    lines = ["id_estudiante,nombre_estudiante,carrera,gpa,pais_interes,posicion,id_beca,nombre_beca,pais_beca,monto,score,criteria"]
    for sid, sdata in data["by_student"].items():
        for i, b in enumerate(sdata["top_becas"], 1):
            criteria_str = "; ".join(b["criteria"])
            lines.append(f"{sid},{sdata['nombre_estudiante']},{sdata['carrera']},{sdata['gpa']},{sdata['pais_interes']},{i},{b['id_beca']},{b['nombre_beca']},{b['beca_pais']},{b['beca_monto']},{b['score']},\"{criteria_str}\"")
    filepath = os.path.join(OUTPUT_FOLDER, "reporte_recomendaciones.csv")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return send_file(filepath, as_attachment=True, download_name="reporte_recomendaciones.csv")


@app.route("/api/results")
def api_results():
    data = session.get("results")
    if not data:
        return jsonify({"error": "No hay resultados"}), 404
    return jsonify(data)


def _serialize_student(s):
    return {
        "id_estudiante": s["id_estudiante"],
        "nombre_estudiante": s["nombre_estudiante"],
        "carrera": s["carrera"],
        "gpa": s["gpa"],
        "pais_interes": s["pais_interes"],
        "situacion_ec": s["situacion_ec"],
        "top_becas": [_serialize_scored(b) for b in s["top_becas"]],
    }


def _serialize_scored(s):
    return {
        "id_estudiante": s["id_estudiante"],
        "nombre_estudiante": s["nombre_estudiante"],
        "id_beca": s["id_beca"],
        "nombre_beca": s["nombre_beca"],
        "eligible": s["eligible"],
        "carrera_exacta": s["carrera_exacta"],
        "pendiente_confirmar": s.get("pendiente_confirmar", False),
        "reasons": s["reasons"],
        "estudiante_carrera": s["estudiante_carrera"],
        "estudiante_gpa": s["estudiante_gpa"],
        "estudiante_pais_interes": s["estudiante_pais_interes"],
        "estudiante_situacion_ec": s["estudiante_situacion_ec"],
        "beca_pais": s["beca_pais"],
        "beca_monto": s["beca_monto"],
        "beca_gpa_minimo": s["beca_gpa_minimo"],
        "beca_idioma_req": s["beca_idioma_req"],
        "beca_fecha_cierre": s["beca_fecha_cierre"],
        "beca_requiere_carta": s["beca_requiere_carta"],
        "beca_situacion_ec": s["beca_situacion_ec"],
        "score": s["score"],
        "criteria": s["criteria"],
        "ia_aplicada": s.get("ia_aplicada", False),
    }


def _generate_report(data):
    fecha_eval = data.get("fecha_evaluacion", "No configurada")
    metrics = data.get("metrics", {})
    warnings = data.get("warnings", [])
    explanations = data.get("explanations", {})

    lines = [
        "=" * 70,
        "REPORTE DE RECOMENDACIONES DE BECAS - BecaMatch AI",
        "=" * 70,
        f"Fecha de evaluación: {fecha_eval}",
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "MÉTRICAS",
        "-" * 40,
        f"Estudiantes procesados: {metrics.get('estudiantes', 0)}",
        f"Becas evaluadas: {metrics.get('becas', 0)}",
        f"Matches elegibles: {metrics.get('elegibles', 0)}",
        f"Recomendaciones enriquecidas con IA: {metrics.get('ia_enriched', 0)}",
        f"IA disponible: {'Sí' if metrics.get('ia_available') else 'No (modo fallback)'}",
        "",
    ]

    if warnings:
        lines.append("ADVERTENCIAS")
        lines.append("-" * 40)
        for w in warnings:
            lines.append(f"  ⚠ {w}")
        lines.append("")

    lines.append("TOP 3 BECAS POR ESTUDIANTE")
    lines.append("=" * 70)

    for sid, sdata in data.get("by_student", {}).items():
        lines.append("")
        lines.append(f"Estudiante: {sdata['nombre_estudiante']} (ID: {sid})")
        lines.append(f"  Carrera: {sdata['carrera']}")
        lines.append(f"  GPA: {sdata['gpa']}")
        lines.append(f"  País de interés: {sdata['pais_interes']}")
        lines.append(f"  Situación económica: {sdata['situacion_ec']}")
        lines.append("")

        if not sdata["top_becas"]:
            lines.append("  No se encontraron becas elegibles.")
        else:
            for i, b in enumerate(sdata["top_becas"], 1):
                lines.append(f"  {i}. {b['nombre_beca']} ({b['id_beca']})")
                lines.append(f"     País: {b['beca_pais']} | Monto: ${b['beca_monto']:,.0f}")
                lines.append(f"     Puntaje: {b['score']}/100")
                lines.append(f"     Criterios: {', '.join(b['criteria'])}")
                lines.append(f"     Fecha cierre: {b['beca_fecha_cierre']} | Carta: {'Sí' if b['beca_requiere_carta'] else 'No'}")
                if b.get("ia_aplicada"):
                    lines.append(f"     IA aplicada: Sí")
                exp_key = f"{sid}|{b['id_beca']}"
                if exp_key in explanations:
                    lines.append(f"     Explicación IA: {explanations[exp_key]}")
                lines.append("")

    lines.append("=" * 70)
    lines.append("Fin del reporte - BecaMatch AI")
    return "\n".join(lines)


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=True, host="0.0.0.0", port=port)
