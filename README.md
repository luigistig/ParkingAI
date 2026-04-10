# Sistema de Gestión de Parqueadero Inteligente con Reconocimiento de Placas

## 📋 Descripción

Sistema web completo para la gestión de parqueaderos con reconocimiento automático de placas vehiculares mediante inteligencia artificial. Incluye captura de imágenes, OCR, cálculo automático de tarifas y panel de administración.

## ✨ Características Principales

### 1. **Registro Automático de Entrada**
- Captura de imágenes en tiempo real
- Detección automática de placas usando OpenCV
- OCR para extracción de números de placa
- Registro automático en base de datos

### 2. **Sistema de Pago Inteligente**
- Búsqueda de vehículo por placa
- Cálculo automático de tarifa según tiempo estacionado
- Múltiples métodos de pago (efectivo, tarjeta, transferencia, QR)
- Generación de recibos

### 3. **Panel de Control**
- Estadísticas en tiempo real
- Visualización de vehículos activos
- Historial completo de operaciones
- Registros del sistema

### 4. **Panel de Administración**
- Gestión de tarifas
- Monitoreo de actividades
- Backup de base de datos
- Configuración del sistema

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.8+**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para base de datos
- **SQLite** - Base de datos (fácil configuración)

### Procesamiento de Imágenes
- **OpenCV** - Detección y procesamiento de imágenes
- **Tesseract OCR** - Reconocimiento de texto en placas
- **Pillow** - Manipulación de imágenes

### Frontend
- **HTML5** - Estructura
- **CSS3** - Estilos personalizados
- **Bootstrap 5** - Framework responsivo
- **JavaScript Vanilla** - Interactividad

## 📁 Estructura del Proyecto

```
parqueadero_system/
├── app/
│   ├── __init__.py                 # Factory de aplicación
│   ├── models.py                   # Modelos de base de datos
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── vehicles.py            # Rutas de vehículos
│   │   ├── payments.py            # Rutas de pagos
│   │   ├── camera.py              # Rutas de cámara
│   │   └── admin.py               # Rutas de administración
│   ├── services/
│   │   ├── __init__.py
│   │   ├── plate_detection.py     # Detección de placas
│   │   ├── ocr.py                 # OCR para placas
│   │   ├── tariff.py              # Cálculo de tarifas
│   │   └── camera.py              # Gestión de cámara
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Estilos personalizados
│   │   ├── js/
│   │   │   ├── main.js            # JavaScript principal
│   │   │   └── camera.js          # Control de cámara
│   │   └── uploads/               # Imágenes capturadas
│   └── templates/
│       ├── base.html              # Template base
│       ├── index.html             # Page de inicio
│       ├── camera.html            # Registro de entrada
│       ├── payment.html           # Sistema de pago
│       ├── history.html           # Historial
│       └── admin.html             # Panel administrativo
├── config.py                       # Configuración
├── run.py                         # Punto de entrada
├── requirements.txt               # Dependencias
├── .env                          # Variables de entorno
└── README.md                     # Este archivo
```

## 🚀 Instalación y Configuración

### Requisitos Previos

1. **Python 3.8 o superior**
   ```bash
   python --version
   ```

2. **Tesseract OCR** (opcional pero recomendado)
   - Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
   - Instalar en la ubicación predeterminada o configurar ruta en `.env`

3. **Cámara web** (opcional - sistema funciona без hardware)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**
   ```bash
   cd parqueadero_system
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   ```

3. **Activar entorno virtual**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurar variables de entorno**
   - Editar el archivo `.env` con sus configuraciones
   - Especialmente: `TESSERACT_PATH` si está en ubicación no estándar

6. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```

7. **Acceder a la aplicación**
   - Abrir navegador y navegar a: `http://localhost:5000`

## 📖 Guía de Uso

### Flujo de Entrada de Vehículo

1. Dirigirse a **Registro de Entrada**
2. Opción A: Capturar foto con cámara o subir imagen
3. El sistema detectará la placa automáticamente
4. Confirmar la placa detectada
5. Vehículo registrado en el sistema

### Flujo de Pago

1. Dirigirse a **Procesar Pago**
2. Ingresar número de placa del vehículo
3. Sistema muestra:
   - Imagen del vehículo
   - Hora de entrada
   - Tiempo estacionado
   - Valor total a pagar
4. Seleccionar método de pago
5. Confirmar pago
6. Descargar recibo

### Panel de Administración

**Dashboard**
- Ver estadísticas en tiempo real
- Vehículos activos
- Ingresos diarios/mensuales

