"""
Modelos de la base de datos con Programación Orientada a Objetos
"""

from app import db
from datetime import datetime
import re


# ============================================================================
# CLASE BASE
# ============================================================================


class BaseModel(db.Model):
    """Clase base para todos los modelos - DRY principle"""

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    def to_dict(self):
        """Convertir modelo a diccionario - Implementar en subclases"""
        raise NotImplementedError("Subclases deben implementar to_dict()")

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"


# ============================================================================
# MODELO VEHICLE - Con Validación y Métodos de Dominio
# ============================================================================


class Vehicle(BaseModel):
    """Modelo para vehículos estacionados con lógica de negocio encapsulada"""

    __tablename__ = "vehicles"

    placa = db.Column(db.String(20), unique=True, nullable=False, index=True)
    hora_entrada = db.Column(db.DateTime, default=datetime.now, nullable=False)
    hora_salida = db.Column(db.DateTime, nullable=True)
    tiempo_total = db.Column(db.Integer, nullable=True)  # en minutos
    valor_a_pagar = db.Column(db.Float, nullable=True)
    ruta_imagen = db.Column(db.String(255), nullable=True)
    estado = db.Column(
        db.String(20), default="dentro", nullable=False
    )  # dentro, pagado, salido
    marca = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(30), nullable=True)

    # Estados válidos
    ESTADOS_VALIDOS = {"dentro", "pagado", "salido"}
    FORMATO_PLACA = re.compile(r"^[A-Z]{3}-?\d{3}$")

    def __init__(self, placa, marca=None, color=None, **kwargs):
        """Constructor con validación de placa"""
        # Validar placa antes de crear
        if not self._validar_placa(placa):
            raise ValueError(
                f"Placa inválida: {placa}. Formato esperado: XXX-123 o XXX123"
            )

        self.placa = placa.upper()
        self.marca = marca
        self.color = color
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Vehicle {self.placa} [{self.estado}]>"

    # =========================================================================
    # VALIDACIONES
    # =========================================================================

    @staticmethod
    def _validar_placa(placa):
        """Validar formato de placa (XXX-1234)"""
        if not placa or not isinstance(placa, str):
            return False
        return bool(Vehicle.FORMATO_PLACA.match(placa.upper()))

    def _validar_estado(self, nuevo_estado):
        """Validar que el nuevo estado sea válido"""
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado inválido: {nuevo_estado}. Válidos: {self.ESTADOS_VALIDOS}"
            )

    # =========================================================================
    # PROPIEDADES CALCULADAS (dinamincas)
    # =========================================================================

    @property
    def tiempo_transcurrido_minutos(self):
        """Calcular tiempo transcurrido en minutos (tiempo real)"""
        fecha_fin = self.hora_salida or datetime.now()
        delta = fecha_fin - self.hora_entrada
        return int(delta.total_seconds() / 60)

    @property
    def tiempo_transcurrido_horas(self):
        """Calcular tiempo transcurrido en horas y minutos"""
        minutos = self.tiempo_transcurrido_minutos
        horas = minutos // 60
        mins = minutos % 60
        return {"horas": horas, "minutos": mins, "total_minutos": minutos}

    @property
    def puede_pagar(self):
        """¿Puede este vehículo realizar un pago?"""
        return self.estado == "dentro"

    @property
    def puede_salir(self):
        """¿Puede salir del parqueadero?"""
        return self.estado in {"pagado", "dentro"}

    @property
    def estado_display(self):
        """Representación legible del estado"""
        estados = {
            "dentro": "🚗 Dentro del Parqueadero",
            "pagado": "✅ Pagado - Listo para Salir",
            "salido": "🚪 Vehículo Salido",
        }
        return estados.get(self.estado, self.estado)

    # =========================================================================
    # MÉTODOS DE CLASE (métodos de búsqueda)
    # =========================================================================

    @classmethod
    def buscar_por_placa(cls, placa):
        """Buscar vehículo por placa (case-insensitive)"""
        if not placa:
            return None
        return cls.query.filter_by(placa=placa.upper()).first()

    @classmethod
    def obtener_activos(cls):
        """Obtener todos los vehículos dentro del parqueadero"""
        return cls.query.filter_by(estado="dentro").all()

    @classmethod
    def obtener_pagados(cls):
        """Obtener vehículos con pago realizado"""
        return cls.query.filter_by(estado="pagado").all()

    # =========================================================================
    # MÉTODOS DE INSTANCIA - Operaciones
    # =========================================================================

    def cambiar_estado(self, nuevo_estado):
        """Cambiar estado del vehículo con validación"""
        self._validar_estado(nuevo_estado)

        # Validaciones de transición
        if self.estado == "salido":
            raise ValueError("No se puede cambiar el estado de un vehículo ya salido")

        self.estado = nuevo_estado
        db.session.commit()
        return self

    def registrar_pago(self, monto, metodo="efectivo"):
        """Registrar pago y cambiar estado a 'pagado'"""
        if not self.puede_pagar:
            raise ValueError(f"Vehículo no puede pagar. Estado actual: {self.estado}")

        if monto <= 0:
            raise ValueError("El monto debe ser mayor a 0")

        self.valor_a_pagar = monto
        self.cambiar_estado("pagado")

        # Registrar en logs
        SystemLog.create_log(
            accion="PAGO_REGISTRADO",
            detalles=f"Vehículo {self.placa} pagó ${monto} ({metodo})",
            usuario="sistema",
        )

        return self

    def registrar_salida(self):
        """Registrar salida del vehículo"""
        if self.estado != "pagado":
            raise ValueError(
                f"Solo vehículos pagados pueden salir. Estado: {self.estado}"
            )

        self.hora_salida = datetime.now()
        self.tiempo_total = self.tiempo_transcurrido_minutos
        self.cambiar_estado("salido")

        SystemLog.create_log(
            accion="SALIDA_REGISTRADA",
            detalles=f"Vehículo {self.placa} salió del parqueadero",
            usuario="sistema",
        )

        return self

    def calcular_tarifa(self):
        """Calcular tarifa de estacionamiento (delega a servicio)"""
        from app.services.tariff import TariffCalculator

        if self.estado == "salido":
            # Si ya salió, usar la hora de salida guardada
            calculator = TariffCalculator()
            return calculator.calculate_tariff(self.hora_entrada, self.hora_salida)
        elif self.estado in {"dentro", "pagado"}:
            # Si está dentro o pagado, calcular hasta ahora
            calculator = TariffCalculator()
            return calculator.calculate_tariff(self.hora_entrada)
        else:
            return None

    def obtener_info_completa(self):
        """Obtener información completa del vehículo con tarifa"""
        return {
            "vehicle": self.to_dict(),
            "tariff": self.calcular_tarifa(),
            "puede_pagar": self.puede_pagar,
            "puede_salir": self.puede_salir,
        }

    # =========================================================================
    # SERIALIZACIÓN
    # =========================================================================

    def to_dict(self):
        """Convertir vehículo a diccionario"""
        return {
            "id": self.id,
            "placa": self.placa,
            "marca": self.marca,
            "color": self.color,
            "hora_entrada": self.hora_entrada.isoformat(),
            "hora_salida": self.hora_salida.isoformat() if self.hora_salida else None,
            "tiempo_transcurrido": self.tiempo_transcurrido_horas,
            "tiempo_total_minutos": self.tiempo_total,
            "valor_a_pagar": self.valor_a_pagar,
            "ruta_imagen": self.ruta_imagen,
            "estado": self.estado,
            "estado_display": self.estado_display,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================================
# MODELO PARKING SPACE
# ============================================================================


class ParkingSpace(BaseModel):
    """Modelo para gestionar espacios de estacionamiento"""

    __tablename__ = "parking_spaces"

    numero = db.Column(db.Integer, unique=True, nullable=False)
    estado = db.Column(
        db.String(20), default="disponible", nullable=False
    )  # disponible, ocupado
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True)

    ESTADOS_VALIDOS = {"disponible", "ocupado"}

    def __init__(self, numero, **kwargs):
        """Constructor con validación"""
        if numero <= 0:
            raise ValueError("Número de espacio debe ser positivo")
        self.numero = numero
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<ParkingSpace {self.numero} [{self.estado}]>"

    @property
    def esta_disponible(self):
        """¿Está disponible este espacio?"""
        return self.estado == "disponible"

    def ocupar(self, vehicle_id):
        """Ocupar espacio con un vehículo"""
        if not self.esta_disponible:
            raise ValueError(f"Espacio {self.numero} ya está ocupado")
        self.state = "ocupado"
        self.vehicle_id = vehicle_id
        db.session.commit()

    def liberar(self):
        """Liberar espacio"""
        self.estado = "disponible"
        self.vehicle_id = None
        db.session.commit()

    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "numero": self.numero,
            "estado": self.estado,
            "disponible": self.esta_disponible,
            "vehicle_id": self.vehicle_id,
        }


