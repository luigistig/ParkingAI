from flask import request, has_request_context
from app import db
from app.models import AuditLog


class AuditService:

    @staticmethod
    def log_event(
        accion,
        modulo,
        nivel="INFO",
        descripcion="",
        usuario="Sistema"
    ):

        try:

            # =========================
            # VALIDAR CONTEXTO REQUEST
            # =========================
            if has_request_context():
                ip_address = request.remote_addr
            else:
                ip_address = "127.0.0.1"

            # =========================
            # CREAR LOG
            # =========================
            log = AuditLog(
                usuario=usuario,
                accion=accion,
                modulo=modulo,
                nivel=nivel,
                ip=ip_address,
                descripcion=descripcion
            )

            db.session.add(log)
            db.session.commit()

            print(f"✅ LOG REGISTRADO: {accion}")

        except Exception as e:

            db.session.rollback()

            print(f"❌ ERROR AUDIT LOG: {e}")