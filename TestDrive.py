sys.path.insert(0, '/home/pi/SunFounder_PiCar-S/example/')
from SunFounder_Ultrasonic_Avoidance import Ultrasonic_Avoidance
from picar import front_wheels
from picar import back_wheels
import time
import picar
import random
picar.setup()

ua = Ultrasonic_Avoidance.Ultrasonic_Avoidance(20)
fw = front_wheels.Front_Wheels(db='config')
bw = back_wheels.Back_Wheels(db='config')

forward_speed = 70
backward_speed = 30

back_distance = 10

def start_avoidance():
	print('start_avoidance')
	
	while True:
		distance = ua.get_distance()
		print("distance: %scm" % distance)
		
		if distance < back_distance:
		    stop()
		    bw.backward()
		    bw.speed = backward_speed
		    time.sleep(1)
		    
		else:
		    fw.turn_straight()
		    bw.forward()
		    bw.speed = forward_speed
		 
def stop():
	bw.stop()
	fw.turn_straight()

if __name__ == '__main__':
	try:
		start_avoidance()
	except KeyboardInterrupt:
		stop()

