
from app.services.audit_service import AuditService
from flask import (
    request,
    jsonify,
    current_app,
    Response,
)

from werkzeug.utils import secure_filename

from app import db
from app.models import (
    Vehicle,
    SystemLog,
    VehiclePhoto,
)

from app.services.plate_detection import PlateDetector
from app.services.ocr import PlateOCR
from app.services.vehicle_detection import VehicleDetector
from app.services.camera import get_camera_service

import cv2
import os
import time
import contextlib
import io

from datetime import datetime


# ============================================================================
# VARIABLES GLOBALES
# ============================================================================

_last_plate_detection_log = 0
LOG_THROTTLE_SECONDS = 5

_last_ai_detection = 0
AI_DETECTION_THROTTLE_SECONDS = 5


# ============================================================================
# AUDITORÍA
# ============================================================================

def registrar_auditoria(
    accion,
    modulo,
    nivel="INFO",
    descripcion="",
    usuario="Sistema"
):
    """
    Registrar eventos de auditoría
    """

    try:

        AuditService.log_event(
            accion=accion,
            modulo=modulo,
            nivel=nivel,
            descripcion=descripcion,
            usuario=usuario
        )

    except Exception as e:

        print(f"ERROR REGISTRANDO AUDITORÍA: {e}")


# ============================================================================
# LOG DE PLACAS
# ============================================================================

def log_plate_detection(
    plate_number,
    action="detectada",
    extra_info=""
):
    """
    Log de detección de placas
    """

    global _last_plate_detection_log

    current_time = time.time()

    if current_time - _last_plate_detection_log >= LOG_THROTTLE_SECONDS:

        timestamp = datetime.now().strftime("%H:%M:%S")

        message = f"[{timestamp}] 🚗 PLACA {action.upper()}: {plate_number}"

        if extra_info:
            message += f" - {extra_info}"

        print(message)

        _last_plate_detection_log = current_time


# ============================================================================
# STREAM NORMAL
# ============================================================================

