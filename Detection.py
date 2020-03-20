import numpy as np
import cv2
import logging
import math


def detect_objects(frame):
	threshold = 120

	#define cascade classifiers
	traffic_light_cascade = cv2.CascadeClassifier('classifiers/cascade_traffic_light_new.xml')
	#stop_sign_cascade = cv2.CascadeClassifier('classifiers/cascade_stop_sign.xml')

	#convert to grayscale
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	#stop sign detection
	'''stop_signs = stop_sign_cascade.detectMultiScale(gray, minNeighbors=10, minSize= (30, 30))
	
	for (x, y,  w, h) in stop_signs:
		logging.info("Stop sign detected. Stop.")
		cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
		cv2.putText(frame, 'Stop', org=(x, y), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 0, 255), thickness=2)
		return frame, True'''
	
	#traffic light detection
	traffic_lights = traffic_light_cascade.detectMultiScale(gray, minNeighbors=0)

	for (x, y, w, h) in traffic_lights:
		roi = gray[y: y + h, x+10: x + w -10] #crop grayscale image to only contain traffic light
		mask = cv2.blur(roi, (10, 10))  # reduce noise by averaging pixels
		minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(mask)  # find the location of max and min value pixel
		if (maxVal - minVal) > threshold:
			if maxLoc[1] <= h/3:  # if max pixel value is at the top third height of image -> red light
				logging.info("Red light detected. Stop.")
				#print(maxVal - minVal)
				cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 0), 2)
				cv2.putText(frame, 'red', org=(x, y), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 0, 255), thickness=2)
				return frame, True
			elif maxLoc[1] >= 2* h/3:  # if max pixel value is at 2/3  height of image -> green light
				logging.info("Green light detected. Go.")
				#print(maxVal - minVal)
				cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 0), 2)
				cv2.putText(frame, 'green', org=(x, y), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7, color=(0, 255, 0), thickness=2)
				return frame, False
			else:
				logging.info("No light detected...")
				continue

	return frame, False

def detect_lanes(frame, index):
	hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
	#cv2.imshow("hsv", hsv_image)
	

	lower_blue = np.array([2, 50, 50])
	upper_blue = np.array([6, 180, 255])
	hsv_mask = cv2.inRange(hsv_image, lower_blue, upper_blue)
	

	cv2.imshow("hsv_mask", hsv_mask)

	# edge detection
	#denoise = cv2.GaussianBlur(hsv_mask, (5, 5), 0)  # blurs and reduces noise
	edge = cv2.Canny(hsv_mask, 200, 400)  # returns edge detected image(white=edge, black=background)
	cv2.imshow("canny", edge)


	height, width = edge.shape[:2]

	# define ROI
	polygon = np.array([[(0, height/2),  # mid left
						(width, height/2),  # mid left
						(width, height), #bottom right
						(0, height)]], np.int32)  # bottom left
	mask = np.zeros_like(edge)  # returns black image with same width and height as image
	cv2.fillPoly(mask, polygon, 255)  # draw white polygon in the mask image
	roi = cv2.bitwise_and(edge, mask)

	cv2.imshow("roi", roi)
	cv2.imshow('mask', mask)
	# line detection
	lines = cv2.HoughLinesP(roi, 1, np.pi / 180, 10, np.array([]), minLineLength=16, maxLineGap=4)

	hough = display_lines(frame, lines)
	hough_image = cv2.addWeighted(frame, 0.8, hough, 1, 0)
	cv2.imshow('hough', hough_image)

	best_fit_lines = compute_best_fit_line(frame, lines)
	if len(best_fit_lines) > 0:
		hough = display_lines(frame, best_fit_lines)
		lane_image = cv2.addWeighted(frame, 0.8, hough, 1, 0)
		x1, y1, x2, y2, steering_angle = compute_steering_line(frame, best_fit_lines)
		#cv2.line(lane_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
		cv2.imwrite('demo/images/lane/lane{}.png'.format(index), lane_image)
		cv2.imwrite('demo/images/hsv/hsv{}.png'.format(index), hsv_mask)
		cv2.imwrite('demo/images/canny/canny{}.png'.format(index), edge)
		cv2.imwrite('demo/images/roi/roi{}.png'.format(index), roi)
		cv2.imwrite('demo/images/mask.png', mask)
		cv2.imwrite('demo/images/hough/hough{}.png'.format(index), hough_image)
		return lane_image, steering_angle, len(best_fit_lines)
	
	
	return frame, 90, 0


