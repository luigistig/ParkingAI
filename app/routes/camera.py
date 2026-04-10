"""
Rutas para cámara y detección de placas
"""

from flask import request, jsonify, render_template, current_app, Response
from werkzeug.utils import secure_filename
from app import db
from app.models import Vehicle, SystemLog, VehiclePhoto
from app.services.plate_detection import PlateDetector
from app.services.ocr import PlateOCR
from app.services.vehicle_detection import VehicleDetector
from app.services.camera import CameraService, get_camera_service
import cv2
import os
import time
from datetime import datetime
import contextlib
import io

# Variable global para controlar el throttling de mensajes de consola
_last_plate_detection_log = 0
LOG_THROTTLE_SECONDS = 5

# Variable global para controlar la detección de IA en el stream
_last_ai_detection = 0
AI_DETECTION_THROTTLE_SECONDS = 5


def log_plate_detection(plate_number, action="detectada", extra_info=""):
    """
    Función para loggear detección de placas con throttling

    Args:
        plate_number: Número de placa detectado
        action: Acción realizada ("detectada", "registrada", etc.)
        extra_info: Información adicional
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


def camera_stream():
    """Stream en tiempo real de la cámara"""
    try:
        camera = get_camera_service(use_mock=False)

        def generate():
            # Abrir cámara si no está abierta
            if not camera.camera or not camera.camera.isOpened():
                if not camera.open_camera():
                    print("No se pudo abrir la cámara para stream")
                    return

            # Intentar obtener frames
            error_count = 0
            while error_count < 10:
                try:
                    frame = camera.get_frame_for_display()
                    if frame is None:
                        error_count += 1
                        time.sleep(0.1)
                        continue
                    error_count = 0  # Reset contador de errores
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                    )
                except:
                    error_count += 1
                    time.sleep(0.1)

        return Response(
            generate(), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    except Exception as e:
        print(f"Error en camera_stream: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def camera_stream_ai():
    """Stream en tiempo real con detección de IA"""
    try:
        camera = get_camera_service(use_mock=False)
        detector = VehicleDetector()

        def generate():
            global _last_ai_detection

            if not camera.camera or not camera.camera.isOpened():
                if not camera.open_camera():
                    print("No se pudo abrir la cámara para stream AI")
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

                    # Solo detectar cada AI_DETECTION_THROTTLE_SECONDS segundos
                    if (
                        current_time - _last_ai_detection
                        >= AI_DETECTION_THROTTLE_SECONDS
                    ):
                        # Detectar vehículos (permitir output de YOLOv8)
                        vehicles = detector.detect_vehicles(frame)

                        # Anotar imagen
                        annotated = detector.annotate_image(frame, vehicles)

                        # Actualizar timestamp de última detección
                        _last_ai_detection = current_time
                    else:
                        # Detectar vehículos pero suprimir output de YOLOv8
                        with contextlib.redirect_stdout(io.StringIO()):
                            vehicles = detector.detect_vehicles(frame)

                        # Usar frame sin anotaciones
                        annotated = frame

                    # Codificar para stream
                    ret, buffer = cv2.imencode(".jpg", annotated)
                    if ret:
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n"
                            + buffer.tobytes()
                            + b"\r\n"
                        )

                except Exception as e:
                    print(f"Error en frame AI: {e}")
                    error_count += 1
                    time.sleep(0.1)

        return Response(
            generate(), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    except Exception as e:
        print(f"Error en camera_stream_ai: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def detect_vehicle_auto():
    """Detectar vehículo automáticamente y registrar"""
    try:
        camera = get_camera_service(use_mock=False)

        # Verificar si la cámara está disponible
        if not camera.camera or not camera.camera.isOpened():
            if not camera.open_camera():
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Cámara no disponible. Conecte una cámara o use carga manual de imágenes.",
                        }
                    ),
                    503,
                )

        vehicle_detector = VehicleDetector()
        plate_detector = PlateDetector()
        ocr = PlateOCR()

        # Capturar frame
        ret, frame = camera.camera.read()
        if not ret or frame is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se pudo capturar imagen de la cámara",
                    }
                ),
                500,
            )

        # PRIMERO intentar detectar placas en toda la imagen (más robusto)
        plates = plate_detector.detect_plates(frame)

        plate_number = None
        plate_conf = 0
        if plates:
            # Tomar la placa más confiable
            plate = max(plates, key=lambda p: p["conf"])
            plate_img = plate_detector.crop_plate(frame, plate)
            if plate_img is not None and plate_img.size > 0:
                plate_number = ocr.extract_plate_number(plate_img)
                plate_conf = plate["conf"]

        # Si no se detectó placa, intentar el método anterior (vehículo + placa)
        if not plate_number:
            # Detectar vehículos
            vehicles = vehicle_detector.detect_vehicles(frame)

            if vehicles:
                # Tomar el vehículo más grande (más cercano)
                vehicle = max(vehicles, key=lambda v: v["w"] * v["h"])

                # Detectar placas en el área del vehículo
                x, y, w, h = vehicle["x"], vehicle["y"], vehicle["w"], vehicle["h"]
                vehicle_roi = frame[y : y + h, x : x + w]

                plates = plate_detector.detect_plates(vehicle_roi)

                if plates:
                    # Tomar la placa más confiable
                    plate = max(plates, key=lambda p: p["conf"])
                    plate_img = plate_detector.crop_plate(vehicle_roi, plate)
                    if plate_img is not None and plate_img.size > 0:
                        plate_number = ocr.extract_plate_number(plate_img)
                        plate_conf = plate["conf"]

        # Si aún no hay placa, intentar OCR directo en toda la imagen
        if not plate_number:
            try:
                # OCR directo en la imagen completa
                plate_number = ocr.extract_text(frame)
                if plate_number:
                    plate_conf = 0.3  # Confianza baja para OCR directo
            except:
                pass

        if not plate_number:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se pudo detectar ninguna placa en la imagen. Asegúrese de que la placa sea visible y bien iluminada.",
                    }
                ),
                400,
            )

        # Loggear detección de placa
        log_plate_detection(plate_number, "detectada", f"Confianza: {plate_conf:.2f}")

        # Verificar si ya está registrado
        existing = Vehicle.query.filter_by(placa=plate_number, estado="dentro").first()
        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Vehículo {plate_number} ya está dentro del parqueadero",
                    }
                ),
                400,
            )

        # Detectar vehículo para obtener tipo y color (opcional)
        vehicle_type = "carro"  # Default a carro cuando solo se detecta placa
        color = "Desconocido"

        vehicles = vehicle_detector.detect_vehicles(frame)
        if vehicles:
            vehicle = max(vehicles, key=lambda v: v["w"] * v["h"])
            vehicle_type = vehicle["class"].title()
            color = vehicle_detector.get_dominant_color(frame, vehicle)

        # Guardar imagen
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vehicle_{plate_number}_{timestamp}.jpg"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        cv2.imwrite(filepath, frame)

        # Crear registro del vehículo
        vehicle_record = Vehicle(
            placa=plate_number,
            marca=vehicle_type,
            color=color,
            ruta_imagen=filepath,
        )

        db.session.add(vehicle_record)
        db.session.commit()

        # Loggear registro exitoso
        log_plate_detection(
            plate_number, "registrada", f"Tipo: {vehicle_type}, Color: {color}"
        )

        # Registrar en logs
        SystemLog.create_log(
            accion="ENTRADA_REGISTRADA_AUTO",
            detalles=f"Vehículo {plate_number} ({vehicle_type}, {color}) detectado y registrado automáticamente. Confianza placa: {plate_conf:.2f}",
        )

        return jsonify(
            {
                "success": True,
                "message": f"Vehículo registrado exitosamente con placa {plate_number}",
                "vehicle": {
                    "placa": plate_number,
                    "tipo": vehicle_type,
                    "color": color,
                    "imagen": filepath,
                    "confianza_placa": plate_conf,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


def process_image_ai():
    """Procesar imagen subida con IA y registrar vehículo"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No se encontró archivo"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "Archivo vacío"}), 400

        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}",
        )
        file.save(filepath)

        # Leer imagen
        image = cv2.imread(filepath)
        if image is None:
            os.remove(filepath)
            return (
                jsonify({"success": False, "error": "No se pudo leer la imagen"}),
                400,
            )

        # Procesar con IA - MÉTODO ROBUSTO
        vehicle_detector = VehicleDetector()
        plate_detector = PlateDetector()
        ocr = PlateOCR()

        # PRIMERO intentar detectar placas en toda la imagen (más robusto)
        plates = plate_detector.detect_plates(image)

        plate_number = None
        plate_conf = 0
        if plates:
            # Tomar la placa más confiable
            plate = max(plates, key=lambda p: p["conf"])
            plate_img = plate_detector.crop_plate(image, plate)
            if plate_img is not None and plate_img.size > 0:
                plate_number = ocr.extract_plate_number(plate_img)
                plate_conf = plate["conf"]

        # Si no se detectó placa, intentar el método anterior (vehículo + placa)
        if not plate_number:
            # Detectar vehículos
            vehicles = vehicle_detector.detect_vehicles(image)

            if vehicles:
                # Tomar el vehículo más grande
                vehicle = max(vehicles, key=lambda v: v["w"] * v["h"])

                # Detectar placas en el área del vehículo
                x, y, w, h = vehicle["x"], vehicle["y"], vehicle["w"], vehicle["h"]
                vehicle_roi = image[y : y + h, x : x + w]

                plates = plate_detector.detect_plates(vehicle_roi)

                if plates:
                    # Tomar la placa más confiable
                    plate = max(plates, key=lambda p: p["conf"])
                    plate_img = plate_detector.crop_plate(vehicle_roi, plate)
                    if plate_img is not None and plate_img.size > 0:
                        plate_number = ocr.extract_plate_number(plate_img)
                        plate_conf = plate["conf"]

        # Si aún no hay placa, intentar OCR directo en toda la imagen
        if not plate_number:
            try:
                # OCR directo en la imagen completa
                plate_number = ocr.extract_text(image)
                if plate_number:
                    plate_conf = 0.3  # Confianza baja para OCR directo
            except:
                pass

        if not plate_number:
            os.remove(filepath)  # Limpiar archivo temporal
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No se pudo detectar ninguna placa en la imagen. Asegúrese de que la placa sea visible y bien iluminada.",
                    }
                ),
                400,
            )

        # Loggear detección de placa
        log_plate_detection(plate_number, "detectada", f"Confianza: {plate_conf:.2f}")

        # Verificar si ya está registrado
        existing = Vehicle.query.filter_by(placa=plate_number, estado="dentro").first()
        if existing:
            os.remove(filepath)  # Limpiar archivo temporal
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Vehículo {plate_number} ya está dentro del parqueadero",
                    }
                ),
                400,
            )

        # Detectar vehículo para obtener tipo y color (opcional)
        vehicle_type = "Desconocido"
        color = "Desconocido"

        vehicles = vehicle_detector.detect_vehicles(image)
        if vehicles:
            vehicle = max(vehicles, key=lambda v: v["w"] * v["h"])
            vehicle_type = vehicle["class"].title()
            color = vehicle_detector.get_dominant_color(image, vehicle)

        # Mover imagen a ubicación final
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"vehicle_{plate_number}_{timestamp}.jpg"
        final_filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"], final_filename
        )
        os.rename(filepath, final_filepath)

        # Crear registro del vehículo
        vehicle_record = Vehicle(
            placa=plate_number,
            marca=vehicle_type,
            color=color,
            ruta_imagen=final_filepath,
        )

        db.session.add(vehicle_record)
        db.session.commit()

        # Loggear registro exitoso
        log_plate_detection(
            plate_number, "registrada", f"Tipo: {vehicle_type}, Color: {color}"
        )

        # Registrar en logs
        SystemLog.create_log(
            accion="ENTRADA_REGISTRADA_AI",
            detalles=f"Vehículo {plate_number} ({vehicle_type}, {color}) procesado con IA y registrado. Confianza placa: {plate_conf:.2f}",
        )

        return jsonify(
            {
                "success": True,
                "message": f"Vehículo registrado exitosamente con placa {plate_number}",
                "vehicle": {
                    "placa": plate_number,
                    "tipo": vehicle_type,
                    "color": color,
                    "imagen": final_filepath,
                    "confianza_placa": plate_conf,
                },
            }
        )

    except Exception as e:
        if "filepath" in locals() and os.path.exists(filepath):
            os.remove(filepath)  # Limpiar archivo temporal en caso de error
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


