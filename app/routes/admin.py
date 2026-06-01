"""
Rutas para panel de administración
"""

from flask import render_template, jsonify, request
from app import db
from app.models import Vehicle, PaymentRecord, SystemLog
from datetime import datetime
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

        # Fechas
        today = datetime.now().date()

        today_start = datetime.combine(today, datetime.min.time())

        today_end = datetime.combine(today, datetime.max.time())

        # Ingresos hoy
        today_income = (
            db.session.query(func.sum(PaymentRecord.monto))
            .filter(PaymentRecord.fecha_pago.between(today_start, today_end))
            .scalar()
            or 0
        )

        # Ingresos del mes
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

        # Vehículos procesados hoy
        today_vehicles = Vehicle.query.filter(
            Vehicle.hora_entrada.between(today_start, today_end)
        ).count()

        # Vehículos pagados hoy
        today_paid = Vehicle.query.filter(
            Vehicle.hora_salida.between(today_start, today_end),
            Vehicle.estado.in_(["pagado", "salido"]),
        ).count()

        # Tiempo promedio
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
    """Mostrar logs del sistema"""

    try:

        logs = SystemLog.query.order_by(SystemLog.created_at.desc()).all()

        return render_template("admin/logs.html", logs=logs)

    except Exception as e:

        return jsonify({"success": False, "error": str(e)}), 500


@require_admin
def manage_vehicles():
    """Gestionar vehículos"""

    try:

        # =========================
        # GET
        # =========================
        if request.method == "GET":

            estado = request.args.get("estado", "dentro")
            date_from = request.args.get("date_from")
            date_to = request.args.get("date_to")

            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)

            # Si se filtra por 'salido' es más lógico ordenar por hora_salida
            if estado == "salido":
                query = Vehicle.query.order_by(Vehicle.hora_salida.desc())
            else:
                query = Vehicle.query.order_by(Vehicle.hora_entrada.desc())

            if estado:
                query = query.filter_by(estado=estado)

            placa = request.args.get("placa")
            if placa:
                query = query.filter(Vehicle.placa.ilike(f"%{placa}%"))

            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                    query = query.filter(
                        Vehicle.hora_entrada
                        >= datetime.combine(date_from_obj, datetime.min.time())
                    )
                except ValueError:
                    pass

            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                    query = query.filter(
                        Vehicle.hora_entrada
                        <= datetime.combine(date_to_obj, datetime.max.time())
                    )
                except ValueError:
                    pass

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

        # =========================
        # POST
        # =========================
        elif request.method == "POST":

            data = request.get_json()

            if "placa" not in data:

                return jsonify({"success": False, "error": "Placa requerida"}), 400

            vehicle = Vehicle(
                placa=data["placa"].upper(),
                marca=data.get("marca"),
                color=data.get("color"),
                estado="dentro",
            )

            # Agregar ruta de imagen si se proporciona (CORRECCIÓN PARA IMAGEN EN PAGO)
            if data.get("ruta_imagen"):
                vehicle.ruta_imagen = data.get("ruta_imagen")

            db.session.add(vehicle)
            db.session.commit()

            # Crear log
            SystemLog.create_log(
                accion="ENTRADA_REGISTRADA",
                detalles=f"Vehículo {vehicle.placa} registrado manualmente",
                usuario="admin",
            )

            return jsonify({"success": True, "vehicle": vehicle.to_dict()}), 201

    except Exception as e:

        db.session.rollback()

        return jsonify({"success": False, "error": str(e)}), 500
