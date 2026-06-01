"""
Servicio de cálculo de tarifas de estacionamiento
"""

from datetime import datetime
import math


class TariffCalculator:
    """Clase para calcular la tarifa de estacionamiento"""

    def __init__(self, tariff_per_hour=2000, min_charge=500):
        """
        Inicializar calculadora de tarifas

        Args:
            tariff_per_hour: valor por hora en pesos
            min_charge: cargo mínimo
        """
        self.tariff_per_hour = tariff_per_hour
        self.min_charge = min_charge

    def calculate_duration(self, entrada, salida=None):
        """
        Calcular duración del estacionamiento en minutos

        Args:
            entrada: datetime de entrada
            salida: datetime de salida (default: ahora)

        Returns:
            tupla (minutos, horas, minutos_restantes)
        """
        if salida is None:
            salida = datetime.now()

        # Calcular diferencia
        delta = salida - entrada
        total_minutes = int(delta.total_seconds() / 60)

        # Convertir a horas y minutos
        hours = total_minutes // 60
        remaining_minutes = total_minutes % 60

        return total_minutes, hours, remaining_minutes

    def calculate_tariff(self, entrada, salida=None, rounding_method="ceil"):
        """
        Calcular el valor a pagar

        Args:
            entrada: datetime de entrada
            salida: datetime de salida (default: ahora)
            rounding_method: 'ceil' para redondear al alza, 'round' para redondeo normal

        Returns:
            diccionario con detalles del cálculo
        """
        total_minutes, hours, remaining_minutes = self.calculate_duration(
            entrada, salida
        )

        # Calcular valor
        if total_minutes <= 60:
            # Hasta 1 hora se cobra por bloques de 15 minutos usando cargo mínimo.
            # El primer bloque es el valor mínimo; luego cada 15 minutos completos adicionales
            # aumentan el cargo mínimo una vez.
            if total_minutes <= 15:
                blocks_to_charge = 1
            else:
                extra_minutes = total_minutes - 15
                blocks_to_charge = 1 + (extra_minutes // 15)

            amount = blocks_to_charge * self.min_charge
            hours_to_charge = blocks_to_charge
        else:
            # Después de 1 hora, se cobra por horas completas.
            hours_to_charge = math.ceil(total_minutes / 60)
            amount = hours_to_charge * self.tariff_per_hour

        return {
            "total_minutes": total_minutes,
            "hours": hours,
            "remaining_minutes": remaining_minutes,
            "hours_to_charge": hours_to_charge,
            "tariff_per_hour": self.tariff_per_hour,
            "amount": amount,
            "currency": "COP",  # Pesos Colombianos
        }

    def format_duration(self, total_minutes):
        """
        Formatear duración en formato legible

        Args:
            total_minutes: minutos totales

        Returns:
            string con formato "X horas y Y minutos"
        """
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours == 0:
            return f"{minutes} minutos"
        elif minutes == 0:
            return f"{hours} hora{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hora{'s' if hours != 1 else ''} y {minutes} minuto{'s' if minutes != 1 else ''}"

    def format_currency(self, amount):
        """
        Formatear cantidad de dinero

        Args:
            amount: cantidad en pesos

        Returns:
            string formateado "$ 2.000"
        """
        return f"${amount:,.0f}".replace(",", ".")

    def get_price_estimate(self, hours):
        """
        Obtener estimado de precio para cierta cantidad de horas

        Args:
            hours: número de horas

        Returns:
            valor estimado
        """
        amount = hours * self.tariff_per_hour
        return max(amount, self.min_charge)


class PricingPlans:
    """Diferentes planes de tarificación"""

    STANDARD = {
        "name": "Tarifa Estándar",
        "description": "Tarifa por hora",
        "tariff_per_hour": 2000,
        "min_charge": 500,
    }

    DAILY_PASS = {
        "name": "Pase Diario",
        "description": "Uso ilimitado por 24 horas",
        "price": 20000,
        "duration_hours": 24,
    }

    MONTHLY_PASS = {
        "name": "Pase Mensual",
        "description": "Acceso ilimitado durante un mes",
        "price": 150000,
        "duration_days": 30,
    }

    VIP = {
        "name": "Tarifa VIP",
        "description": "Reducción de 20% en tarifa",
        "tariff_per_hour": 1600,
        "min_charge": 400,
    }


def calculate_parking_fee(entrada, salida=None):
    """
    Función auxiliar para calcular tarifa

    Args:
        entrada: datetime de entrada
        salida: datetime de salida

    Returns:
        diccionario con información de tarifa
    """
    calculator = TariffCalculator()
    return calculator.calculate_tariff(entrada, salida)


def format_duration(total_minutes):
    """
    Función auxiliar para formatear duración

    Args:
        total_minutes: minutos totales

    Returns:
        string formateado
    """
    calculator = TariffCalculator()
    return calculator.format_duration(total_minutes)
