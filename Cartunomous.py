
# from SunFounder_Ultrasonic_Avoidance import Ultrasonic_Avoidance
from TrafficSignDetector import TrafficSignDetector
from LaneNavigator import LaneNavigator
from VideoStream import VideoStream
# from Detection import *
import picar
import cv2
import threading
import logging
import argparse
import time
from imutils.video import FPS
import sys
import os


sys.path.insert(0, '/home/pi/SunFounder_PiCar-S/example/')


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-d', '--debug', type=int, default=1,
                        help='Displays debugging prompts')
arg_parser.add_argument('-s', '--speed', type=int, default=30,
                        help='Sets speed of RC car')
arg_parser.add_argument("-v", '--video', type=str, default="",
                        help='Sets the path to where the video will be saved')
arg_parser.add_argument("-lp", '--lanepath', type=str, default='models/lane_navigation_check.h5',
                        help='Sets the path of the lane navigation model location')
arg_parser.add_argument("-sp", '--signpath', type=str, default='models/road_signs_quantized_edgetpu.tflite',
                        help='Sets the path of the traffic sign model location')
arg_parser.add_argument("-l", '--label', type=str, default='models/road_signs_labels.txt',
                        help='Sets the path of the traffic sign labels location')
arg_parser.add_argument("-ds", '--detect', type=int, default=1,
                        help='Turns on/off traffic sign detector')
arg_parser.add_argument("-ln", '--lane', type=int, default=1,
                        help='Turns on/off lane navigator')

args = vars(arg_parser.parse_args())

demo_dir = "demo"
if not os.path.exists(demo_dir):
    os.mkdir(demo_dir)

video_name = "{}.avi".format(args["video"])
demo_path = os.path.join(demo_dir, video_name)


if os.path.exists(demo_path):
    print("Deleting video found in {}...".format(demo_path))
    os.remove(demo_path)

if args["video"]:
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(demo_path, fourcc, 20, (320, 240))

traffic_signs = {"speedLimit25": 25,
                 "speedLimit35": 35, "speedLimit45": 45, "stop": 0}