def capture_image():
    """Capturar imagen desde la cámara o archivo subido"""
    try:
        # Verificar si se subió un archivo
        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return (
                    jsonify({"success": False, "error": "No se seleccionó archivo"}),
                    400,
                )

            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"],
                    f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}",
                )
                file.save(filepath)
        else:
            # Capturar desde cámara (usando instancia única)
            camera = get_camera_service(use_mock=False)

            success, filepath = camera.capture_and_save(
                current_app.config["UPLOAD_FOLDER"]
            )
            # No cerrar la cámara - mantenerla abierta para reutilizar

            if not success:
                return (
                    jsonify({"success": False, "error": "Error al capturar imagen"}),
                    500,
                )

        return (
            jsonify(
                {
                    "success": True,
                    "filepath": filepath,
                    "message": "Imagen capturada exitosamente",
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def detect_plate():
    """Detectar y extraer número de placa de una imagen"""
    try:
        data = request.get_json()

        if "filepath" not in data:
            return jsonify({"success": False, "error": "Ruta de imagen requerida"}), 400

        filepath = data["filepath"]

        # Verificar que el archivo existe
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Archivo no encontrado"}), 404

        # Detectar placas
        detector = PlateDetector()
        plates = detector.detect_plates(filepath)

        if not plates:
            return (
                jsonify(
                    {
                        "success": True,
                        "plates": [],
                        "message": "No se detectaron placas en la imagen",
                    }
                ),
                200,
            )

        # Extraer OCR para cada placa
        ocr = PlateOCR()
        results = []

        for idx, (x, y, w, h) in enumerate(plates):
            # Extraer ROI
            plate_roi = detector.extract_plate_roi(filepath, x, y, w, h)

            # Preprocesar
            if plate_roi is not None:
                processed = detector.preprocess_plate(plate_roi)

                # Extraer texto
                plate_text = ocr.extract_text(processed)
                plate_number = ocr._normalize_plate(plate_text) if plate_text else None

                # Guardar imagen de la placa
                plate_img_path = None
                if plate_roi is not None:
                    plate_img_filename = (
                        f"plate_{idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    )
                    plate_img_path = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], plate_img_filename
                    )
                    cv2.imwrite(plate_img_path, plate_roi)

                # Si la placa es válida, guardar automáticamente la imagen del vehículo
                is_valid = ocr._is_valid_plate(plate_number) if plate_number else False
                if is_valid and plate_number:
                    try:
                        # Loggear detección y registro automático
                        log_plate_detection(
                            plate_number,
                            "detectada y registrada",
                            "Registro automático desde detección manual",
                        )

                        # Buscar o crear vehículo
                        vehicle = Vehicle.query.filter_by(placa=plate_number).first()

                        if not vehicle:
                            vehicle = Vehicle(
                                placa=plate_number,
                                hora_entrada=datetime.now(),
                                estado="dentro",
                            )
                            db.session.add(vehicle)
                            db.session.flush()  # Para obtener el ID

                        # Guardar foto en VehiclePhoto
                        vehicle_photo = VehiclePhoto(
                            vehicle_id=vehicle.id,
                            ruta_imagen=filepath,
                            tipo="placa_detectada",
                            fecha_captura=datetime.now(),
                        )
                        db.session.add(vehicle_photo)

                        # Actualizar ruta_imagen del vehículo
                        vehicle.ruta_imagen = filepath
                        db.session.commit()

                        SystemLog.create_log(
                            "PLACA_DETECTADA",
                            f"Placa {plate_number} detectada y foto guardada",
                        )
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error guardando foto: {str(e)}")

                results.append(
                    {
                        "idx": idx,
                        "coordinates": {"x": x, "y": y, "w": w, "h": h},
                        "text": plate_text,
                        "plate_number": plate_number,
                        "is_valid": is_valid,
                        "image": plate_img_path,
                        "auto_saved": is_valid,
                    }
                )

        return (
            jsonify(
                {
                    "success": True,
                    "original_image": filepath,
                    "plates_detected": len(results),
                    "results": results,
                    "message": f"Se detectaron {len(results)} placa(s)",
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
