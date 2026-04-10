"""
Configuración de la aplicación de gestión de parqueadero inteligente
"""

import os
from datetime import timedelta

# Directorio base de la aplicación
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuración predeterminada"""

    # Base de datos
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "parqueadero.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sesión
    SECRET_KEY = "parqueadero-ia-2026-secret-key"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Rutas
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo para imágenes

    # Configuración de tarifa
    TARIFF_PER_HOUR = 2000  # 2000 pesos por hora
    MIN_CHARGE = 500  # Cargo mínimo

    # Configuración de OpenCV y OCR
    ENABLE_CAMERA = True
    CAMERA_INDEX = 0  # Cámara por defecto


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuración para pruebas"""

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Seleccionar configuración según el entorno
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
