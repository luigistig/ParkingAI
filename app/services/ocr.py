"""
Servicio de OCR para reconocimiento de caracteres en placas usando EasyOCR
"""

import easyocr
import cv2
import numpy as np
import re


class PlateOCR:
    """Clase para realizar OCR en placas vehiculares usando EasyOCR"""

    # Patrón típico de placas colombianas (ejemplo: ABC-123 o ABC123)
    PLATE_PATTERNS = [
        r"^[A-Z]{3}-?\d{3}$",  # ABC-123 o ABC123 (formato colombiano estándar)
    ]

    def __init__(self, langs=["en"]):
        """Inicializar OCR con EasyOCR"""
        self.reader = easyocr.Reader(langs)

    def extract_text(self, image):
        """
        Extraer texto de una imagen de placa usando múltiples técnicas

        Args:
            image: imagen como array numpy

        Returns:
            texto extraído de la placa
        """
        try:
            texts = []

            # Técnica 1: Preprocesamiento original
            processed1 = self.preprocess_image(image)
            results1 = self.reader.readtext(processed1)
            texts.extend([result[1] for result in results1 if result[2] > 0.1])

            # Técnica 2: Sin preprocesamiento
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            results2 = self.reader.readtext(gray)
            texts.extend([result[1] for result in results2 if result[2] > 0.1])

            # Técnica 3: Threshold adaptativo
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            results3 = self.reader.readtext(thresh)
            texts.extend([result[1] for result in results3 if result[2] > 0.1])

            # Técnica 4: CLAHE para mejorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            results4 = self.reader.readtext(enhanced)
            texts.extend([result[1] for result in results4 if result[2] > 0.1])

            # Técnica 5: Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            results5 = self.reader.readtext(morph)
            texts.extend([result[1] for result in results5 if result[2] > 0.1])

            # Técnica 6: Bilateral filter for noise reduction
            bilateral = cv2.bilateralFilter(gray, 11, 17, 17)
            results6 = self.reader.readtext(bilateral)
            texts.extend([result[1] for result in results6 if result[2] > 0.1])

            if not texts:
                return ""

            # Combinar textos y limpiar
            full_text = " ".join(texts).upper().replace(" ", "")

            # Validar contra patrones de placa
            for pattern in self.PLATE_PATTERNS:
                match = re.match(pattern, full_text)
                if match:
                    return match.group()

            # Si no coincide exactamente, intentar encontrar subcadenas que coincidan
            for text in texts:
                text = text.upper().replace(" ", "").strip()
                for pattern in self.PLATE_PATTERNS:
                    match = re.search(pattern, text)
                    if match:
                        return match.group()

            # Si no hay coincidencias, devolver el texto más largo y limpio
            cleaned_texts = [
                t.upper().replace(" ", "").strip() for t in texts if t.strip()
            ]
            return max(cleaned_texts, key=len) if cleaned_texts else ""

        except Exception as e:
            print(f"Error en OCR: {e}")
            return ""

    def extract_plate_number(self, image):
        """
        Extraer número de placa de una imagen

        Args:
            image: imagen de la placa

        Returns:
            número de placa limpio y validado
        """
        # Preprocesar imagen
        processed = self.preprocess_image(image)

        # Extraer texto
        text = self.extract_text(processed)

        # Normalizar
        plate_number = self._normalize_plate(text)

        # Validar formato
        if self._is_valid_plate(plate_number):
            return plate_number

        return None

    def preprocess_image(self, image):
        """
        Preprocesar imagen para mejor OCR

        Args:
            image: imagen de la placa

        Returns:
            imagen preprocesada
        """
        # Convertir a gris
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Aplicar threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def _normalize_plate(self, text):
        """
        Normalizar el número de placa

        Args:
            text: texto a normalizar

        Returns:
            placa normalizada
        """
        # Convertir a mayúsculas
        text = text.upper()

        # Remover caracteres no válidos
        text = re.sub(r"[^A-Z0-9\-]", "", text)

        # Agregar guion si es necesario (XXX-123)
        if len(text) >= 6 and not "-" in text:
            # Detectar patrón y agregar guion
            if text[:3].isalpha() and text[3:].isdigit():
                text = text[:3] + "-" + text[3:]
            elif text[:2].isalpha() and text[2:].isdigit():
                text = text[:2] + "-" + text[2:]

        return text

    def _is_valid_plate(self, plate):
        """
        Validar que la placa tenga un formato válido

        Args:
            plate: número de placa a validar

        Returns:
            True si es válida, False en caso contrario
        """
        if not plate:
            return False

        for pattern in self.PLATE_PATTERNS:
            if re.match(pattern, plate):
                return True

        return False


def extract_plate_text(image):
    """
    Función auxiliar para extraer texto de placa

    Args:
        image: imagen de la placa

    Returns:
        número de placa extraído
    """
    ocr = PlateOCR()
    return ocr.extract_plate_number(image)


def validate_plate_format(plate):
    """
    Validar formato de placa

    Args:
        plate: número de placa a validar

    Returns:
        True si es válida, False en caso contrario
    """
    ocr = PlateOCR()
    return ocr._is_valid_plate(plate)

    def extract_characters(self, image):
        """
        Detectar caracteres en la imagen de forma simple

        Args:
            image: imagen de la placa como array numpy

        Returns:
            lista de caracteres detectados
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Binarización
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Encontrar contornos de caracteres
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filtrar contornos por tamaño
        char_contours = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if 10 < w < 100 and 10 < h < 100:
                char_contours.append((x, y, w, h))

        # Ordenar por posición horizontal
        char_contours.sort(key=lambda c: c[0])

        return char_contours
