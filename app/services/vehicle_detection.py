"""
Servicio de detección de vehículos usando YOLOv8
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os


class VehicleDetector:
    """Clase para detectar vehículos usando YOLOv8"""

    # Clases de vehículos en COCO dataset
    VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

    def __init__(self):
        """Inicializar detector de vehículos"""
        self.model = YOLO("yolov8n.pt")  # Modelo preentrenado con COCO

    def detect_vehicles(self, image, conf=0.5):
        """
        Detectar vehículos en una imagen

        Args:
            image: imagen como array numpy
            conf: confianza mínima

        Returns:
            lista de diccionarios con detecciones
        """
        results = self.model(image, conf=conf)

        vehicles = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls)
                if cls in self.VEHICLE_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf_score = box.conf[0].cpu().numpy()
                    vehicles.append(
                        {
                            "class": self.VEHICLE_CLASSES[cls],
                            "x": int(x1),
                            "y": int(y1),
                            "w": int(x2 - x1),
                            "h": int(y2 - y1),
                            "conf": conf_score,
                        }
                    )

        return vehicles

    def get_dominant_color(self, image, bbox=None):
        """
        Obtener el color dominante de un vehículo

        Args:
            image: imagen completa
            bbox: bounding box del vehículo (x, y, w, h)

        Returns:
            color dominante como string
        """
        if bbox:
            x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
            vehicle_img = image[y : y + h, x : x + w]
        else:
            vehicle_img = image

        # Calcular promedio de color
        avg_color = vehicle_img.mean(axis=0).mean(axis=0)

        # Convertir BGR a RGB
        avg_color = avg_color[::-1]

        # Clasificar color
        return self._classify_color(avg_color)

    def _classify_color(self, rgb):
        """
        Clasificar color basado en valores RGB

        Args:
            rgb: tupla (r, g, b)

        Returns:
            nombre del color
        """
        r, g, b = rgb

        # Normalizar
        total = r + g + b
        if total == 0:
            return "negro"

        r_norm = r / total
        g_norm = g / total
        b_norm = b / total

        # Lógica simple de clasificación
        if r_norm > 0.4 and g_norm > 0.4 and b_norm > 0.4:
            return "blanco"
        elif r_norm > 0.6:
            return "rojo"
        elif g_norm > 0.6:
            return "verde"
        elif b_norm > 0.6:
            return "azul"
        elif r_norm > 0.3 and g_norm > 0.3:
            return "amarillo"
        elif max(r_norm, g_norm, b_norm) < 0.4:
            return "negro"
        else:
            return "gris"

    def annotate_image(self, image, detections):
        """
        Anotar imagen con detecciones

        Args:
            image: imagen original
            detections: lista de detecciones

        Returns:
            imagen anotada
        """
        annotated = image.copy()

        for det in detections:
            x, y, w, h = det["x"], det["y"], det["w"], det["h"]
            label = f"{det['class']} {det['conf']:.2f}"

            # Dibujar bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Dibujar label
            cv2.putText(
                annotated,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        return annotated
