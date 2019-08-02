import copy
import os
from optparse import OptionParser
import cv2
import imutils
import numpy as np
import pandas as pd
import serial
import threading
import time
# to find the arduino
import warnings
import serial
import serial.tools.list_ports
import sys
import requests
import re
import json

# parse params
print(sys.argv)
zipper_type = sys.argv[1]
color = sys.argv[2]
size = sys.argv[3]


def arduinoFinder():
    arduino_ports = [p.device for p in serial.tools.list_ports.comports(
    ) if u'ttyUSB' in p.device]
    if not arduino_ports:
        raise IOError("No Arduino found")
    if len(arduino_ports) > 1:
        warnings.warn('Multiple Arduinos found - using the first')
    return arduino_ports[0].encode('utf-8')


# Start the stream
ser = serial.Serial(arduinoFinder(), 9600)
cap = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(1)
cap.read()
cap2.read()
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
cap.set(cv2.CAP_PROP_EXPOSURE, 0.005)
cap2.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
cap2.set(cv2.CAP_PROP_EXPOSURE, 0.00460)
counter = 0
ctr = 0

class Organizer:
    def __init__(self, expected_start, ser):
        self.pq = []
        self.expected = expected_start
        self.ser = ser
    
    def insert(self, data, priority):
        if priority == self.expected:
            #print(data, priority)
            self.ser.write(data)
            self.expected += 1
            if len(self.pq) > 0:
                prox = self.pq[0]
                if prox[1] == self.expected:
                    del self.pq[0]
                    self.insert(prox[0], prox[1])
        else:
            self.pq.append((data, priority))
            self.pq.sort(key=lambda x: x[1])

elcounter = 0
org = Organizer(elcounter, ser)

def fixPath(path):
    splitted = path.split('/')
    return splitted[0] + '/' + splitted[2] + '/' + splitted[3]


def inferAndNotify(top_frame, head_frame, num):
    global ctr
    global counter
    global org
    try:
        url = 'http://50d83b46.ngrok.io/images' + '?type=' + zipper_type + '&color=' + color + '&size=' + size
        _, tframe = cv2.imencode('.jpg', top_frame)
        _, hframe = cv2.imencode('.jpg', head_frame)

        # new shit
        data_encode_t = np.array(tframe)
        str_encode_t = data_encode_t.tostring()

        data_encode_h = np.array(hframe)
        str_encode_h = data_encode_h.tostring()

        #url = 'http://localhost:3001/conveyors/images/' + '?type=' + zipper_type + '&color=' + color + '&size=' + size + '&conveyor=1'
        files = {'img_head': str_encode_h, 'img_top':str_encode_t}
        data = {'type': zipper_type, 'color': color, 'size': size, 'conveyor': 1}
        response = requests.post(url, files=files, data=data)
        lbl = json.loads(response._content)
    except Exception as e:
        print('exception on infrnce call' + str(e))
        lbl = {"label" : 1}
    
    path_top, path_head = '', ''

    if lbl["label"] == 0:
        #org.insert('b', num)
        ser.write('b')
        path_top, path_head = './public/images/top_b' + str(ctr) + '.jpg', './public/images/head_b' + str(ctr) + '.jpg'
        cv2.imwrite(path_head, head_frame)
        cv2.imwrite(path_top, top_frame[0:,174:-240])
    else:
        #org.insert('g', num)
        ser.write('g')
        path_top, path_head = './public/images/top_g' + str(ctr) + '.jpg', './public/images/head_g' + str(ctr) + '.jpg'
        cv2.imwrite(path_head, head_frame)
        cv2.imwrite(path_top, top_frame[0:,174:-240])
    
    ctr += 1
    url2 = 'http://localhost:3030/imgs'
    if (len(path_top + path_head) > 0):
        try:
            requests.get(url2, params={'path_top': fixPath(path_top), 'path_head': fixPath(path_head)})
        except Exception as e:
            print('Excepting at continuous_construction.py - ' + str(e))



#lacra = 0
while(True):
#    lacra += 1
    ret2, frame2 = cap2.read()
    ret, frame = cap.read()
    
#    if lacra % 401 == 0:
    if (ser.in_waiting > 0 and ser.read(size=1) == b'1'):
        # ret2, frame2 = cap2.read()
        # ret, frame = cap.read()

        while (not ret or not ret2):
            ret, frame = cap.read()
            ret2, frame2 = cap2.read()

        threading.Thread(target=inferAndNotify, args=(copy.deepcopy(frame), copy.deepcopy(frame2), elcounter)).start()
        elcounter += 1
    time.sleep(0.05)



