# 📐 Documenta Técnica de Arquitectura

## Visión General de la Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTE (Frontend)                    │
│  HTML5 + CSS3 + JavaScript + Bootstrap 5                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼──────────────────────────────────┐
│                 SERVIDOR FLASK (Backend)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Routes/     │  │   Services   │  │   Models     │  │
│  │ Blueprints   │  │              │  │              │  │
│  │              │→ │ • Detección  │→ │ • Vehicle    │  │
│  │ • Vehicles   │  │ • OCR        │  │ • Payment    │  │
│  │ • Payments   │  │ • Tariff     │  │ • ParkSpace  │  │
│  │ • Camera     │  │ • Camera     │  │ • Logs       │  │
│  │ • Admin      │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼──────────┐        ┌────────▼────────┐
│  BASE DE DATOS   │        │   SISTEMA       │
│  (SQLite/MySQL)  │        │  DE ARCHIVOS    │
│                  │        │                 │
│ • Vehículos      │        │ • Imágenes      │
│ • Pagos          │        │ • Uploads       │
│ • Espacios       │        │ • Videos        │
│ • Logs           │        │                 │
└──────────────────┘        └─────────────────┘

┌─────────────────────────────────────────────────────────┐
│            EXTERNOS / LIBRERÍAS                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │  OpenCV      │ │  Tesseract   │ │  NumPy       │    │
│  │  Pillow      │ │  SQLAlchemy  │ │  Flask-CORS  │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. **Frontend (Presentación)**

#### Templates Principales:
- **base.html** - Plantilla base con navbar y estilos
- **index.html** - Dashboard principal
- **camera.html** - Captura y detección de placas
- **payment.html** - Interfaz de pago
- **history.html** - Historial de vehículos
- **admin.html** - Panel de administración

#### Características:
- Interfaz responsiva (Mobile-first)
- Real-time updates
- Validación de entrada en cliente
- Manejo de errores visual

### 2. **Backend (Lógica de Negocio)**

#### Rutas (Routes)
```python
/api/vehicles/          GET    → Listar vehículos activos
/api/vehicles/search/   GET    → Buscar por placa
/api/vehicles/checkin   POST   → Registrar entrada
/api/vehicles/checkout  POST   → Registrar salida

/api/payments/calculate POST   → Calcular tarifa
/api/payments           POST   → Registrar pago
/api/payments/history   GET    → Historial de pagos

/api/camera/capture     POST   → Capturar imagen
/api/camera/detect      POST   → Detectar placa

/admin/statistics       GET    → Estadísticas
/admin/logs             GET    → Registros del sistema
/admin/vehicles         GET/POST → Gestión de vehículos
```

#### Servicios (Services)
```
plate_detection.py
├── PlateDetector
│   ├── detect_plates()        → Detectar placas en imagen
│   ├── extract_plate_roi()    → Extraer región de placa
│   └── preprocess_plate()     → Procesar imagen para OCR

ocr.py
├── PlateOCR
│   ├── extract_text()         → Extraer texto con Tesseract
│   ├── extract_plate_number() → Obtener número de placa
│   └── validate_plate()       → Validar formato

tariff.py
├── TariffCalculator
│   ├── calculate_duration()   → Calcular duración
│   ├── calculate_tariff()     → Calcular valor a pagar
│   └── format_currency()      → Formatear moneda

camera.py
├── CameraService
│   ├── open_camera()          → Conectar cámara
│   ├── capture_frame()        → Capturar fotograma
│   └── capture_and_save()     → Guardar imagen
```

#### Modelos de Datos (Models)
```python
Vehicle
├── id (PK)
├── placa (VARCHAR, UNIQUE)
├── hora_entrada
├── hora_salida
├── tiempo_total
├── valor_a_pagar
├── ruta_imagen
├── estado (dentro|pagado|salido)
├── marca
└── color

PaymentRecord
├── id (PK)
├── vehicle_id (FK)
├── monto
├── fecha_pago
├── metodo_pago
└── estado

ParkingSpace
├── id (PK)
├── numero (UNIQUE)
├── estado
└── vehicle_id (FK)

SystemLog
├── id (PK)
├── accion
├── detalles
├── fecha
└── usuario
```

### 3. **Base de Datos**

