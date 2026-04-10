"""
Inicializador de la aplicación Flask
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import os

db = SQLAlchemy()


def create_app(config_name="development"):
    """Factory para crear la aplicación Flask"""

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    # Cargar configuración
    app.config.from_object(config[config_name])

    # Configurar sesiones
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["SESSION_COOKIE_SECURE"] = False  # True en producción con HTTPS
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7  # 7 días

    # Inicializar extensiones
    db.init_app(app)

    # Crear carpeta de uploads si no existe
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Registrar blueprints
    from app.routes import vehicle_bp, payment_bp, admin_bp, camera_bp, auth_bp

    app.register_blueprint(vehicle_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(auth_bp)

    # Crear tablas
    with app.app_context():
        db.create_all()

    return app