# ============================================================================
# MODELO PAYMENT RECORD
# ============================================================================


class PaymentRecord(BaseModel):
    """Modelo para registrar pagos con validación"""

    __tablename__ = "payment_records"

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.now, nullable=False)
    metodo_pago = db.Column(db.String(50), default="efectivo", nullable=False)
    estado = db.Column(db.String(20), default="completado", nullable=False)

    vehicle = db.relationship("Vehicle", backref=db.backref("payments", lazy=True))

    METODOS_VALIDOS = {"efectivo", "tarjeta", "transferencia", "qr"}
    ESTADOS_VALIDOS = {"completado", "pendiente", "cancelado"}

    def __init__(self, vehicle_id, monto, metodo_pago="efectivo", **kwargs):
        """Constructor con validación"""
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a 0")

        if metodo_pago not in self.METODOS_VALIDOS:
            raise ValueError(f"Método inválido. Válidos: {self.METODOS_VALIDOS}")

        self.vehicle_id = vehicle_id
        self.monto = monto
        self.metodo_pago = metodo_pago
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<PaymentRecord {self.id} ${self.monto}>"

    @property
    def monto_formateado(self):
        """Monto formateado con separador de miles"""
        return f"${self.monto:,.2f}".replace(",", ".")

    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "monto": self.monto,
            "monto_formateado": self.monto_formateado,
            "fecha_pago": self.fecha_pago.isoformat(),
            "metodo_pago": self.metodo_pago,
            "estado": self.estado,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# MODELO VEHICLE PHOTO
