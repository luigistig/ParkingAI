from flask import Blueprint, render_template
from app.models import AuditLog

audit_bp = Blueprint(
    "audit",
    __name__,
    url_prefix="/admin/logs"
)


@audit_bp.route("/")
def logs():

    logs = AuditLog.query.order_by(
        AuditLog.fecha.desc()
    ).all()

    return render_template(
        "admin/logs.html",
        logs=logs
    )