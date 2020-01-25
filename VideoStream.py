from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import logging


class VideoStream:
	def __init__(self, resolution=(320, 240), framerate=30, debug = False):
		# initialize the camera and stream
		self.camera = PiCamera()
		self.camera.resolution = resolution
		self.camera.rotation =180
		self.camera.framerate = framerate
		self.rawCapture = PiRGBArray(self.camera, size=resolution)
		self.stream = self.camera.capture_continuous(self.rawCapture,
												 format="bgr", use_video_port=True)
		time.sleep(0.1) #time needed to warm up camera sensor
		self.frame = None		
		self.stop_capturing = False

		self.debug = debug


	#captures and updates frames
	def capture(self):
		for f in self.stream:
			self.frame = f.array
			self.rawCapture.truncate(0)
			if self.stop_capturing:
				self.destroy()
				return

	#called when program is exiting; destroys and closes everything
	def destroy(self):
		self.stream.close()
		self.rawCapture.close()
		self.camera.close()


	def read(self):
		return self.frame


	def stop(self):
		self.stop_capturing = True
