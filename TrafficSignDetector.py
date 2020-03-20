import cv2
import numpy as np
from edgetpu.detection.engine import DetectionEngine
from PIL import Image


class_colors = {"stop": (0, 255, 0),
                "speedLimit25": (0, 0, 255),
                "speedLimit35": (255, 0, 255),
                "speedLimit45": (0, 255, 255)}


class TrafficSignDetector(object):
    def __init__(self, model_path="models/road_signs_quantized_edgetpu.tflite",
                 label_path="models/road_signs_labels.txt", min_confidence=0.5):
        self.labels = {}

        for row in open(label_path):
            (classID, label) = row.strip().split(maxsplit=1)
            self.labels[int(classID)] = label.strip()

        self.model = DetectionEngine(model_path)

        self.min_confidence = min_confidence

    def detect_signs(self, image):
        mask = np.zeros_like(image)

        image_RGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_RGB = Image.fromarray(image_RGB)

        signs = self.model.detect_with_image(
            image_RGB, threshold=self.min_confidence, keep_aspect_ratio=True, relative_coord=False)

        # loop over all detected objects
        for sign in signs:
            # extract the bounding box and label
            box = sign.bounding_box.flatten().astype("int")
            (startX, startY, endX, endY) = box
            label = self.labels[sign.label_id]

            # draw the rectangle from bounding box coord
            cv2.rectangle(mask, (startX, startY), (endX, endY),
                          class_colors[label], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            score = "{}: {:.2f}%".format(label, sign.score * 100)
            cv2.putText(mask, score, (startX, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, class_colors[label], 2)

        return signs, mask
