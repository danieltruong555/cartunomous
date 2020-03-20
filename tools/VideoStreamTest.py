from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.rotation = 180
camera.resolution = (320, 240)


sigma = 3

camera.start_preview(fullscreen = False, window = (100,100, 800, 800))
while True:
    sleep(1)
    #camera.capture('/home/pi/Desktop/TestRun1/image%s_%s.jpg' % (i, sigma))
camera.stop_preview()
