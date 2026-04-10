"""
Rutas para procesamiento de pagos
"""

from flask import request, jsonify
from app import db
from app.models import Vehicle, PaymentRecord, SystemLog, VehiclePhoto
from app.services.tariff import TariffCalculator
from datetime import datetime


def calculate_payment():
    """Calcular el valor a pagar para un vehículo"""
    try:
        data = request.get_json()

        if "placa" not in data:
            return jsonify({"success": False, "error": "Placa requerida"}), 400

        placa = data["placa"].upper()

        # Buscar vehículo
        vehicle = Vehicle.query.filter_by(placa=placa, estado="dentro").first()
        if not vehicle:
            return (
                jsonify(
                    {"success": False, "error": "Vehículo no encontrado o ya salió"}
                ),
                404,
            )

        # Calcular tarifa
        calculator = TariffCalculator()
        tariff_info = calculator.calculate_tariff(vehicle.hora_entrada)

        return jsonify(
            {
                "success": True,
                "vehicle": {
                    "id": vehicle.id,
                    "placa": vehicle.placa,
                    "entrada": vehicle.hora_entrada.isoformat(),
                    "imagen": vehicle.ruta_imagen,
                    "marca": vehicle.marca,
                    "color": vehicle.color,
                },
                "imagenes": [vehicle.ruta_imagen] if vehicle.ruta_imagen else [],
                "tariff": {
                    "duration": calculator.format_duration(
                        tariff_info["total_minutes"]
                    ),
                    "hours": tariff_info["hours"],
                    "minutes": tariff_info["remaining_minutes"],
                    "hours_to_charge": tariff_info["hours_to_charge"],
                    "amount": tariff_info["amount"],
                    "amount_formatted": calculator.format_currency(
                        tariff_info["amount"]
                    ),
                    "currency": "COP",
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def create_payment():
    """Registrar un pago usando método del modelo"""
    try:
        data = request.get_json()

        required_fields = ["vehicle_id", "monto", "metodo_pago"]
        if not all(field in data for field in required_fields):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Campos requeridos: vehicle_id, monto, metodo_pago",
                    }
                ),
                400,
            )

        vehicle = Vehicle.query.get(data["vehicle_id"])
        if not vehicle:
            return jsonify({"success": False, "error": "Vehículo no encontrado"}), 404

        try:
            # Usar método del modelo - valida automáticamente
            monto = float(data["monto"])
            metodo = data["metodo_pago"]

            vehicle.registrar_pago(monto, metodo)

            # Crear registro de pago en BD
            payment = PaymentRecord(
                vehicle_id=vehicle.id,
                monto=monto,
                metodo_pago=metodo,
                estado="completado",
            )
            db.session.add(payment)
            db.session.commit()

            # Calcular tarifa para el recibo
            tariff_info = vehicle.calcular_tarifa()

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Pago completado exitosamente",
                        "payment_id": payment.id,
                        "vehicle": vehicle.to_dict(),
                        "receipt": {
                            "placa": vehicle.placa,
                            "entrada": vehicle.hora_entrada.isoformat(),
                            "duracion": vehicle.tiempo_transcurrido_horas,
                            "monto": monto,
                            "metodo": metodo,
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                ),
                201,
            )

        except ValueError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


def payment_history():
    """Obtener historial de pagos"""
    try:
        # Obtener parámetros de paginación
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)

        # Consultar pagos
        payments_query = PaymentRecord.query.order_by(PaymentRecord.fecha_pago.desc())

        # Aplicar filtros si existen
        vehicle_id = request.args.get("vehicle_id", type=int)
        if vehicle_id:
            payments_query = payments_query.filter_by(vehicle_id=vehicle_id)

        # Paginar resultados
        paginated = payments_query.paginate(page=page, per_page=per_page)

        payments_data = [
            {
                "id": p.id,
                "vehicle": {"id": p.vehicle.id, "placa": p.vehicle.placa},
                "monto": p.monto,
                "fecha_pago": p.fecha_pago.isoformat(),
                "metodo_pago": p.metodo_pago,
                "estado": p.estado,
            }
            for p in paginated.items
        ]

        return jsonify(
            {
                "success": True,
                "total": paginated.total,
                "pages": paginated.pages,
                "current_page": page,
                "payments": payments_data,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def get_vehicle_photos():
    """Obtener todas las fotos de un vehículo por placa"""
    try:
        placa = request.args.get("placa", "").upper()

        if not placa:
            return jsonify({"success": False, "error": "Placa requerida"}), 400

        # Buscar vehículo
        vehicle = Vehicle.query.filter_by(placa=placa).first()
        if not vehicle:
            return jsonify({"success": False, "error": "Vehículo no encontrado"}), 404

        # Obtener todas las fotos ordenadas por fecha
        photos = (
            VehiclePhoto.query.filter_by(vehicle_id=vehicle.id)
            .order_by(VehiclePhoto.fecha_captura.desc())
            .all()
        )

        photos_data = [
            {
                "id": photo.id,
                "ruta_imagen": photo.ruta_imagen,
                "tipo": photo.tipo,
                "fecha_captura": photo.fecha_captura.isoformat(),
            }
            for photo in photos
        ]

        return jsonify(
            {
                "success": True,
                "vehicle": {
                    "id": vehicle.id,
                    "placa": vehicle.placa,
                    "marca": vehicle.marca,
                    "color": vehicle.color,
                    "entrada": vehicle.hora_entrada.isoformat(),
                    "salida": (
                        vehicle.hora_salida.isoformat() if vehicle.hora_salida else None
                    ),
                    "estado": vehicle.estado,
                },
                "total_photos": len(photos),
                "photos": photos_data,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
