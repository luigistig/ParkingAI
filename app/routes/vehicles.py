"""
Rutas para gestión de vehículos
"""

from flask import request, jsonify, render_template, current_app
from app import db
from app.models import Vehicle, SystemLog
from app.services.tariff import TariffCalculator
from datetime import datetime
import os
from sqlalchemy.exc import IntegrityError


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

        # Verificar si ya existe un registro con esa placa (cualquier estado)
        existing_any = Vehicle.buscar_por_placa(placa)

        # Si ya está dentro, informar al usuario
        if existing_any and existing_any.estado == "dentro":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Vehículo ya está dentro del parqueadero",
                    }
                ),
                400,
            )

        # Si existe en otro estado, reutilizar el registro (evitar duplicados por UNIQUE)
        try:
            if existing_any:
                # Reiniciar campos para nueva entrada
                existing_any.hora_entrada = datetime.now()
                existing_any.hora_salida = None
                existing_any.tiempo_total = None
                existing_any.valor_a_pagar = None
                existing_any.estado = "dentro"
                # Actualizar datos opcionales si vienen
                if data.get("marca"):
                    existing_any.marca = data.get("marca")
                if data.get("color"):
                    existing_any.color = data.get("color")
                if data.get("ruta_imagen"):
                    existing_any.ruta_imagen = data.get("ruta_imagen")

                db.session.add(existing_any)
                db.session.commit()

                SystemLog.create_log(
                    accion="ENTRADA_REACTIVADA",
                    detalles=f"Vehículo {placa} reingresó al parqueadero",
                )

                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Vehículo registrado (registro existente actualizado)",
                            "vehicle_id": existing_any.id,
                            "vehicle": existing_any.to_dict(),
                        }
                    ),
                    200,
                )

            # Crear nuevo registro - Constructor valida la placa
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
        except IntegrityError as ie:
            # Error de integridad: no exponer detalles técnicos al cliente
            current_app.logger.error(f"DB IntegrityError on checkin: {ie}")
            db.session.rollback()
            return (
                jsonify(
                    {"success": False, "error": "No se pudo registrar el vehículo"}
                ),
                400,
            )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error inesperado en vehicle_checkin")
        return (
            jsonify(
                {"success": False, "error": "Ocurrió un error al procesar la solicitud"}
            ),
            500,
        )


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
