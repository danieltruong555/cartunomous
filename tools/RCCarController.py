import picar
import threading
import cv2
import argparse
import time
import os
import logging
import getch
import system
from VideoStream import VideoStream


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-s", '--speed', type=int, default=40,
                        help='Sets the max speed of RC car')
arg_parser.add_argument("-v", '--out', type=str, default="training",
                        help='Sets the output file name')
args = vars(arg_parser.parse_args())

MAX_SPEED = args['speed']

training_path = "training_data"
if not os.path.exists(training_path):
    os.makedirs(training_path)

data_path = os.path.join(training_path, "{}_images".format(args['out']))
if not os.path.exists(data_path):
    os.makedirs(data_path)

if os.path.exists(data_path):
    for file in os.listdir(data_path):
        os.remove(os.path.join(data_path, file))


class RCCarController(object):
    def __init__(self, outpath):
        logging.info('Initializing car')

        picar.setup()

        # set up camera
        self.video_stream = VideoStream((320, 240), 30, 0)
        threading.Thread(
            target=self.video_stream.capture).start()

        # set up backwheel
        self.back_wheels = picar.back_wheels.Back_Wheels()
        self.back_wheels.speed = 0

        # set up frontwheel
        self.front_wheels = picar.front_wheels.Front_Wheels()
        self.front_wheels.turn(90)

        self.steering_angle = 90
        self.speed = 0

        self.outpath = outpath
        logging.info('Saving images into {}'.format(self.outpath))

        logging.info('Car successfully initialized')

    def drive(self):
        time.sleep(1)
        self.speed = 40
        self.back_wheels.speed = self.speed

        self.back_wheels.forward()
        logging.info("Car is now driving...")

        i = 1
        try:
            while True:
                frame = self.video_stream.read()  # read the frame from video stream
                char = getch.getch()
                if char == "w":
                    self.speed += 1
                    if(self.speed > MAX_SPEED):
                        self.speed = MAX_SPEED
                    self.back_wheels.speed = self.speed
                    logging.info("Speed is now {}".format(self.speed))
                if char == "s":
                    self.speed -= 1
                    if(self.speed < 0):
                        self.speed = 0
                    self.back_wheels.speed = self.speed
                    logging.info("Speed is now {}".format(self.speed))
                if char == "a":
                    self.steering_angle -= 1
                    if(self.steering_angle < 45):
                        self.steering_angle = 45
                    self.front_wheels.turn(self.steering_angle)
                    logging.info("Steering angle is now {}".format(
                        self.steering_angle))
                if char == "d":
                    self.steering_angle += 1
                    if(self.steering_angle > 135):
                        self.steering_angle = 135
                    self.front_wheels.turn(self.steering_angle)
                    logging.info("Steering angle is now {}".format(
                        self.steering_angle))
                filename = os.path.join(self.outpath, "{}_image{}_{}.jpg".format(
                    args['out'], i, self.steering_angle))
                cv2.imwrite(filename, frame)
                i += 1

        except KeyboardInterrupt:
            logging.info('Stopping car and exiting program...')
            self.destroy()

    # called when exiting program; destroys everything
    def destroy(self):
        self.back_wheels.stop()
        self.video_stream.stop()
        self.video_stream.destroy()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-5s:%(asctime)s: %(message)s')
    car = RCCarController(data_path)
    car.drive()
