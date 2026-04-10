"""
Inicializador de rutas
"""

from flask import Blueprint

# Crear blueprints
vehicle_bp = Blueprint("vehicles", __name__, url_prefix="/api/vehicles")
payment_bp = Blueprint("payments", __name__, url_prefix="/api/payments")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
camera_bp = Blueprint("camera", __name__, url_prefix="/api/camera")
auth_bp = Blueprint("auth", __name__, url_prefix="/api/admin")

# Importar rutas
from . import vehicles, payments, admin, camera, auth

# Registrar rutas de vehículos
vehicle_bp.add_url_rule("", "list", vehicles.list_vehicles, methods=["GET"])
vehicle_bp.add_url_rule(
    "/<int:vehicle_id>", "get", vehicles.get_vehicle, methods=["GET"]
)
vehicle_bp.add_url_rule(
    "/search/<placa>", "search", vehicles.search_vehicle, methods=["GET"]
)
vehicle_bp.add_url_rule(
    "/checkin", "checkin", vehicles.vehicle_checkin, methods=["POST"]
)
vehicle_bp.add_url_rule(
    "/checkout/<int:vehicle_id>",
    "checkout",
    vehicles.vehicle_checkout,
    methods=["POST"],
)

# Registrar rutas de pagos
payment_bp.add_url_rule(
    "/calculate", "calculate", payments.calculate_payment, methods=["POST"]
)
payment_bp.add_url_rule("", "create", payments.create_payment, methods=["POST"])
payment_bp.add_url_rule(
    "/history", "history", payments.payment_history, methods=["GET"]
)
payment_bp.add_url_rule(
    "/photos", "photos", payments.get_vehicle_photos, methods=["GET"]
)

# Registrar rutas de admin
admin_bp.add_url_rule("", "dashboard", admin.admin_dashboard, methods=["GET"])
admin_bp.add_url_rule(
    "/statistics", "statistics", admin.get_statistics, methods=["GET"]
)
admin_bp.add_url_rule("/logs", "logs", admin.get_logs, methods=["GET"])
admin_bp.add_url_rule(
    "/vehicles", "vehicles", admin.manage_vehicles, methods=["GET", "POST"]
)

# Registrar rutas de cámara
camera_bp.add_url_rule("/stream", "stream", camera.camera_stream, methods=["GET"])
camera_bp.add_url_rule(
    "/stream_ai", "camera_stream_ai", camera.camera_stream_ai, methods=["GET"]
)
camera_bp.add_url_rule("/capture", "capture", camera.capture_image, methods=["POST"])
camera_bp.add_url_rule("/detect", "detect", camera.detect_plate, methods=["POST"])
camera_bp.add_url_rule(
    "/detect_vehicle_auto",
    "detect_vehicle_auto",
    camera.detect_vehicle_auto,
    methods=["POST"],
)
camera_bp.add_url_rule(
    "/process_ai", "process_image_ai", camera.process_image_ai, methods=["POST"]
)

# Registrar rutas de autenticación
auth_bp.add_url_rule("/login", "admin_login", auth.admin_login, methods=["GET"])
auth_bp.add_url_rule("/login", "login_post", auth.login_post, methods=["POST"])
auth_bp.add_url_rule(
    "/check-session", "check_session", auth.check_session, methods=["GET"]
)
auth_bp.add_url_rule("/logout", "logout", auth.logout, methods=["GET"])
