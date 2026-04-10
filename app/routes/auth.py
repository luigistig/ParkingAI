"""
Rutas para autenticación de administrador
"""

from flask import request, jsonify, render_template, session, redirect, url_for
from datetime import datetime, timedelta
import os


def admin_login():
    """Página de login del administrador"""
    return render_template("admin_login.html")


def login_post():
    """Procesar login del administrador"""
    try:
        data = request.get_json()

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        remember = data.get("remember", False)

        # Credenciales por defecto (en producción usar base de datos)
        ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

        # Validar credenciales
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            # Crear sesión
            session["admin_id"] = 1
            session["admin_name"] = "Administrador"
            session["admin_username"] = username
            session["is_admin"] = True

            # Hacer la sesión persistente si selecciona "Recuérdame"
            if remember:
                session.permanent = True
                session.expiration = timedelta(days=7)

            return jsonify(
                {
                    "success": True,
                    "message": "Sesión iniciada correctamente",
                    "admin_name": "Administrador",
                }
            )
        else:
            return (
                jsonify(
                    {"success": False, "error": "Usuario o contraseña incorrectos"}
                ),
                401,
            )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def check_session():
    """Verificar si hay sesión de admin activa"""
    try:
        is_admin = session.get("is_admin", False)
        admin_name = session.get("admin_name", "Admin")

        return jsonify(
            {
                "success": True,
                "is_admin": is_admin,
                "admin_name": admin_name if is_admin else None,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def logout():
    """Cerrar sesión del administrador"""
    try:
        session.clear()
        return redirect("/")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def require_admin(f):
    """Decorador para rutas que requieren admin"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorated_function
