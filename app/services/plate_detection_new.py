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

    def detect_plates(self, image, conf=0.5):
        """
        Detectar placas en una imagen usando contornos OpenCV

        Args:
            image: imagen como array numpy
            conf: confianza mínima

        Returns:
            lista de diccionarios con coordenadas y confianza
        """
        # Convertir a gris y detectar bordes
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 100, 200)

        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        plates = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            area = w * h

            # Filtro básico para posibles placas (rectángulos con ratio ~2-8, área razonable)
            if 2 < aspect_ratio < 8 and 1000 < area < 100000:
                plates.append(
                    {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h,
                        "conf": 0.5,  # Confianza fija por ahora
                    }
                )

        return plates

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
