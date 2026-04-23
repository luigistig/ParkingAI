import unittest
from datetime import datetime, timedelta
from app.services.tariff import TariffCalculator, calculate_parking_fee, format_duration


class TariffCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.calculator = TariffCalculator(tariff_per_hour=2000, min_charge=500)

    def test_calculate_duration(self):
        entrada = datetime.now() - timedelta(hours=1, minutes=30)
        total_minutes, hours, remaining_minutes = self.calculator.calculate_duration(
            entrada, datetime.now()
        )

        self.assertEqual(total_minutes, 90)
        self.assertEqual(hours, 1)
        self.assertEqual(remaining_minutes, 30)

    def test_calculate_tariff_uses_ceiling(self):
        entrada = datetime.now() - timedelta(hours=1, minutes=10)
        result = self.calculator.calculate_tariff(entrada, datetime.now(), rounding_method="ceil")

        self.assertEqual(result["hours_to_charge"], 2)
        self.assertEqual(result["amount"], 4000)

    def test_calculate_tariff_applies_minimum_charge(self):
        calculator = TariffCalculator(tariff_per_hour=100, min_charge=500)
        entrada = datetime.now() - timedelta(minutes=10)

        result = calculator.calculate_tariff(entrada, datetime.now(), rounding_method="ceil")

        self.assertEqual(result["hours_to_charge"], 1)
        self.assertEqual(result["amount"], 500)

    def test_format_duration(self):
        self.assertEqual(self.calculator.format_duration(45), "45 minutos")
        self.assertEqual(self.calculator.format_duration(60), "1 hora")
        self.assertEqual(self.calculator.format_duration(125), "2 horas y 5 minutos")

    def test_format_currency(self):
        self.assertEqual(self.calculator.format_currency(2000), "$2.000")
        self.assertEqual(self.calculator.format_currency(15000), "$15.000")

    def test_helper_functions(self):
        entrada = datetime.now() - timedelta(hours=2)
        result = calculate_parking_fee(entrada, datetime.now())

        self.assertIn("amount", result)
        self.assertEqual(format_duration(125), "2 horas y 5 minutos")


if __name__ == "__main__":
    unittest.main()
