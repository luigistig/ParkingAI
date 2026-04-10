"""
Servicio de detección de placas vehiculares usando OpenCV
"""

import cv2
import numpy as np


class PlateDetector:
    """Clase para detectar placas vehiculares en imágenes"""

    def __init__(self):
        """Inicializar el detector de placas"""
        pass

    def detect_plates(self, image, conf=0.1):
        """
        Detectar placas en una imagen usando múltiples técnicas

        Args:
            image: imagen como array numpy
            conf: confianza mínima

        Returns:
            lista de diccionarios con coordenadas y confianza
        """
        plates = []

        # Técnica 1: Detección por contornos (método original mejorado)
        plates.extend(self._detect_by_contours(image, conf))

        # Técnica 2: Detección por morphología
        plates.extend(self._detect_by_morphology(image, conf))

        # Técnica 3: Detección en diferentes escalas
        plates.extend(self._detect_multiscale(image, conf))

        # Filtrar duplicados y ordenar por confianza
        plates = self._filter_duplicates(plates)

        return plates

    def _detect_by_contours(self, image, conf):
        """Detección por contornos mejorada"""
        # Convertir a gris y detectar bordes
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blur, 50, 150)

        # Dilatar para conectar componentes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Encontrar contornos
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        plates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h) if h > 0 else 0
            area = w * h
            solidity = cv2.contourArea(contour) / (w * h) if w * h > 0 else 0

            # Filtros mejorados para placas (más permisivos)
            if (
                1.5 < aspect_ratio < 10  # Relación de aspecto más amplia
                and 200 < area < 200000  # Área más amplia
                and 0.2 < solidity < 1.0  # Solidez más permisiva
                and w > 40  # Ancho mínimo reducido
                and h > 10  # Alto mínimo reducido
            ):

                # Calcular confianza basada en características
                conf_score = min(0.8, solidity * 0.5 + (area / 50000) * 0.3 + 0.2)

                if conf_score >= conf:
                    plates.append({"x": x, "y": y, "w": w, "h": h, "conf": conf_score})

        return plates

    def _detect_by_morphology(self, image, conf):
        """Detección usando operaciones morfológicas"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Aplicar diferentes thresholds
        plates = []
        for thresh_val in [100, 120, 140]:
            _, thresh = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)

            # Operaciones morfológicas
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

            # Encontrar contornos
            contours, _ = cv2.findContours(
                morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h) if h > 0 else 0
                area = w * h

                if 1.5 < aspect_ratio < 10 and 300 < area < 150000:
                    conf_score = 0.4  # Confianza base más baja
                    if conf_score >= conf:
                        plates.append(
                            {"x": x, "y": y, "w": w, "h": h, "conf": conf_score}
                        )

        return plates

    def _detect_multiscale(self, image, conf):
        """Detección en diferentes escalas"""
        plates = []
        scales = [0.8, 1.0, 1.2]

        for scale in scales:
            if scale != 1.0:
                width = int(image.shape[1] * scale)
                height = int(image.shape[0] * scale)
                resized = cv2.resize(image, (width, height))
            else:
                resized = image

            # Usar detección por contornos en la imagen escalada
            scaled_plates = self._detect_by_contours(resized, conf * 0.8)

            # Re-escalar coordenadas de vuelta
            if scale != 1.0:
                scale_factor = 1.0 / scale
                for plate in scaled_plates:
                    plate["x"] = int(plate["x"] * scale_factor)
                    plate["y"] = int(plate["y"] * scale_factor)
                    plate["w"] = int(plate["w"] * scale_factor)
                    plate["h"] = int(plate["h"] * scale_factor)
                    plate["conf"] *= 0.9  # Penalizar detecciones escaladas

            plates.extend(scaled_plates)

        return plates

    def _filter_duplicates(self, plates, iou_threshold=0.3):
        """Filtrar detecciones duplicadas usando IoU"""
        if not plates:
            return plates

        # Ordenar por confianza descendente
        plates.sort(key=lambda x: x["conf"], reverse=True)

        filtered = []
        for plate in plates:
            is_duplicate = False
            for existing in filtered:
                if self._calculate_iou(plate, existing) > iou_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append(plate)

        return filtered

    def _calculate_iou(self, box1, box2):
        """Calcular Intersection over Union entre dos bounding boxes"""
        x1 = max(box1["x"], box2["x"])
        y1 = max(box1["y"], box2["y"])
        x2 = min(box1["x"] + box1["w"], box2["x"] + box2["w"])
        y2 = min(box1["y"] + box1["h"], box2["y"] + box2["h"])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = box1["w"] * box1["h"]
        area2 = box2["w"] * box2["h"]
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    def crop_plate(self, image, plate_coords):
        """
        Recortar la placa de la imagen

        Args:
            image: imagen original
            plate_coords: diccionario con x, y, w, h

        Returns:
            imagen recortada de la placa
        """
        x, y, w, h = (
            plate_coords["x"],
            plate_coords["y"],
            plate_coords["w"],
            plate_coords["h"],
        )
        return image[y : y + h, x : x + w]
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        edges = cv2.dilate(edges, kernel, iterations=2)
        edges = cv2.erode(edges, kernel, iterations=2)

        # 3. Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        plates = []

        # Filtrar contornos por características de placa
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Las placas típicamente tienen cierta relación de aspecto
            aspect_ratio = float(w) / h if h > 0 else 0

            # Filtros para identificar placas
            if (
                h > 20
                and w > 60  # Tamaño mínimo
                and 2 < aspect_ratio < 6  # Relación de aspecto típica de placas
                and cv2.contourArea(contour) > 500
            ):  # Área mínima

                plates.append((x, y, w, h))

        # Si usamos cascade classifier (si está disponible)
        if self.cascade is not None:
            cascade_plates = self.cascade.detectMultiScale(gray, 1.1, 4)
            plates.extend(cascade_plates)

        # Combinar y eliminar duplicados
        plates = self._remove_duplicates(plates)

        # Dibujar en la imagen si se solicita
        if output_path:
            img_marked = img.copy()
            for x, y, w, h in plates:
                cv2.rectangle(img_marked, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imwrite(output_path, img_marked)

        return plates

    def extract_plate_roi(self, image_path, x, y, w, h, padding=10):
        """
        Extraer la región de interés (ROI) de la placa

        Args:
            image_path: ruta a la imagen
            x, y, w, h: coordenadas de la placa
            padding: píxeles de padding alrededor de la placa

        Returns:
            imagen de la placa extraída
        """
        img = cv2.imread(image_path)
        if img is None:
            return None

        # Aplicar padding
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2 * padding)
        h = min(img.shape[0] - y, h + 2 * padding)

        # Extraer ROI
        plate_roi = img[y : y + h, x : x + w]

        return plate_roi

    def preprocess_plate(self, plate_image):
        """
        Preprocesar la imagen de la placa para mejorar OCR

        Args:
            plate_image: imagen de la placa (OpenCV format)

        Returns:
            imagen preprocesada
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)

        # Aplicar CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Binarización adaptativa
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Remover ruido
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)

        return cleaned

    def _remove_duplicates(self, plates, threshold=50):
        """
        Eliminar detecciones duplicadas (muy cercanas)

        Args:
            plates: lista de tuplas (x, y, w, h)
            threshold: distancia mínima entre placas

        Returns:
            lista filtrada de placas
        """
        if not plates:
            return []

        plates = list(plates)
        filtered = []

        while plates:
            current = plates.pop(0)
            filtered.append(current)

            # Remover placas muy cercanas
            plates = [
                p
                for p in plates
                if abs(p[0] - current[0]) > threshold
                or abs(p[1] - current[1]) > threshold
            ]

        return filtered


def detect_vehicle_plates(image_path):
    """
    Función auxiliar para detectar placas en una imagen

    Args:
        image_path: ruta a la imagen del vehículo

    Returns:
        lista de placas detectadas con sus coordenadas
    """
    detector = PlateDetector()
    return detector.detect_plates(image_path)


def extract_plate_image(image_path, x, y, w, h):
    """
    Función auxiliar para extraer la región de la placa

    Args:
        image_path: ruta a la imagen
        x, y, w, h: coordenadas de la placa

    Returns:
        imagen de la placa como array numpy
    """
    detector = PlateDetector()
    return detector.extract_plate_roi(image_path, x, y, w, h)
