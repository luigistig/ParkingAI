"""
Script de inicialización y prueba de la base de datos
"""

from app import create_app, db
from app.models import Vehicle, PaymentRecord, ParkingSpace, SystemLog, VehiclePhoto
from datetime import datetime, timedelta


def init_database():
    """Inicializar base de datos con datos de prueba"""
    app = create_app("development")

    with app.app_context():
        # Crear tablas
        db.create_all()
        print("✓ Tablas de base de datos creadas")

        # Limpiar datos existentes
        VehiclePhoto.query.delete()
        Vehicle.query.delete()
        PaymentRecord.query.delete()
        ParkingSpace.query.delete()
        SystemLog.query.delete()
        db.session.commit()
        print("✓ Base de datos limpiada")

        # Crear datos de prueba
        test_vehicles = [
            Vehicle(
                placa="ABC-1234",
                marca="Toyota",
                color="Negro",
                hora_entrada=datetime.now() - timedelta(hours=2),
                estado="dentro",
                ruta_imagen=None,
            ),
            Vehicle(
                placa="XYZ-5678",
                marca="Honda",
                color="Blanco",
                hora_entrada=datetime.now() - timedelta(hours=1),
                estado="dentro",
                ruta_imagen=None,
            ),
            Vehicle(
                placa="DEF-9012",
                marca="Chevrolet",
                color="Rojo",
                hora_entrada=datetime.now() - timedelta(days=1),
                hora_salida=datetime.now() - timedelta(days=1, hours=2),
                tiempo_total=120,
                valor_a_pagar=4000,
                estado="pagado",
                ruta_imagen=None,
            ),
        ]

        for vehicle in test_vehicles:
            db.session.add(vehicle)

        db.session.commit()
        print(f"✓ {len(test_vehicles)} vehículos de prueba creados")

        # Crear espacios de estacionamiento
        for i in range(1, 51):
            space = ParkingSpace(numero=i, estado="disponible")
            db.session.add(space)

        db.session.commit()
        print("✓ 50 espacios de estacionamiento creados")

        # Crear log de inicialización
        log = SystemLog(
            accion="INICIALIZACION",
            detalles="Base de datos inicializada con datos de prueba",
            usuario="sistema",
        )
        db.session.add(log)
        db.session.commit()
        print("✓ Log de inicialización registrado")

        print("\n✓ Base de datos inicializada correctamente!")
        print(f"  - URL: http://localhost:5000")
        print(f"  - Vehículos de prueba: {len(test_vehicles)}")
        print(f"  - Espacios disponibles: 50")


if __name__ == "__main__":
    init_database()
