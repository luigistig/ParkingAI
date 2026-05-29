"""Inicializador de la aplicación Flask"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import os

# =========================
# IMPORTS LOGGING
# =========================
from app.middleware.request_logger import init_request_logger
from app.middleware.error_logger import init_error_logger

db = SQLAlchemy()


def create_app(config_name="development"):
    """Factory para crear la aplicación Flask"""

    app = Flask(
        __name__,
        template_folder=os.path.join(
            os.path.dirname(__file__),
            "templates"
        ),
        static_folder=os.path.join(
            os.path.dirname(__file__),
            "static"
        ),
    )

    # =========================
    # CARGAR CONFIGURACIÓN
    # =========================
    app.config.from_object(config[config_name])

    # =========================
    # CONFIGURAR SESIONES
    # =========================
    app.secret_key = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )

    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7

    # =========================
    # INICIALIZAR EXTENSIONES
    # =========================
    db.init_app(app)

    # =========================
    # INICIALIZAR LOGGING
    # =========================
    init_request_logger(app)
    init_error_logger(app)

    # =========================
    # CREAR CARPETA UPLOADS
    # =========================
    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    # =========================
    # REGISTRAR BLUEPRINTS
    # =========================
    from app.routes import (
        vehicle_bp,
        payment_bp,
        admin_bp,
        camera_bp,
        auth_bp,
        audit_bp
    )

    app.register_blueprint(vehicle_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(audit_bp)

    # =========================
    # CREAR TABLAS
    # =========================
    with app.app_context():

        db.create_all()

        print("✅ Base de datos inicializada correctamente")

    return app