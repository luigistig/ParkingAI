#!/bin/bash
# Script de inicio rápido para Linux/Mac
# Sistema de Parqueadero Inteligente

echo ""
echo "==============================================="
echo "  SISTEMA DE PARQUEADERO INTELIGENTE"
echo "  Iniciador Rápido para Linux/Mac"
echo "==============================================="
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no está instalado"
    echo "Instalar con: brew install python3 (Mac) o apt-get install python3 (Linux)"
    exit 1
fi

echo "[OK] Python detectado"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo ""
    echo "Creando entorno virtual..."
    python3 -m venv venv
    echo "[OK] Entorno virtual creado"
fi

# Activar entorno virtual
echo ""
echo "Activando entorno virtual..."
source venv/bin/activate
echo "[OK] Entorno virtual activado"

# Instalar dependencias
echo ""
echo "Instalando/Actualizando dependencias..."
pip install -q -r requirements.txt
echo "[OK] Dependencias instaladas"

# Inicializar base de datos
echo ""
echo "Inicializando base de datos..."
python init_db.py
echo "[OK] Base de datos iniciada"

# Mostrar información
echo ""
echo "==============================================="
echo "  ✓ Sistema listo para ejecutar"
echo "==============================================="
echo ""
echo "Iniciando servidor en http://localhost:5000/"
echo "Presiona Ctrl+C para detener el servidor"
echo ""
echo "==============================================="
echo ""

# Ejecutar la aplicación
python run.py
