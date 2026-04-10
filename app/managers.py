"""
Managers/Repositories para operaciones comunes
Implementa el patrón Repository para separar lógica de acceso a datos
"""

from app import db
from app.models import Vehicle, PaymentRecord, SystemLog, VehiclePhoto
from app.services.tariff import TariffCalculator
from datetime import datetime, timedelta
from sqlalchemy import func


class VehicleManager:
    """Gestor de operaciones de vehículos"""

    @staticmethod
    def registrar_entrada(placa, marca=None, color=None, ruta_imagen=None):
        """
        Registrar entrada de un vehículo

        Args:
            placa: Placa del vehículo (validada en constructor)
            marca: Marca/tipo de vehículo
            color: Color del vehículo
            ruta_imagen: Ruta a la imagen capturada

        Returns:
            Tupla (success, vehicle, error_message)
        """
        try:
            # Verificar si ya existe
            existing = Vehicle.buscar_por_placa(placa)
            if existing and existing.estado == "dentro":
                return False, None, "Vehículo ya está dentro del parqueadero"

            # Crear vehículo - Constructor valida placa
            vehicle = Vehicle(placa=placa, marca=marca, color=color)
            vehicle.ruta_imagen = ruta_imagen

            db.session.add(vehicle)
            db.session.commit()

            # Registrar evento
            SystemLog.create_log(
                accion="ENTRADA_REGISTRADA", detalles=f"Entrada registrada para {placa}"
            )

            return True, vehicle, None

        except ValueError as e:
            return False, None, str(e)
        except Exception as e:
            db.session.rollback()
            return False, None, str(e)

    @staticmethod
    def procesar_pago(vehicle_id, monto, metodo_pago="efectivo"):
        """
        Procesar pago de un vehículo

        Args:
            vehicle_id: ID del vehículo
            monto: Monto a pagar
            metodo_pago: Método de pago

        Returns:
            Tupla (success, payment_record, error_message)
        """
        try:
            vehicle = Vehicle.query.get(vehicle_id)
            if not vehicle:
                return False, None, "Vehículo no encontrado"

            # Registrar pago - Valida automáticamente
            vehicle.registrar_pago(monto, metodo_pago)

            # Crear registro de pago
            payment = PaymentRecord(
                vehicle_id=vehicle_id,
                monto=monto,
                metodo_pago=metodo_pago,
                estado="completado",
            )
            db.session.add(payment)
            db.session.commit()

            return True, payment, None

        except ValueError as e:
            db.session.rollback()
            return False, None, str(e)
        except Exception as e:
            db.session.rollback()
            return False, None, str(e)

    @staticmethod
    def obtener_estadisticas():
        """Obtener estadísticas del parqueadero"""
        try:
            activos = Vehicle.query.filter_by(estado="dentro").count()
            pagados = Vehicle.query.filter_by(estado="pagado").count()
            salidos = Vehicle.query.filter_by(estado="salido").count()

            # Ingresos hoy
            hoy = datetime.now().date()
            hoy_start = datetime.combine(hoy, datetime.min.time())
            hoy_end = datetime.combine(hoy, datetime.max.time())

            ingresos_hoy = (
                db.session.query(func.sum(PaymentRecord.monto))
                .filter(PaymentRecord.created_at.between(hoy_start, hoy_end))
                .scalar()
                or 0
            )

            # Promedio de estancia hoy
            tiempo_promedio = (
                db.session.query(func.avg(Vehicle.tiempo_total))
                .filter(
                    Vehicle.updated_at.between(hoy_start, hoy_end),
                    Vehicle.estado == "salido",
                )
                .scalar()
                or 0
            )

            return {
                "vehículos_dentro": activos,
                "vehículos_pagados": pagados,
                "vehículos_salidos_hoy": salidos,
                "ingresos_hoy": ingresos_hoy,
                "tiempo_promedio_minutos": int(tiempo_promedio),
                "tiempo_promedio_horas": round(tiempo_promedio / 60, 2),
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def obtener_reporte_diario():
        """Obtener reporte completo del día"""
        try:
            hoy = datetime.now().date()
            hoy_start = datetime.combine(hoy, datetime.min.time())
            hoy_end = datetime.combine(hoy, datetime.max.time())

            vehiculos_hoy = Vehicle.query.filter(
                Vehicle.hora_entrada.between(hoy_start, hoy_end)
            ).all()

            pagos_hoy = PaymentRecord.query.filter(
                PaymentRecord.created_at.between(hoy_start, hoy_end)
            ).all()

            return {
                "fecha": hoy.isoformat(),
                "total_vehiculos": len(vehiculos_hoy),
                "total_pagos": len(pagos_hoy),
                "ingresos_totales": sum(p.monto for p in pagos_hoy),
                "vehiculos": [v.to_dict() for v in vehiculos_hoy],
                "pagos": [p.to_dict() for p in pagos_hoy],
            }

        except Exception as e:
            return {"error": str(e)}


class SystemManager:
    """Gestor de operaciones de sistema"""

    @staticmethod
    def registrar_evento(accion, detalles="", usuario="sistema"):
        """Registrar evento en logs"""
        try:
            return SystemLog.create_log(accion, detalles, usuario)
        except Exception as e:
            print(f"Error registrando evento: {e}")
            return None

    @staticmethod
    def obtener_logs(cantidad=100, accion=None):
        """Obtener logs con filtro opcional"""
        try:
            if accion:
                return SystemLog.obtener_por_accion(accion, cantidad)
            else:
                return SystemLog.obtener_ultimos(cantidad)
        except Exception as e:
            print(f"Error obteniendo logs: {e}")
            return []

    @staticmethod
    def obtener_estadisticas_acceso():
        """Obtener estadísticas de acceso al sistema"""
        try:
            hoy = datetime.now().date()
            hoy_start = datetime.combine(hoy, datetime.min.time())
            hoy_end = datetime.combine(hoy, datetime.max.time())

            logins = (
                SystemLog.query.filter_by(accion="LOGIN_ADMIN")
                .filter(SystemLog.created_at.between(hoy_start, hoy_end))
                .count()
            )

            acciones_admin = (
                SystemLog.query.filter(SystemLog.usuario != "sistema")
                .filter(SystemLog.created_at.between(hoy_start, hoy_end))
                .count()
            )

            return {
                "login_intents": logins,
                "admin_actions": acciones_admin,
                "fecha": hoy.isoformat(),
            }

        except Exception as e:
            return {"error": str(e)}


class TariffManager:
    """Gestor de cálculos de tarifa"""

    def __init__(self, tariff_per_hour=2000, min_charge=500):
        """Inicializar con parámetros de tarifa"""
        self.calculator = TariffCalculator(tariff_per_hour, min_charge)

    def calcular_para_vehiculo(self, vehicle):
        """Calcular tarifa para un vehículo específico"""
        return self.calculator.calculate_tariff(vehicle.hora_entrada)

    def obtener_tarifas_configuradas(self):
        """Obtener tarifas actuales"""
        return {
            "tarifa_por_hora": self.calculator.tariff_per_hour,
            "cargo_minimo": self.calculator.min_charge,
            "moneda": "COP",
        }

    @staticmethod
    def comparar_tarifas(entrada, salidas_multiples):
        """
        Comparar tarifas para diferentes horarios de salida
        Útil para análisis de qué-pasa-si
        """
        calculator = TariffCalculator()
        resultados = []

        for salida in salidas_multiples:
            tariff = calculator.calculate_tariff(entrada, salida)
            resultados.append({"salida": salida.isoformat(), "tarifa": tariff})

        return resultados
