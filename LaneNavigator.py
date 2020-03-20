import cv2
import numpy as np
from keras.models import load_model
import math


class LaneNavigator(object):
    def __init__(self, model_path='models/lane_navigation_final.h5'):
        self.model = load_model(model_path)

    def predict_steering_angle(self, image):
        preprocessed_image = preprocess_image(image)
        preprocessed_image = np.asarray([preprocessed_image])
        steering_angle = self.model.predict(preprocessed_image)[0]
        # image = display_heading_line(image, steering_angle)
        return int(steering_angle)


def preprocess_image(image):
    height = image.shape[0]
    image = image[int(0.6*height):, :, :]
    image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    image = cv2.resize(image, (200, 66))
    image = image/255
    return image


# def display_heading_line(image, steering_angle):
#     heading_image = np.zeros_like(image)
#     height, width, _ = image.shape

#     steering_angle_radian = steering_angle / 180.0 * math.pi
#     x1 = int(width / 2)
#     y1 = height
#     x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
#     y2 = int(height / 2)

#     cv2.line(heading_image, (x1, y1), (x2, y2), (0, 255, 255), 5)
#     heading_image = cv2.addWeighted(image, 0.8, heading_image, 1, 1)

#     return heading_image