**Gestionar Vehículos**
- Ver todos los registros
- Filtrar por estado
- Agregar entradas manuales

**Registros**
- Ver historial de actividades
- Auditoría del sistema

**Configuración**
- Ajustar tarifas
- Configurar cámara
- Realizar backups

## 💰 Sistema de Tarifas

### Tarificación Estándar
- **$2.000 por hora**
- **Cargo mínimo: $500**
- Sistema redondea al alza por fracción de hora

### Ejemplo de Cálculo
```
Entrada: 10:00
Salida: 12:30
Tiempo: 2h 30m → Se cobran 3 horas
Valor: 3h × $2.000 = $6.000
```

## 🔧 Configuración de Cámara

### Cámara Predeterminada (USB/Integrated)
1. Conectar cámara al equipo
2. La aplicación detecta automáticamente (índice 0)

### Múltiples Cámaras
- En `.env`, cambiar `CAMERA_INDEX` a 1, 2, etc.

### Uso sin Cámara
- Sistema funciona cargando imágenes
- O entrada manual de placas

## 📊 Base de Datos

### Tablas Principales

**vehicles**
- id, placa, hora_entrada, hora_salida, tiempo_total, valor_a_pagar, ruta_imagen, estado, marca, color

**payment_records**
- id, vehicle_id, monto, fecha_pago, metodo_pago, estado

**parking_spaces**
- id, numero, estado, vehicle_id

**system_logs**
- id, accion, detalles, fecha, usuario

## 🔐 Seguridad

### Implementaciones de Seguridad

1. **Validación de entrada** - Todos los datos se validan
2. **SQL Injection prevención** - Uso de SQLAlchemy ORM
3. **CSRF Protection** - Implementable con Flask-WTF
4. **Sesiones seguras** - Configuradas con SECRET_KEY

### Para Producción

1. Cambiar `DEBUG = False`
2. Cambiar `SECRET_KEY` en config.py
3. Usar base de datos robusta (MySQL/PostgreSQL)
4. Implementar HTTPS
5. Usar servidor WSGI (Gunicorn, Waitress)

## 🚀 Deployment con Gunicorn

```bash
# Instalar Gunicorn
pip install gunicorn

# Ejecutar aplicación
gunicorn -b 0.0.0.0:5000 run:app
```

## 🐛 Solución de Problemas

### Error: "Tesseract is not installed"
- Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
- Actualizar ruta en `.env`

### Error: "Cannot open camera"
- Verificar que la cámara está conectada
- Verificar permisos del navegador (HTTPS o localhost)
- Sistema funciona sin cámara (cargar imágenes)

### Error de Puerto 5000 en uso
- Cambiar puerto en `.env`: `FLASK_PORT=8000`

### Base de datos corrupta
- Eliminar archivo `parqueadero.db`
- Reiniciar aplicación (se recrea automáticamente)

## 📚 API Endpoints

### Vehículos
- `GET /api/vehicles` - Listar activos
- `GET /api/vehicles/search/<placa>` - Buscar por placa
- `POST /api/vehicles/checkin` - Registrar entrada
- `POST /api/vehicles/checkout/<id>` - Registrar salida

### Pagos
- `POST /api/payments/calculate` - Calcular monto
- `POST /api/payments` - Registrar pago
- `GET /api/payments/history` - Historial de pagos

### Cámara
- `POST /api/camera/capture` - Capturar imagen
- `POST /api/camera/detect` - Detectar placa

### Admin
- `GET /admin/statistics` - Estadísticas
- `GET /admin/logs` - Registros del sistema
- `GET /admin/vehicles` - Listar vehículos

## 📝 Notas Importantes

1. **Diseño modular** - Fácil de extender y personalizar
2. **Base de datos SQLite** - Sin configuración adicional, ideal para demostración
3. **Frontend responsivo** - Se adapta a cualquier dispositivo
4. **OCR opcional** - Funciona sin Tesseract (con detección manual)
5. **Escalable** - Puede crecer a miles de registros

## 🤝 Contribuciones

Este es un proyecto de demostración. Siéntase libre de:
- Agregar nuevas características
- Mejorar la precisión del OCR
- Implementar más métodos de pago
- Optimizar el código

## 📄 Licencia

Proyecto educativo de demostración.

## 👨‍💻 Desarrollado por

Sistema de Parqueadero Inteligente con IA - 2026

## 📧 Soporte

Para preguntas o problemas:
1. Revisar la sección "Solución de Problemas"
2. Verificar logs del sistema en el panel de administración
3. Revisar documentación en línea

---

**¡Gracias por usar el Sistema de Parqueadero Inteligente!**