# ============================================================================


class VehiclePhoto(BaseModel):
    """Modelo para almacenar fotos de vehículos"""

    __tablename__ = "vehicle_photos"

    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)
    ruta_imagen = db.Column(db.String(255), nullable=False)
    tipo = db.Column(
        db.String(50), default="captura", nullable=False
    )  # entrada, placa_detectada, captura
    fecha_captura = db.Column(db.DateTime, default=datetime.now, nullable=False)

    vehicle = db.relationship("Vehicle", backref=db.backref("photos", lazy=True))
    TIPOS_VALIDOS = {"entrada", "placa_detectada", "captura"}

    def __init__(self, vehicle_id, ruta_imagen, tipo="captura", **kwargs):
        """Constructor con validación"""
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido. Válidos: {self.TIPOS_VALIDOS}")

        self.vehicle_id = vehicle_id
        self.ruta_imagen = ruta_imagen
        self.tipo = tipo
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<VehiclePhoto {self.id} [{self.tipo}]>"

    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "ruta_imagen": self.ruta_imagen,
            "tipo": self.tipo,
            "fecha_captura": self.fecha_captura.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# MODELO SYSTEM LOG - Con métodos de utilidad
# ============================================================================


class SystemLog(BaseModel):
    """Modelo para registrar eventos/logs del sistema"""

    __tablename__ = "system_logs"

    accion = db.Column(db.String(100), nullable=False)
    detalles = db.Column(db.Text, nullable=True)
    usuario = db.Column(db.String(50), default="sistema", nullable=False)

    ACCIONES_VALIDAS = {
        "ENTRADA_REGISTRADA",
        "SALIDA_REGISTRADA",
        "PAGO_REGISTRADO",
        "PLACA_DETECTADA",
        "ERROR_OCR",
        "LOGIN_ADMIN",
        "LOGOUT_ADMIN",
        "SESION_ADMIN",
        "INICIALIZACION",
    }

    def __init__(self, accion, detalles="", usuario="sistema", **kwargs):
        """Constructor con validación"""
        if accion not in self.ACCIONES_VALIDAS:
            raise ValueError(f"Acción inválida. Válidas: {self.ACCIONES_VALIDAS}")

        self.accion = accion
        self.detalles = detalles
        self.usuario = usuario
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<SystemLog {self.accion} by {self.usuario}>"

    @classmethod
    def create_log(cls, accion, detalles="", usuario="sistema"):
        """Crear y guardar un log en una línea"""
        try:
            log = cls(accion=accion, detalles=detalles, usuario=usuario)
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            print(f"Error creando log: {e}")
            return None

    @classmethod
    def obtener_ultimos(cls, cantidad=100):
        """Obtener últimos logs"""
        return cls.query.order_by(cls.created_at.desc()).limit(cantidad).all()

    @classmethod
    def obtener_por_accion(cls, accion, cantidad=50):
        """Obtener logs de una acción específica"""
        return (
            cls.query.filter_by(accion=accion)
            .order_by(cls.created_at.desc())
            .limit(cantidad)
            .all()
        )

    def to_dict(self):
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "accion": self.accion,
            "detalles": self.detalles,
            "usuario": self.usuario,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
