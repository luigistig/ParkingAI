"""
Rutas para panel de administración
"""

from flask import render_template, jsonify, request
from app import db
from app.models import Vehicle, PaymentRecord, SystemLog
from datetime import datetime, timedelta
from sqlalchemy import func
from app.routes.auth import require_admin


@require_admin
def admin_dashboard():
    """Panel de administración"""
    return render_template("admin.html")


@require_admin
def get_statistics():
    """Obtener estadísticas del sistema"""
    try:
        # Vehículos activos
        active_vehicles = Vehicle.query.filter_by(estado="dentro").count()

        # Ingresos totales hoy
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        today_income = (
            db.session.query(func.sum(PaymentRecord.monto))
            .filter(PaymentRecord.fecha_pago.between(today_start, today_end))
            .scalar()
            or 0
        )

        # Ingresos totales este mes
        month_start = today.replace(day=1)
        month_income = (
            db.session.query(func.sum(PaymentRecord.monto))
            .filter(
                PaymentRecord.fecha_pago
                >= datetime.combine(month_start, datetime.min.time())
            )
            .scalar()
            or 0
        )

        # Total de vehículos procesados hoy
        today_vehicles = Vehicle.query.filter(
            Vehicle.hora_entrada.between(today_start, today_end)
        ).count()

        # Vehículos pagados hoy
        today_paid = Vehicle.query.filter(
            Vehicle.hora_salida.between(today_start, today_end),
            Vehicle.estado.in_(["pagado", "salido"]),
        ).count()

        # Tiempo promedio de estancia
        avg_duration = (
            db.session.query(func.avg(Vehicle.tiempo_total))
            .filter(Vehicle.hora_salida.between(today_start, today_end))
            .scalar()
            or 0
        )

        return jsonify(
            {
                "success": True,
                "statistics": {
                    "active_vehicles": active_vehicles,
                    "today_income": today_income,
                    "month_income": month_income,
                    "today_vehicles": today_vehicles,
                    "today_paid": today_paid,
                    "avg_duration_minutes": int(avg_duration) if avg_duration else 0,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@require_admin
def get_logs():
    """Obtener logs del sistema"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 100, type=int)

        logs_query = SystemLog.query.order_by(SystemLog.fecha.desc())

        # Filtros
        accion = request.args.get("accion")
        if accion:
            logs_query = logs_query.filter_by(accion=accion)

        paginated = logs_query.paginate(page=page, per_page=per_page)

        logs_data = [
            {
                "id": l.id,
                "accion": l.accion,
                "detalles": l.detalles,
                "fecha": l.fecha.isoformat(),
                "usuario": l.usuario,
            }
            for l in paginated.items
        ]

        return jsonify(
            {
                "success": True,
                "total": paginated.total,
                "pages": paginated.pages,
                "current_page": page,
                "logs": logs_data,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@require_admin
def manage_vehicles():
    """Gestionar vehículos"""
    try:
        if request.method == "GET":
            # Listar vehículos con filtros
            estado = request.args.get("estado", "dentro")
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)

            query = Vehicle.query.filter_by(estado=estado).order_by(
                Vehicle.hora_entrada.desc()
            )
            paginated = query.paginate(page=page, per_page=per_page)

            vehicles_data = [v.to_dict() for v in paginated.items]

            return jsonify(
                {
                    "success": True,
                    "total": paginated.total,
                    "pages": paginated.pages,
                    "current_page": page,
                    "vehicles": vehicles_data,
                }
            )

        elif request.method == "POST":
            # Crear entrada manual
            data = request.get_json()

            if "placa" not in data:
                return jsonify({"success": False, "error": "Placa requerida"}), 400

            vehicle = Vehicle(
                placa=data["placa"].upper(),
                marca=data.get("marca"),
                color=data.get("color"),
                estado="dentro",
            )

            db.session.add(vehicle)
            db.session.commit()

            return jsonify({"success": True, "vehicle": vehicle.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
