# 🚀 Guía Rápida de Inicio

## 1. Instalación Rápida (5 minutos)

### Paso 1: Clonar/Descargar el proyecto
```bash
cd parqueadero_system
```

### Paso 2: Crear entorno virtual (Windows)
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Inicializar base de datos
```bash
python init_db.py
```

### Paso 5: Ejecutar aplicación
```bash
python run.py
```

### Paso 6: Abrir en navegador
```
http://localhost:5000
```

---

## 2. Primeros Pasos

### Registrar un Vehículo
1. Click en "Registro de Entrada"
2. Subir/capturar foto de vehículo
3. Sistema detecta placa automáticamente
4. Confirmar entrada

### Procesar Pago
1. Click en "Procesar Pago"
2. Ingresar número de placa
3. Revisar información
4. Seleccionar método de pago
5. Confirmar

### Panel de Administración
1. Click en "Administración"
2. Ver estadísticas en tiempo real
3. Gestionar vehículos
4. Revisar logs

---

## 3. Configuración Inicial

### Cambiar Puerto
En `.env`:
```
FLASK_PORT=8000
```

### Activar Tesseract OCR
1. Descargar instalador: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar
3. Actualizar ruta en `.env`:
```
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Cambiar Tarifas
En `.env`:
```
TARIFF_PER_HOUR=3000
MIN_CHARGE=1000
```

---

## 4. Estructura de Bases de Datos

La aplicación crea automáticamente:
- `parqueadero.db` - Archivo de base de datos SQLite
- Tablas: vehicles, payments, parking_spaces, logs

---

## 5. API Básica

### Buscar Vehículo
```bash
curl http://localhost:5000/api/vehicles/search/ABC-1234
```

### Registrar Entrada
```bash
curl -X POST http://localhost:5000/api/vehicles/checkin \
  -H "Content-Type: application/json" \
  -d '{"placa":"ABC-1234","marca":"Toyota","color":"Negro"}'
```

### Calcular Pago
```bash
curl -X POST http://localhost:5000/api/payments/calculate \
  -H "Content-Type: application/json" \
  -d '{"placa":"ABC-1234"}'
```

### Estadísticas
```bash
curl http://localhost:5000/admin/statistics
```

---

## 6. Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Port 5000 en uso | Cambiar en `.env`: `FLASK_PORT=8000` |
| Tesseract no encontrado | Instalar o actualizar ruta en `.env` |
| Cámara no funciona | Sistema automáticamente usa carga de archivos |
| BD corrupta | Eliminar `parqueadero.db` y reiniciar |
| Module not found | Activar venv: `venv\Scripts\activate` |

---

## 7. Comandos Útiles

```bash
# Activar entorno virtual
venv\Scripts\activate

# Desactivar entorno virtual
deactivate

# Ver logs
tail -f logs.txt

# Limpiar DB
rm parqueadero.db

# Reinstalar paquetes
pip install --upgrade -r requirements.txt
```

---

## 8. Contacto y Soporte

- 📖 Ver README.md para documentación completa
- 🔧 Revisar `.env` para configuraciones
- 📊 Panel de admin en `/admin`

---

**¡Listo! Sistema en ejecución** ✓
