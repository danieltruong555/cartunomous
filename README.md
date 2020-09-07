# cartunomous

An autonomous RC car that can perform both object detection and Lane Navigation using Neural Networks, Raspberry Pi 4, and OpenCV. Using Behavior Cloning and the NVIDIA model, RC car can navigate through blue lanes lines autonomously. RC car can also detect various speed limit signs as well stop signs using Single Shot Detector framework.

To run, execute the following:
  1. workon cv
  2. python3 cartunomous.py -d 0
  
To run with debugging messages on, execute the following:
  1. workon cv
  2. python3 cartunomous.pu -d 1

You can run the project with various flags:

```
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
```


## Video
[Video Demo](https://youtu.be/1H4ECDMZCjU)

## Requirements
- Raspberry Pi 4
- SunFounder Pi-Car S
- Ultrawide PiCamera
- Google Coral TPU
- 2x Li-Ion Batteries with 3.7V

## Features
- Autonomously navigate through blue lane lines using Behavior Cloning via NVIDIA's Convolutional Neural Network.
- Detect speed limit and stop signs using Transfer Learning via Single Shot Detector framework.
- Autonomously adjusts its speed according to speed signs.
- Autonomously stop at stop signs.
