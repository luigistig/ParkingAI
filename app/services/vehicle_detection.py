"""
Servicio de detección de vehículos usando YOLOv8
"""

import cv2

from ultralytics import YOLO


class VehicleDetector:
    """Clase para detectar vehículos usando YOLOv8"""

    VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

    def __init__(self):
        """Inicializar detector"""
        self.model = YOLO("yolov8n.pt")

    def detect_vehicles(self, image, conf=0.5):

        results = self.model(image, conf=conf)

        vehicles = []

        for result in results:

            boxes = result.boxes

            for box in boxes:

                cls = int(box.cls)

                if cls in self.VEHICLE_CLASSES:

                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                    conf_score = float(box.conf[0].cpu().numpy())

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

        if bbox:

            x = bbox["x"]
            y = bbox["y"]
            w = bbox["w"]
            h = bbox["h"]

            vehicle_img = image[y : y + h, x : x + w]

        else:

            vehicle_img = image

        avg_color = vehicle_img.mean(axis=0).mean(axis=0)

        avg_color = avg_color[::-1]

        return self._classify_color(avg_color)

    def _classify_color(self, rgb):

        r, g, b = rgb

        total = r + g + b

        if total == 0:
            return "negro"

        r_norm = r / total
        g_norm = g / total
        b_norm = b / total

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

        annotated = image.copy()

        for det in detections:

            x = det["x"]
            y = det["y"]
            w = det["w"]
            h = det["h"]

            label = f"{det['class']} {det['conf']:.2f}"

            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)

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