def compute_steering_line(frame, lines):
	height, width = frame.shape[:2]
	if len(lines) == 1:
		x1 = lines[0][0]
		x2 = lines[0][2]
		x_offset = x2 - x1
		y_offset = int(height / 2)
	elif len(lines) == 2:
		left_x2 = lines[0][2]
		right_x2 = lines[1][2]
		center_x = width / 2
		x_offset = (left_x2 + right_x2) / 2 - center_x
		y_offset = int(height / 2)

	angle_to_mid_radian = math.atan(x_offset / y_offset)
	angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / math.pi)
	steering_angle = angle_to_mid_deg + 90  # 90 is straight

	steering_angle_radian = steering_angle / 180.0 * math.pi
	x1 = int(width / 2)
	y1 = height
	x2 = int(x1 - height / (2 * math.tan(steering_angle_radian)))
	y2 = int(height / 2)

	return x1, y1, x2, y2, steering_angle


def compute_best_fit_line(frame, lines):
	left_line_list = []
	right_line_list = []

	lane_lines = []

	height, width = frame.shape[:2]

	if lines is not None:
		for line in lines:
			x1, y1, x2, y2 = line.reshape(4)
			if x1 == x2:
				#print('Skipping one line segment')
				continue
			line_parameters = np.polyfit((x1, x2), (y1, y2), 1)

			slope = line_parameters[0]
			intercept = line_parameters[1]

			if slope < 0:
				if x1 <  width/2 and x2 < width/2:
					left_line_list.append((slope, intercept))
			else:
				if x1 > width/2 and x2 > width/2:
					right_line_list.append((slope, intercept))

		left_line_average = np.average(left_line_list, axis=0)
		right_line_average = np.average(right_line_list, axis=0)

		if len(left_line_list) > 0:
			#print(left_line_average)
			left_line = convert_to_coordinates(frame, left_line_average)
			lane_lines.append(left_line)
		if len(right_line_list) > 0:
			#print(right_line_average)
			right_line = convert_to_coordinates(frame, right_line_average)
			lane_lines.append(right_line)
	return lane_lines


def convert_to_coordinates(frame, line_parameters):
	slope, intercept = line_parameters
	height, width = frame.shape[:2]
	y1 = frame.shape[0]
	y2 = int(frame.shape[0] / 2)

	x1 = int((y1 - intercept) / slope)
	x2 = int((y2 - intercept) / slope)

	x1 = max(-width, min(2 * width, x1))
	x2 = max(-width, min(2 * width, x2))
	return np.array([x1, y1, x2, y2])


def display_lines(image, lines):
	hough_image = np.zeros_like(image)

	# draw the lines
	if lines is not None:
		for line in lines:
			x1, y1, x2, y2 = line.reshape(4)
			cv2.line(hough_image, (x1, y1), (x2, y2), (255, 0, 255), 5)
	return hough_image


if __name__ == '__main__':

	file = "video01.mp4"
	cap = cv2.VideoCapture(file)
	while cap.isOpened():
		ret, frame = cap.read()
		if ret:
			lane_image, steering_angle, num_of_lines = detect_lanes(frame)
			cv2.imshow("lane", lane_image)
			if cv2.waitKey(100) & 0xFF == ord('q'):
				break


	cap.release()
	cv2.destroyAllWindows()