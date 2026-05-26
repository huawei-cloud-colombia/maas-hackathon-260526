from app.app import app

if __name__ == '__main__':
    print("=" * 50)
    print("  BecaMatch - Sistema de Recomendacion de Becas")
    print("  Iniciando servidor en http://localhost:5001")
    print("=" * 50)
    app.run(debug=True, port=5001)
