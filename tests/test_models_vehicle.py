import unittest
from app.models import Vehicle, db
from flask import Flask


class VehicleModelTest(unittest.TestCase):
    def setUp(self):
        # Crear app mínima para pruebas
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_invalid_plate_raises_value_error(self):
        with self.assertRaises(ValueError):
            Vehicle(placa="INVALID")

    def test_cambiar_estado_requires_valid_state(self):
        vehicle = Vehicle(placa="ABC-123")
        db.session.add(vehicle)
        db.session.commit()

        with self.assertRaises(ValueError):
            vehicle.cambiar_estado("estado_invalido")

    def test_registrar_pago_and_salida(self):
        vehicle = Vehicle(placa="DEF-456")
        db.session.add(vehicle)
        db.session.commit()

        self.assertTrue(vehicle.puede_pagar)

        vehicle.registrar_pago(2000)
        self.assertEqual(vehicle.estado, "pagado")
        self.assertEqual(vehicle.valor_a_pagar, 2000)

        vehicle.registrar_salida()
        self.assertEqual(vehicle.estado, "salido")
        self.assertIsNotNone(vehicle.hora_salida)
        self.assertIsNotNone(vehicle.tiempo_total)

    def test_registrar_salida_without_payment_raises(self):
        vehicle = Vehicle(placa="GHI-789")
        db.session.add(vehicle)
        db.session.commit()

        with self.assertRaises(ValueError):
            vehicle.registrar_salida()

    def test_buscar_por_placa_returns_vehicle(self):
        vehicle = Vehicle(placa="JKL-123")
        db.session.add(vehicle)
        db.session.commit()

        resultado = Vehicle.buscar_por_placa("jkl-123")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.placa, "JKL-123")


if __name__ == "__main__":
    unittest.main()
