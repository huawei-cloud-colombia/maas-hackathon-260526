from flask import Flask, render_template, jsonify, request
from app.data_loader import load_becas, load_estudiantes
from app.recommender import recomendar_becas, obtener_estadisticas

app = Flask(__name__)

becas = load_becas()
estudiantes = load_estudiantes()
becas_dict = {b['id_beca']: b for b in becas}
estudiantes_dict = {e['id_estudiante']: e for e in estudiantes}


@app.route('/')
def index():
    return render_template('index.html', estudiantes=estudiantes)


@app.route('/estudiante/<int:id_estudiante>')
def perfil_estudiante(id_estudiante):
    estudiante = estudiantes_dict.get(id_estudiante)
    if not estudiante:
        return render_template('error.html', mensaje='Estudiante no encontrado'), 404
    top_n = request.args.get('top_n', default=None, type=int)
    recomendaciones = recomendar_becas(estudiante, becas, top_n=top_n)
    stats = obtener_estadisticas(recomendaciones)
    return render_template(
        'recomendaciones.html',
        estudiante=estudiante,
        recomendaciones=recomendaciones,
        stats=stats,
        score_maximo=100,
    )


@app.route('/beca/<int:id_beca>')
def detalle_beca(id_beca):
    beca = becas_dict.get(id_beca)
    if not beca:
        return render_template('error.html', mensaje='Beca no encontrada'), 404
    return render_template('beca.html', beca=beca)


@app.route('/becas')
def listar_becas():
    return render_template('becas.html', becas=becas)


@app.route('/api/estudiantes')
def api_estudiantes():
    return jsonify([{
        'id': e['id_estudiante'],
        'nombre': e['nombre'],
        'carrera': e['carrera'],
        'gpa': e['gpa'],
    } for e in estudiantes])


@app.route('/api/recomendar/<int:id_estudiante>')
def api_recomendar(id_estudiante):
    estudiante = estudiantes_dict.get(id_estudiante)
    if not estudiante:
        return jsonify({'error': 'Estudiante no encontrado'}), 404
    top_n = request.args.get('top_n', default=None, type=int)
    recomendaciones = recomendar_becas(estudiante, becas, top_n=top_n)
    stats = obtener_estadisticas(recomendaciones)
    result = []
    for rec in recomendaciones:
        beca = rec['beca']
        det = rec['detalle']
        result.append({
            'beca': {
                'id': beca['id_beca'],
                'nombre': beca['nombre_beca'],
                'pais': beca['pais'],
                'monto': beca['monto'],
                'fecha_cierre': beca['fecha_cierre'],
            },
            'score_total': rec['score_total'],
            'detalle': {
                'carrera': {'score': det['score_carrera'], 'tipo': det['carrera_tipo']},
                'gpa': {'score': det['score_gpa'], 'cumple': det['gpa_cumple']},
                'idioma': {'score': det['score_idioma'], 'detalle': det['idioma_detalle']},
                'pais': {'score': det['score_pais']},
                'fecha': {'score': det['score_fecha']},
            },
        })
    return jsonify({
        'estudiante': {
            'id': estudiante['id_estudiante'],
            'nombre': estudiante['nombre'],
            'carrera': estudiante['carrera'],
            'gpa': estudiante['gpa'],
        },
        'recomendaciones': result,
        'estadisticas': stats,
    })


@app.route('/api/becas')
def api_becas():
    return jsonify([{
        'id': b['id_beca'],
        'nombre': b['nombre_beca'],
        'pais': b['pais'],
        'monto': b['monto'],
        'gpa_minimo': b['gpa_minimo'],
        'fecha_cierre': b['fecha_cierre'],
    } for b in becas])


if __name__ == '__main__':
    app.run(debug=True, port=5001)
