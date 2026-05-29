import logging
import os
from logging.handlers import RotatingFileHandler

# Crear carpeta logs si no existe
LOG_DIR = "app/logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Formato global
LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)

formatter = logging.Formatter(LOG_FORMAT)

# Logger principal
logger = logging.getLogger("ParkingAI")
logger.setLevel(logging.DEBUG)

# =========================
# SYSTEM LOG
# =========================
system_handler = RotatingFileHandler(
    f"{LOG_DIR}/system.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

system_handler.setFormatter(formatter)
system_handler.setLevel(logging.INFO)

# =========================
# ERROR LOG
# =========================
error_handler = RotatingFileHandler(
    f"{LOG_DIR}/error.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)

# =========================
# ACCESS LOG
# =========================
access_handler = RotatingFileHandler(
    f"{LOG_DIR}/access.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

access_handler.setFormatter(formatter)
access_handler.setLevel(logging.INFO)

# =========================
# AUDIT LOG
# =========================
audit_handler = RotatingFileHandler(
    f"{LOG_DIR}/audit.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

audit_handler.setFormatter(formatter)
audit_handler.setLevel(logging.INFO)

# Agregar handlers
logger.addHandler(system_handler)
logger.addHandler(error_handler)
logger.addHandler(access_handler)
logger.addHandler(audit_handler)

# Consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)