class Cartunomous(object):

    def __init__(self, debug, detect_signs, lane_navigate, lane_path,
                 sign_path, label_path, video):
        logging.info('Initializing car...')

        picar.setup()

        # set up camera
        self.video_stream = VideoStream((320, 240), 30, debug)
        threading.Thread(target=self.video_stream.capture).start()
        logging.info('Camera with {0} resolution succesfully deployed'
                     .format(self.video_stream.camera.resolution))

        # set up backwheel
        self.back_wheels = picar.back_wheels.Back_Wheels()
        self.back_wheels.speed = 0
        # self.back_wheels.forward_A = self.back_wheels.forward_B = 0
        self.is_driving = False
        logging.info('Back wheels are ready')

        # set up frontwheel
        self.front_wheels = picar.front_wheels.Front_Wheels()
        self.front_wheels.turn(90)
        logging.info("Front wheels are ready")

        # 90 -> go straight, #91-135 -> turn right, #45-89 -> turn left
        self.current_steering_angle = 90
        self.current_speed = 0

        self.stop_detected = False

        # set up ultrasonic sensors
        # self.ultrasonic = Ultrasonic_Avoidance.Ultrasonic_Avoidance(channel=20)
        # logging.info("Ultrasonic sensor is ready")

        self.debug = debug

        self.video = video

        # initialize the lane navigation system
        if(lane_navigate):
            self.lane_navigator = LaneNavigator(lane_path)
            logging.info('Lane Navigator successfully deployed')

        # initialize the traffic sign detector system; only allow scores above 0.5 to be detected
        if(detect_signs):
            self.sign_detector = TrafficSignDetector(
                sign_path, label_path, min_confidence=0.70)
            logging.info('Traffic Sign Detector successfully deployed')

        logging.info('Car initialization complete')

    # initiates car drive and updates frame
    def drive(self, speed):
        time.sleep(3)

        self.current_speed = speed
        self.back_wheels.speed = self.current_speed  # 0 is slowest, 100 is fastest
        self.back_wheels.forward()
        self.is_driving = True
        logging.info("Car is now driving...")

        fps = FPS().start()
        try:
            while True:
                frame = self.video_stream.read()  # read the frame from video stream
                mask = np.zeros_like(frame)
                if args['detect']:
                    mask = np.zeros_like(frame)
                    detected_signs, mask = self.sign_detector.detect_signs(
                        frame)

                    if detected_signs:
                        self.obey_signs(detected_signs)

                if self.is_driving and args['lane']:
                    # steering_angle, frame = self.lane_navigator.predict_steering_angle(
                    #     frame)
                    steering_angle = self.lane_navigator.predict_steering_angle(
                        frame)
                    logging.info(
                        "New steering angle is {}".format(steering_angle))
                    self.front_wheels.turn(steering_angle)

                processed_frame = cv2.addWeighted(
                    frame, 0.8, mask, 1, 0)
                if self.debug:
                    # display frame on cv2 window
                    cv2.imshow('Frame', processed_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if fps._numFrames % 100 == 0:  # for every 100 frames, check FPS
                        fps.stop()
                        logging.info('FPS: {:.2f}'.format(fps.fps()))
                        fps = FPS().start()
                fps.update()

                # write the frame into the video
                if self.video:
                    out.write(processed_frame)

        except KeyboardInterrupt:
            logging.info('Stopping car and exiting program...')
            self.destroy()

    # function to force the RC car to respond to traffic signs accordingly
    def obey_signs(self, signs):
        for sign in signs:
            # extract the label or sign class
            label = self.sign_detector.labels[sign.label_id]

            if label == "stop" and not self.stop_detected:
                logging.info("Stop sign detected. Stopping car...")
                self.back_wheels.speed = traffic_signs["stop"]
                self.is_driving = False
                self.stop_detected = True
                # time.sleep(5)
                # logging.info("Car now driving again...")
                # self.back_wheels.speed = self.current_speed
                threading.Timer(5.0, self.resume_driving).start()

            if "speedLimit" in label:
                logging.info("{} detected. Changing speed to {}".format(
                    label, traffic_signs[label]))
                self.current_speed = traffic_signs[label]
                self.back_wheels.speed = self.current_speed

    #function to be called after stopping at a stop sign
    def resume_driving(self):
        self.is_driving = True
        self.back_wheels.speed = self.current_speed
        logging.info("Car is now driving again")
        start = time.time()
        # 5 sec cool-down for next stop
        while time.time() - start < 5:
            pass
        self.stop_detected = False
    
    # called when exiting program; destroys everything
    def destroy(self):
        self.back_wheels.stop()
        self.video_stream.stop()
        self.video_stream.destroy()
        cv2.destroyAllWindows()

    # def adjust_steering(self, steering_angle, num_of_lines):
    #     max_angle_deviation_two_lines = 6
    #     max_angle_deviation_one_line = 2

    #     if num_of_lines == 1:
    #         max_angle_deviation = max_angle_deviation_one_line

    #     else:
    #         max_angle_deviation = max_angle_deviation_two_lines

    #     angle_deviation = steering_angle - self.current_steering_angle
    #     if abs(angle_deviation) > max_angle_deviation:
    #         if angle_deviation < 0:
    #             adjusted_angle = self.current_steering_angle - max_angle_deviation
    #         else:
    #             adjusted_angle = self.current_steering_angle + max_angle_deviation
    #         return adjusted_angle
    #     return steering_angle


if __name__ == '__main__':
    if(args['debug']):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)-5s:%(asctime)s: %(message)s')
    car = Cartunomous(args['debug'], args['detect'], args['lane'], args['lanepath'],
                      args['signpath'], args['label'], args['video'])
    car.drive(args['speed'])
