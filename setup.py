#!/usr/bin/env python
"""
Script de inicio y diagnóstico completo del sistema
"""
import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Imprimir encabezado"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_python():
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠ Se requiere Python 3.8 o superior")
        return False
    return True


def check_dependencies():
    """Verificar dependencias"""
    print("Verificando dependencias...")

    required = ["flask", "sqlalchemy", "opencv", "PIL"]

    all_ok = True
    for dep in required:
        try:
            __import__(dep.replace("-", "_"))
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} (no instalado)")
            all_ok = False

    return all_ok


def check_tesseract():
    """Verificar Tesseract OCR"""
    print("\nVerificando Tesseract OCR...")

    paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]

    for path in paths:
        if os.path.exists(path):
            print(f"  ✓ Encontrado en: {path}")
            return True

    print("  ⚠ Tesseract no encontrado (OCR limitado)")
    print("    Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki")
    return False


def check_camera():
    """Verificar cámara"""
    print("\nVerificando cámara...")

    try:
        import cv2

        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("  ✓ Cámara detectada")
            cap.release()
            return True
        else:
            print("  ⚠ Cámara no disponible")
            print("    Sistema funcionará con carga de imágenes")
            return False
    except Exception as e:
        print(f"  ⚠ Error: {e}")
        return False


def setup_database():
    """Configurar base de datos"""
    print("\nInicializando base de datos...")

    try:
        from app import create_app, db

        app = create_app("development")
        with app.app_context():
            db.create_all()
            print("  ✓ Base de datos inicializada")
            return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def start_server():
    """Iniciar servidor"""
    print_header("INICIANDO SERVIDOR")
    print("Ejecutando: python run.py")
    print("\n⏳ Servidor iniciando en http://localhost:5000/")
    print("   Presione Ctrl+C para detener\n")

    try:
        subprocess.run(["python", "run.py"], cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\n\n✓ Servidor detenido")


def main():
    """Función principal"""
    print_header("DIAGNÓSTICO Y CONFIGURACIÓN DEL SISTEMA")

    # Verificaciones
    print("1️⃣  VERIFICACIÓN DE REQUISITOS\n")

    if not check_python():
        sys.exit(1)

    if not check_dependencies():
        print("\n⚠️  Instale dependencias: pip install -r requirements.txt")
        response = input("¿Continuar de todas formas? (s/n): ")
        if response.lower() != "s":
            sys.exit(1)

    check_tesseract()
    check_camera()

    # Configuración
    print_header("2️⃣  CONFIGURACIÓN DEL SISTEMA")

    # Crear carpeta de uploads
    uploads_dir = Path("app/static/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    print("✓ Carpeta de carga: app/static/uploads/")

    # Inicializar BD
    if setup_database():
        print("✓ Sistema listo para usar")
    else:
        print("⚠ Error en configuración de BD")

    # Mostrar información
    print_header("3️⃣  INFORMACIÓN DEL SISTEMA")

    print("Frontend:  HTML5 + CSS3 + JavaScript + Bootstrap 5")
    print("Backend:   Flask + SQLAlchemy")
    print("BD:        SQLite (parqueadero.db)")
    print("IA:        OpenCV + Tesseract OCR")

    print_header("4️⃣  PRÓXIMOS PASOS")

    print("1. Abrir navegador: http://localhost:5000/")
    print("2. Ir a 'Registro de Entrada' para agregar vehículos")
    print("3. Ir a 'Procesar Pago' para registrar pagos")
    print("4. Revisar 'Administración' para estadísticas")

    response = input("\n¿Iniciar servidor ahora? (s/n): ")
    if response.lower() == "s":
        start_server()
    else:
        print("\nEjecutar después manualmente: python run.py")


if __name__ == "__main__":
    main()
