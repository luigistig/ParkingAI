"""
Rutas para gestión de vehículos
"""

from flask import request, jsonify, render_template
from app import db
from app.models import Vehicle, SystemLog
from app.services.tariff import TariffCalculator
from datetime import datetime
import os


def list_vehicles():
    """Listar todos los vehículos activos"""
    try:
        vehicles = Vehicle.obtener_activos()
        return jsonify(
            {
                "success": True,
                "total": len(vehicles),
                "vehicles": [v.to_dict() for v in vehicles],
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def get_vehicle(vehicle_id):
    """Obtener información completa de un vehículo específico"""
    try:
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({"success": False, "error": "Vehículo no encontrado"}), 404

        return jsonify({"success": True, **vehicle.obtener_info_completa()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def search_vehicle(placa):
    """Buscar vehículo por placa con información completa"""
    try:
        vehicle = Vehicle.buscar_por_placa(placa)
        if not vehicle:
            return jsonify({"success": False, "error": "Vehículo no encontrado"}), 404

        return jsonify({"success": True, **vehicle.obtener_info_completa()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def vehicle_checkin():
    """Registrar entrada de vehículo"""
    try:
        data = request.get_json()

        if not data or "placa" not in data:
            return jsonify({"success": False, "error": "Placa requerida"}), 400

        placa = data["placa"].upper()

        # Verificar si el vehículo ya está dentro
        existing = Vehicle.query.filter_by(placa=placa, estado="dentro").first()
        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Vehículo ya está dentro del parqueadero",
                    }
                ),
                400,
            )

        # Crear nuevo registro - Constructor valida la placa
        try:
            vehicle = Vehicle(
                placa=placa, marca=data.get("marca"), color=data.get("color")
            )
            vehicle.ruta_imagen = data.get("ruta_imagen")

            db.session.add(vehicle)
            db.session.commit()

            # Registrar en logs
            SystemLog.create_log(
                accion="ENTRADA_REGISTRADA",
                detalles=f"Vehículo {placa} ingresó al parqueadero",
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Vehículo registrado exitosamente",
                        "vehicle_id": vehicle.id,
                        "vehicle": vehicle.to_dict(),
                    }
                ),
                201,
            )

        except ValueError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


def vehicle_checkout(vehicle_id):
    """Registrar salida de vehículo"""
    try:
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({"success": False, "error": "Vehículo no encontrado"}), 404

        if vehicle.estado != "dentro":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Vehículo no está dentro del parqueadero",
                    }
                ),
                400,
            )

        try:
            # Usar método de instancia para registrar salida
            vehicle.registrar_salida()

            return jsonify(
                {
                    "success": True,
                    "message": "Salida registrada exitosamente",
                    "vehicle": vehicle.to_dict(),
                }
            )

        except ValueError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
