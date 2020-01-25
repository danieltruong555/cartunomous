from VideoStream import VideoStream
from Detection import *
import picar
import cv2
import threading
import logging
import argparse
import time
from imutils.video import FPS
import sys

sys.path.insert(0, '/home/pi/SunFounder_PiCar-S/example/')
from SunFounder_Ultrasonic_Avoidance import Ultrasonic_Avoidance


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-d', '--debug', type=int, default=1,
                        help='Displays debugging prompts')
arg_parser.add_argument('-s', '--speed', type=int, default=30,
						help='Sets speed of RC car')
arg_parser.add_argument("-v", '--video', type=int, default=0,
						help='Record a video')
args = vars(arg_parser.parse_args())

fourcc =  cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('demo/demo.avi', fourcc, 30, (320,240))

class Cartunomous(object):

	def __init__(self, debug, video):
		logging.info('Initializing car...')

		picar.setup()

		'''self.camera = PiCamera()
		self.camera.resolution = (320, 240)
		self.camera.framerate = 30
		self.rawCapture = PiRGBArray(self.camera,size=self.camera.resolution)
		time.sleep(0.1) #need time for camera sensor to warm'''
		
		#set up camera
		self.video_stream = VideoStream((320,240), 30, debug)
		threading.Thread(target=self.video_stream.capture).start()
		logging.info('Camera with {0} resolution succesfully deployed'
					 .format(self.video_stream.camera.resolution))
		
		#set up backwheel
		self.back_wheels = picar.back_wheels.Back_Wheels()
		self.back_wheels.speed = 0
		#self.back_wheels.forward_A = self.back_wheels.forward_B = 0
		self.is_driving = False
		logging.info('Back wheels are ready')
		
		#set up frontwheel
		self.front_wheels = picar.front_wheels.Front_Wheels()
		self.front_wheels.turn(90)
		logging.info("Front wheels are ready")
		
		self.current_steering_angle = 90 #90 -> go straight, #91-135 -> turn right, #45-89 -> turn left
		
		#set up ultrasonic sensors
		self.ultrasonic = Ultrasonic_Avoidance.Ultrasonic_Avoidance(channel=20)
		logging.info("Ultrasonic sensor is ready")
		
		logging.info('Car successfully deployed')
		
		self.debug = debug
		
		self.video = video


	#initiates car drive and updates frame
	def drive(self, speed=30):
		time.sleep(2)
		
		self.back_wheels.speed = speed #0 is slowest, 100 is fastest
		self.back_wheels.forward()
		self.is_driving = True
		stop_detected = False
		logging.info("Car is now driving...")
		
		index = 0
		fps = FPS().start()
		try:
			while True:
				frame = self.video_stream.read() #read the frame from video stream
				#distance = self.ultrasonic.get_distance()
				#logging.info("Distance from object: {}".format(distance))
				if (self.ultrasonic.get_distance() <= 10):
					logging.info("Object detected")
					frame, stop_detected = detect_objects(frame) #returns frame and True if stop sign or red light is detected
					if stop_detected and self.is_driving: #if stop sign or red light is detected, stop the car
						self.back_wheels.speed = 0
						self.is_driving = False
						logging.info("Stopping car...")
						time.sleep(3)
					elif not stop_detected and not self.is_driving: #if car is not driving and green light, start driving the car
						self.back_wheels.speed = speed
						self.is_driving = True
						logging.info("Car is now driving again...")

				if self.is_driving:
					frame, new_steering_angle, num_of_lines = detect_lanes(frame, index, self.video)
					index += 1
					if num_of_lines > 0:
						self.current_steering_angle = self.adjust_steering(new_steering_angle, num_of_lines)
						self.front_wheels.turn(self.current_steering_angle)
						logging.info("Current Steering Angle: {}".format(self.current_steering_angle))
				fps.update()	
				if self.debug:
					cv2.imshow('Frame', frame) #display frame on cv2 window
					key = cv2.waitKey(1) & 0xFF
					if fps._numFrames % 100 == 0: #for every 100 frames, check FPS
						fps.stop()
						logging.info('FPS: {:.2f}'.format(fps.fps()))
						fps = FPS().start()
				if self.video:
					out.write(frame)

		except KeyboardInterrupt:
			logging.info('Stopping car and exiting program...')
			self.destroy()

	#called when exiting program; destroys everything
	def destroy(self):
		self.back_wheels.stop()
		self.video_stream.stop()
		self.video_stream.destroy()
		cv2.destroyAllWindows()
		
		
	def adjust_steering(self, steering_angle, num_of_lines):
		max_angle_deviation_two_lines = 6
		max_angle_deviation_one_line = 2
		
		if num_of_lines == 1:
			max_angle_deviation = max_angle_deviation_one_line
		
		else:
			max_angle_deviation = max_angle_deviation_two_lines
		
		angle_deviation = steering_angle - self.current_steering_angle
		if abs(angle_deviation) > max_angle_deviation:
			if angle_deviation < 0:
				adjusted_angle = self.current_steering_angle - max_angle_deviation
			else:
				adjusted_angle = self.current_steering_angle + max_angle_deviation
			return adjusted_angle
		return steering_angle

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG, format='%(levelname)-5s:%(asctime)s: %(message)s')
	car = Cartunomous(args['debug'], args['video'])
	car.drive(args['speed'])