def camera_stream():
    """
    Stream de cámara normal
    """

    try:

        camera = get_camera_service(use_mock=False)

        def generate():

            if not camera.camera or not camera.camera.isOpened():

                if not camera.open_camera():

                    registrar_auditoria(
                        accion="ERROR_CAMARA",
                        modulo="CAMERA_STREAM",
                        nivel="ERROR",
                        descripcion="No se pudo abrir cámara"
                    )

                    return

            error_count = 0

            while error_count < 10:

                try:

                    frame = camera.get_frame_for_display()

                    if frame is None:

                        error_count += 1
                        time.sleep(0.1)
                        continue

                    error_count = 0

                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + frame
                        + b"\r\n"
                    )

                except Exception as e:

                    print(f"ERROR STREAM: {e}")

                    error_count += 1
                    time.sleep(0.1)

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    except Exception as e:

        registrar_auditoria(
            accion="ERROR_STREAM",
            modulo="CAMERA_STREAM",
            nivel="ERROR",
            descripcion=str(e)
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# STREAM IA
# ============================================================================

def camera_stream_ai():
    """
    Stream con IA
    """

    try:

        camera = get_camera_service(use_mock=False)

        detector = VehicleDetector()

        def generate():

            global _last_ai_detection

            if not camera.camera or not camera.camera.isOpened():

                if not camera.open_camera():

                    registrar_auditoria(
                        accion="ERROR_CAMARA_AI",
                        modulo="CAMERA_STREAM_AI",
                        nivel="ERROR",
                        descripcion="No se pudo abrir cámara IA"
                    )

                    return

            error_count = 0

            while error_count < 10:

                try:

                    ret, frame = camera.camera.read()

                    if not ret:

                        error_count += 1
                        time.sleep(0.1)
                        continue

                    error_count = 0

                    current_time = time.time()

                    if (
                        current_time - _last_ai_detection
                        >= AI_DETECTION_THROTTLE_SECONDS
                    ):

                        vehicles = detector.detect_vehicles(frame)

                        annotated = detector.annotate_image(
                            frame,
                            vehicles
                        )

                        _last_ai_detection = current_time

                    else:

                        with contextlib.redirect_stdout(io.StringIO()):

                            detector.detect_vehicles(frame)

                        annotated = frame

                    ret, buffer = cv2.imencode(
                        ".jpg",
                        annotated
                    )

                    if ret:

                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + buffer.tobytes()
                            + b"\r\n"
                        )

                except Exception as e:

                    registrar_auditoria(
                        accion="ERROR_FRAME_AI",
                        modulo="CAMERA_STREAM_AI",
                        nivel="ERROR",
                        descripcion=str(e)
                    )

                    error_count += 1
                    time.sleep(0.1)

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    except Exception as e:

        registrar_auditoria(
            accion="ERROR_STREAM_AI",
            modulo="CAMERA_STREAM_AI",
            nivel="ERROR",
            descripcion=str(e)
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# DETECCIÓN AUTOMÁTICA
# ============================================================================

def detect_vehicle_auto():
    """
    Detectar vehículo automáticamente
    """

    try:

        registrar_auditoria(
            accion="INICIO_DETECCION",
            modulo="IA",
            descripcion="Inicio detección automática"
        )

        camera = get_camera_service(use_mock=False)

        if not camera.camera or not camera.camera.isOpened():

            if not camera.open_camera():

                return jsonify({
                    "success": False,
                    "error": "No se pudo abrir cámara"
                }), 500

        vehicle_detector = VehicleDetector()
        plate_detector = PlateDetector()
        ocr = PlateOCR()

        ret, frame = camera.camera.read()

        if not ret:

            return jsonify({
                "success": False,
                "error": "No se pudo capturar frame"
            }), 500

        plates = plate_detector.detect_plates(frame)

        plate_number = None
        plate_conf = 0

        if plates:

            plate = max(
                plates,
                key=lambda p: p["conf"]
            )

            plate_img = plate_detector.crop_plate(
                frame,
                plate
            )

            if plate_img is not None:

                plate_number = ocr.extract_plate_number(
                    plate_img
                )

                plate_conf = plate["conf"]

        if not plate_number:

            registrar_auditoria(
                accion="PLACA_NO_DETECTADA",
                modulo="OCR",
                nivel="WARNING",
                descripcion="No se detectó placa"
            )

            return jsonify({
                "success": False,
                "error": "No se detectó placa"
            }), 400

        log_plate_detection(
            plate_number,
            "detectada",
            f"Confianza: {plate_conf:.2f}"
        )

        existing = Vehicle.query.filter_by(
            placa=plate_number,
            estado="dentro"
        ).first()

        if existing:

            return jsonify({
                "success": False,
                "error": "Vehículo ya registrado"
            }), 400

        vehicle_type = "carro"
        color = "Desconocido"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"vehicle_{plate_number}_{timestamp}.jpg"

        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            filename
        )

        cv2.imwrite(filepath, frame)

        vehicle_record = Vehicle(
            placa=plate_number,
            marca=vehicle_type,
            color=color,
            ruta_imagen=filepath
        )

        db.session.add(vehicle_record)
        db.session.commit()

        registrar_auditoria(
            accion="VEHICULO_REGISTRADO",
            modulo="PARKING",
            descripcion=f"Vehículo registrado: {plate_number}"
        )

        SystemLog.create_log(
            accion="ENTRADA_REGISTRADA",
            detalles=f"Vehículo {plate_number} registrado"
        )

        return jsonify({
            "success": True,
            "message": "Vehículo registrado",
            "vehicle": {
                "placa": plate_number,
                "tipo": vehicle_type,
                "color": color,
                "imagen": filepath,
                "confianza_placa": plate_conf
            }
        })

    except Exception as e:

        db.session.rollback()

        registrar_auditoria(
            accion="ERROR_DETECCION",
            modulo="IA",
            nivel="ERROR",
            descripcion=str(e)
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# CAPTURAR IMAGEN
# ============================================================================

def capture_image():
    """
    Capturar imagen desde cámara
    """

    try:

        registrar_auditoria(
            accion="CAPTURA_IMAGEN",
            modulo="CAMARA",
            descripcion="Captura manual"
        )

        camera = get_camera_service(use_mock=False)

        success, filepath = camera.capture_and_save(
            current_app.config["UPLOAD_FOLDER"]
        )

        if not success:

            return jsonify({
                "success": False,
                "error": "No se pudo capturar imagen"
            }), 500

        return jsonify({
            "success": True,
            "filepath": filepath,
            "message": "Imagen capturada"
        }), 201

    except Exception as e:

        registrar_auditoria(
            accion="ERROR_CAPTURA",
            modulo="CAMARA",
            nivel="ERROR",
            descripcion=str(e)
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# DETECTAR PLACA
# ============================================================================

def detect_plate():
    """
    Detectar placa desde imagen
    """

    try:

        data = request.get_json()

        if "filepath" not in data:

            return jsonify({
                "success": False,
                "error": "Ruta requerida"
            }), 400

        filepath = data["filepath"]

        image = cv2.imread(filepath)

        if image is None:

            return jsonify({
                "success": False,
                "error": "No se pudo leer imagen"
            }), 400

        detector = PlateDetector()
        ocr = PlateOCR()

        plates = detector.detect_plates(image)

        results = []

        for plate in plates:

            plate_img = detector.crop_plate(
                image,
                plate
            )

            if plate_img is not None:

                text = ocr.extract_plate_number(
                    plate_img
                )

                results.append({
                    "plate": text,
                    "confidence": plate.get("conf", 0)
                })

        registrar_auditoria(
            accion="PLACA_ANALIZADA",
            modulo="OCR",
            descripcion=f"Cantidad placas: {len(results)}"
        )

        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:

        registrar_auditoria(
            accion="ERROR_OCR",
            modulo="OCR",
            nivel="ERROR",
            descripcion=str(e)
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# SUBIR IMAGEN IA
# ============================================================================

def process_image_ai():
    """
    Procesar imagen manual
    """

    try:

        if "file" not in request.files:

            return jsonify({
                "success": False,
                "error": "Archivo requerido"
            }), 400

        file = request.files["file"]

        if file.filename == "":

            return jsonify({
                "success": False,
                "error": "Archivo vacío"
            }), 400

        filename = secure_filename(file.filename)

        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(filepath)

        registrar_auditoria(
            accion="IMAGEN_SUBIDA",
            modulo="UPLOAD",
            descripcion=f"Archivo: {filename}"
        )

        return jsonify({
            "success": True,
            "filepath": filepath,
            "message": "Imagen subida"
        })

    except Exception as e:

        registrar_auditoria(
            accion="ERROR_UPLOAD",
            modulo="UPLOAD",
            nivel="ERROR",
            descripcion=str(e)
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
