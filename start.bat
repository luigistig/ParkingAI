@echo off
REM Script de inicio rápido para Windows
REM Sistema de Parqueadero Inteligente

echo.
echo ===============================================
echo   SISTEMA DE PARQUEADERO INTELIGENTE
echo   Iniciador Rápido para Windows
echo ===============================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH
    echo Descargar desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detectado

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo.
    echo Creando entorno virtual...
    python -m venv venv
    echo [OK] Entorno virtual creado
)

REM Activar entorno virtual
echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo [OK] Entorno virtual activado

REM Instalar dependencias
echo.
echo Instalando/Actualizando dependencias...
pip install -q -r requirements.txt
echo [OK] Dependencias instaladas

REM Inicializar base de datos
echo.
echo Inicializando base de datos...
python init_db.py
echo [OK] Base de datos iniciada

REM Mostrar información
echo.
echo ===============================================
echo   ✓ Sistema listo para ejecutar
echo ===============================================
echo.
echo Iniciando servidor en http://localhost:5000/
echo Presiona Ctrl+C para detener el servidor
echo.
echo ===============================================
echo.

REM Ejecutar la aplicación
python run.py

pause
