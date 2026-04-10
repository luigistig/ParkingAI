"""
Punto de entrada de la aplicación Flask
"""

from app import create_app, db
from app.models import Vehicle, PaymentRecord, ParkingSpace, SystemLog
from flask import render_template, redirect
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear aplicación
app = create_app(os.getenv("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    """Contexto de shell para Flask"""
    return {
        "db": db,
        "Vehicle": Vehicle,
        "PaymentRecord": PaymentRecord,
        "ParkingSpace": ParkingSpace,
        "SystemLog": SystemLog,
    }


@app.route("/")
def landing():
    """Página de inicio - Landing page"""
    from flask import render_template

    return render_template("landing.html")


@app.route("/usuario")
def user_page():
    """Panel de usuario - Búsqueda de vehículos"""
    from flask import render_template

    return render_template("user_search.html")


@app.route("/entrada")
def camera_page():
    """Página de registro de entrada"""
    from flask import render_template

    return render_template("camera.html")


@app.route("/pago")
def payment_page():
    """Página de pago"""
    from flask import render_template

    return render_template("payment.html")


@app.route("/historial")
def history_page():
    """Página de historial"""
    from flask import render_template

    return render_template("history.html")


@app.route("/admin/login")
def admin_login():
    """Página de login para administrador"""
    from flask import session

    # Si ya está logeado, ir al dashboard
    if session.get("is_admin"):
        return redirect("/admin")

    return render_template("admin_login.html")


@app.route("/admin")
def admin_page():
    """Panel de administración - Requiere login"""
    from flask import session

    # Verificar si está logeado
    if not session.get("is_admin"):
        return redirect("/admin/login")

    return render_template("index.html")


@app.errorhandler(404)
def not_found(error):
    """Manejo de error 404"""
    return {"success": False, "error": "Página no encontrada"}, 404


@app.errorhandler(500)
def internal_error(error):
    """Manejo de error 500"""
    db.session.rollback()
    return {"success": False, "error": "Error interno del servidor"}, 500


if __name__ == "__main__":
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    # Ejecutar aplicación
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=debug,
        use_reloader=debug,
    )
