"""
Servicio de cámara y captura de imágenes
"""

import cv2
import os
from datetime import datetime
import uuid
import time

# Variable global para mantener instancia única de cámara
_camera_instance = None
_camera_lock = None


class CameraService:
    """Servicio para capturar imágenes de la cámara"""

    def __init__(self, camera_index=0):
        """
        Inicializar servicio de cámara

        Args:
            camera_index: índice de la cámara (0 para la cámara predeterminada)
        """
        self.camera_index = camera_index
        self.camera = None

    def open_camera(self):
        """Abrir conexión con la cámara"""
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                return False

            # Configurar propiedades de la cámara
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.camera.set(cv2.CAP_PROP_FPS, 30)

            return True
        except Exception as e:
            print(f"Error al abrir cámara: {e}")
            return False

    def close_camera(self):
        """Cerrar conexión con la cámara"""
        if self.camera:
            self.camera.release()
            self.camera = None

    def capture_frame(self):
        """
        Capturar un fotograma de la cámara

        Returns:
            tupla (success, frame) donde frame es la imagen capturada
        """
        if not self.camera or not self.camera.isOpened():
            return False, None

        try:
            ret, frame = self.camera.read()
            if not ret:
                # Si falla, intentar reiniciar la cámara
                self.reset_camera()
                return False, None
            return ret, frame
        except Exception as e:
            print(f"Error al capturar fotograma: {e}")
            self.reset_camera()
            return False, None

    def reset_camera(self):
        """Reiniciar la conexión de cámara"""
        try:
            if self.camera:
                self.camera.release()
        except:
            pass
        self.camera = None
        time.sleep(0.5)  # Esperar medio segundo antes de reconectar

    def capture_and_save(self, output_folder):
        """
        Capturar una imagen y guardarla

        Args:
            output_folder: carpeta donde guardar la imagen

        Returns:
            tupla (success, filepath) con ruta del archivo o None
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # Si la cámara no está abierta, abrirla
                if not self.camera or not self.camera.isOpened():
                    if not self.open_camera():
                        print(f"Intento {attempt + 1}: No se pudo abrir la cámara")
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        continue

                # Capturar múltiples frames para asegurar una buena imagen
                frame = None
                for frame_attempt in range(5):
                    ret, frame = self.capture_frame()
                    if ret and frame is not None:
                        break
                    time.sleep(0.1)  # Pausa entre intentos

                if ret and frame is not None:
                    # Crear nombre único para la imagen
                    filename = f"vehicle_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    filepath = os.path.join(output_folder, filename)

                    # Guardar la imagen
                    success = cv2.imwrite(filepath, frame)
                    if success:
                        print(f"Imagen guardada exitosamente: {filepath}")
                        return True, filepath

            except Exception as e:
                print(f"Intento {attempt + 1} - Error al capturar: {e}")
                self.reset_camera()
                if attempt < max_retries - 1:
                    time.sleep(1)

        print("No se pudo capturar la imagen después de múltiples intentos")
        return False, None

    def get_frame_for_display(self):
        """
        Obtener fotograma para mostrar en tiempo real

        Returns:
            fotograma codificado en JPG
        """
        ret, frame = self.capture_frame()
        if not ret:
            return None

        # Codificar frame a JPEG
        _, buffer = cv2.imencode(".jpg", frame)
        return buffer.tobytes()

    def detect_motion(self, threshold=30):
        """
        Detectar movimiento entre fotogramas consecutivos

        Args:
            threshold: umbral de diferencia para detectar movimiento

        Returns:
            True si hay movimiento detectado
        """
        ret1, frame1 = self.capture_frame()
        ret2, frame2 = self.capture_frame()

        if not ret1 or not ret2:
            return False

        # Convertir a escala de grises
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        # Calcular diferencia
        diff = cv2.absdiff(gray1, gray2)

        # Aplicar umbral
        _, diff_binary = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

        # Contar píxeles con movimiento
        motion_pixels = cv2.countNonZero(diff_binary)

        return motion_pixels > 1000  # Si hay más de 1000 píxeles con movimiento


class MockCamera:
    """Cámara simulada para pruebas sin hardware"""

    def __init__(self, test_image_path=None):
        """
        Inicializar cámara simulada

        Args:
            test_image_path: ruta a imagen de prueba
        """
        self.test_image_path = test_image_path
        self.image = None

        if test_image_path and os.path.exists(test_image_path):
            self.image = cv2.imread(test_image_path)

    def open_camera(self):
        """Simular apertura de cámara"""
        return True

    def close_camera(self):
        """Simular cierre de cámara"""
        pass

    def capture_frame(self):
        """Capturar fotograma simulado"""
        if self.image is not None:
            return True, self.image.copy()

        # Crear imagen de prueba si no hay imagen
        test_image = self._create_test_image()
        return True, test_image

    def capture_and_save(self, output_folder):
        """Capturar y guardar imagen simulada"""
        ret, frame = self.capture_frame()
        if not ret:
            return False, None

        try:
            filename = f"test_vehicle_{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(output_folder, filename)
            cv2.imwrite(filepath, frame)
            return True, filepath
        except Exception as e:
            print(f"Error: {e}")
            return False, None

    def _create_test_image(self):
        """Crear imagen de prueba"""
        # Crear imagen con texto
        image = (
            cv2.imread(self.test_image_path)
            if self.test_image_path
            else cv2.imread(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "static",
                    "uploads",
                    "test_vehicle.jpg",
                )
            )
        )

        if image is None:
            # Crear imagen gris si no hay archivo
            image = (
                cv2.imread("C:\\Windows\\win.ini")
                or cv2.imread("/usr/share/pixmaps/debian-logo.png")
                or np.ones((720, 1280, 3), dtype=np.uint8) * 200
            )

        return image


def get_camera_service(use_mock=False):
    """
    Obtener servicio de cámara (instancia única)

    Args:
        use_mock: usar cámara simulada para pruebas

    Returns:
        instancia de CameraService o MockCamera
    """
    global _camera_instance

    if use_mock:
        return MockCamera()

    # Retornar instancia única de cámara
    if _camera_instance is None:
        _camera_instance = CameraService()

    return _camera_instance


def release_camera_service():
    """Liberar instancia única de cámara"""
    global _camera_instance
    if _camera_instance:
        try:
            _camera_instance.close_camera()
        except:
            pass
        _camera_instance = None
