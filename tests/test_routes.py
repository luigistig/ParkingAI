import unittest
from app import create_app, db
from app.models import Vehicle


class BaseRouteTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


class VehicleRoutesTest(BaseRouteTest):
    def test_vehicle_checkin_and_search(self):
        response = self.client.post(
            "/api/vehicles/checkin", json={"placa": "ABC-123", "marca": "Toyota"}
        )
        self.assertEqual(response.status_code, 201)

        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("vehicle_id", data)
        self.assertEqual(data["vehicle"]["placa"], "ABC-123")

        search_response = self.client.get("/api/vehicles/search/ABC-123")
        self.assertEqual(search_response.status_code, 200)
        search_data = search_response.get_json()
        self.assertTrue(search_data["success"])
        self.assertEqual(search_data["vehicle"]["placa"], "ABC-123")

    def test_vehicle_checkin_invalid_plate_returns_400(self):
        response = self.client.post("/api/vehicles/checkin", json={"placa": "BAD"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_vehicle_checkout_without_payment_returns_400(self):
        response = self.client.post(
            "/api/vehicles/checkin", json={"placa": "XYZ-789"}
        )
        self.assertEqual(response.status_code, 201)
        vehicle_id = response.get_json()["vehicle_id"]

        checkout_response = self.client.post(f"/api/vehicles/checkout/{vehicle_id}")
        self.assertEqual(checkout_response.status_code, 400)
        checkout_data = checkout_response.get_json()
        self.assertFalse(checkout_data["success"])
        self.assertIn("Solo vehículos pagados pueden salir", checkout_data["error"])

    def test_list_vehicles_endpoint(self):
        self.client.post("/api/vehicles/checkin", json={"placa": "MNO-123"})

        response = self.client.get("/api/vehicles")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total"], 1)


class AuthRoutesTest(BaseRouteTest):
    def test_admin_login_success(self):
        response = self.client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "admin123", "remember": False},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["admin_name"], "Administrador")

    def test_admin_login_failure(self):
        response = self.client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_check_session_returns_false_if_not_logged_in(self):
        response = self.client.get("/api/admin/check-session")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["is_admin"])
        self.assertIsNone(data["admin_name"])


if __name__ == "__main__":
    unittest.main()