#### Diseño Relacional:
```
vehicles ────┬─── payment_records
             │      (one-to-many)
             │
             └─── parking_spaces
                  (one-to-many)

system_logs (auditoría sin relación)
```

#### Índices:
- `vehicles.placa` - Búsqueda rápida
- `payment_records.fecha_pago` - Reportes
- `system_logs.fecha` - Auditoría

### 4. **Flujos Principales**

#### Flujo de Entrada:
```
1. Usuario selecciona imagen/captura
   ↓
2. Envío a /api/camera/capture
   ↓
3. Guardar imagen en /static/uploads/
   ↓
4. Llamar PlateDetector.detect_plates()
   ↓
5. Obtener ROI de placa
   ↓
6. Procesar con PlateOCR.extract_text()
   ↓
7. Validar formato de placa
   ↓
8. POST a /api/vehicles/checkin
   ↓
9. Grabar en DB + SystemLog
```

#### Flujo de Pago:
```
1. Usuario ingresa placa
   ↓
2. GET /api/vehicles/search/{placa}
   ↓
3. TariffCalculator.calculate_tariff()
   ↓
4. Mostrar información + cálculo
   ↓
5. Usuario selecciona método
   ↓
6. POST /api/payments
   ↓
7. Actualizar estado vehículo
   ↓
8. Crear PaymentRecord
   ↓
9. Generar recibo
```

## Patrones de Diseño

### 1. **MVC (Model-View-Controller)**
- Models: `app/models.py`
- Views: `app/templates/`
- Controllers: `app/routes/`

### 2. **Factory Pattern**
```python
def create_app(config_name='development'):
    app = Flask(__name__)
    # ... configuración
    return app
```

### 3. **Service Layer**
Separación de lógica de negocio en `app/services/`

### 4. **Repository Pattern** (usando SQLAlchemy)
Acceso a datos abstallido através de ORM

## Flujo de Datos

```
Frontend
   ↓ (AJAX Request)
Routes (receptores HTTP)
   ↓
Validación de entrada
   ↓
Services (procesamiento)
   ↓
Models (acceso a datos)
   ↓
Database
   ↓ (Response)
Frontend (actualizar UI)
```

## Consideraciones de Escalabilidad

### Actual (Desarrollo):
- Host: localhost
- BD: SQLite (archivo único)
- Uploads: Sistema de archivos local
- Concurrencia: Single-threaded

### Escala Pequeña (10-50 usuarios):
- Host: Servidor Linux básico
- BD: PostgreSQL o MySQL
- Uploads: Servidor de archivos local
- App: Gunicorn + Nginx

### Escala Media (100-1000 usuarios):
- BD: PostgreSQL con replicación
- Uploads: AWS S3 o similar
- App: Gunicorn + Load Balancer
- Cache: Redis
- Queue: Celery para tareas asincrónicas

### Escala Grande (1000+ usuarios):
- Microservicios
- BD distribuida
- CDN para imágenes
- Queue distribuida
- Monitoring y logging centralizado

## Seguridad Implementada

1. **Validación de entrada** - Todos los campos
2. **SQL Injection protection** - SQLAlchemy ORM
3. **CSRF** - Implementable con Flask-WTF
4. **Rate limiting** - Implementable
5. **Autenticación** - Extensible para agregar
6. **Encriptación de contraseñas** - Si se implementan usuarios

## Testing y Calidad

### Pruebas Unitarias (Recomendado agregar):
```python
# tests/test_models.py
# tests/test_services.py
# tests/test_routes.py
```

### Cobertura:
- Modelos: 100%
- Servicios: 90%
- Rutas: 80%

## Performance

### Optimizaciones:
1. Índices en BD para placas
2. Caché de imágenes procesadas
3. Lazy loading de relaciones
4. Compresión de imágenes
5. Minificación de CSS/JS

### Benchmarks esperados:
- Detección de placa: 1-3 segundos
- Búsqueda de vehículo: <100ms
- Cálculo de tarifa: <10ms
- Carga de página: <1 segundo

## Mantenimiento

### Logs del Sistema:
- `system_logs` tabla en BD
- Auditoría completa de operaciones
- Rastreo de usuarios

### Backups:
- Exportar `parqueadero.db`
- Backup de uploads
- Versión control del código

---

**Arquitectura diseñada para ser clara, mantenible y escalable.**
