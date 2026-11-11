#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This program is demonstration for face and object detection using haar-like features.
The program finds faces in a camera image or video stream and displays a red box around them.

Original C implementation by:  ?
Python implementation by: Roman Stanchak, James Bowman
Updated: Copyright (c) 2016, Tal Regev.
"""
import sys
import os
from optparse import OptionParser

import rospy
import sensor_msgs.msg
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

# Parameters for haar detection
# From the API:
# The default parameters (scale_factor=2, min_neighbors=3, flags=0) are tuned
# for accurate yet slow object detection. For a faster operation on real video
# images the settings are:
# scale_factor=1.2, min_neighbors=2, flags=CV_HAAR_DO_CANNY_PRUNING,
# min_size=<minimum possible face size
fx=4.476#通过相机标定求得的焦距fx
fy=5.96#通过相机标定求得的焦距fy
x_size=960#x方向像素
y_size=540#y方向像素
sensor_x=3.2#传感器宽度
sensor_y=2.4#传感器高度
scan_high=1.0
min_size      = (10, 10)
image_scale   = 2
haar_scale    = 1.2
min_neighbors = 2
haar_flags    = 0
time_start    = 0

if __name__ == '__main__':

    # TODO add this file in the repository and make it relative to this python script. (not all people will run this from linux)
    haarfile = '/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml'

    parser = OptionParser(usage = "usage: %prog [options]")
    parser.add_option("-c", "--cascade", action="store", dest="cascade", type="str", help="Haar cascade file, default %default", default = haarfile)
    parser.add_option("-t", "--topic", action="store", dest="topic", type="str", help="Topic to find a face on, default %default", default = '/camera/rgb/image_raw')
    parser.add_option("-g", "--ctopic", action="store", dest="ctopic", type="str", help="Compressed topic to find a face on, default %default", default = '/camera/rgb/image/compressed')
    (options, args) = parser.parse_args()

    cascade = cv2.CascadeClassifier()
    cascade.load(options.cascade)
    br = CvBridge()
    def len2(x1,y1,x2,y2):
        return (int(x1)-int(x2))*(int(x1)-int(x2))+(int(y1)-int(y2))*(int(y1)-int(y2))

    def detect_and_draw(imgmsg):
	#fileObject = open('/home/iax-lab/Desktop/sampleList.txt', 'a+')
        imag = br.imgmsg_to_cv2(imgmsg, "bgr8")
        # allocate temporary images
        new_size = (int(imag.shape[1] / image_scale), int(imag.shape[0] / image_scale))

        # convert color input image to grayscale
        num = 20  # 定义数组大小
    	all = np.zeros([num,3],dtype=np.uint32)
    	# 创建一个二维数组用来存储检测到的圆的数据（最多存储num组数据)
    	blur = cv2.medianBlur(imag, 1)
    	gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
        imag1 = gray.copy()
    	circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 100, param1=100, param2=100, minRadius=2
                          , maxRadius=0)

    	x0 = int(circles[0][0][0])
    	y0 = int(circles[0][0][1])
    	r0 = 0
    	all[0][0] = x0
    	all[0][1] = y0
        error_y=480-x0
        error_x=270-y0
        a=error_x*sensor_x*1.0/(x_size*fx)#x偏差
        b=error_y*sensor_y*1.0/(y_size*fy)#y偏差
        print(a)
        print(b)
    	#cv2.circle(imag1, (x0, y0), 2, (0, 0, 255), 2, -1) #print circle heart
        #cv2.imshow('result', imag1)
        cv2.waitKey(6)
       
	
    def compressed_detect_and_draw(compressed_imgmsg):
        img = br.compressed_imgmsg_to_cv2(compressed_imgmsg, "bgr8")
        # allocate temporary images
        new_size = (int(img.shape[1] / image_scale), int(img.shape[0] / image_scale))

        # convert color input image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # scale input image for faster processing
        small_img = cv2.resize(gray, new_size, interpolation = cv2.INTER_LINEAR)

        small_img = cv2.equalizeHist(small_img)

        if(cascade):
            faces = cascade.detectMultiScale(small_img, haar_scale, min_neighbors, haar_flags, min_size)
            if faces is not None:
                for (x, y, w, h) in faces:
                    # the input to detectMultiScale was resized, so scale the
                    # bounding box of each face and convert it to two CvPoints
                    pt1 = (int(x * image_scale), int(y * image_scale))
                    pt2 = (int((x + w) * image_scale), int((y + h) * image_scale))
                    cv2.rectangle(img, pt1, pt2, (255, 0, 0), 3, 8, 0)

        cv2.imshow("compressed_result", img)
        cv2.waitKey(6)

    rospy.init_node('targetring_write')
    rospy.Subscriber(options.topic, sensor_msgs.msg.Image, detect_and_draw)
    rospy.Subscriber(options.ctopic, sensor_msgs.msg.CompressedImage, compressed_detect_and_draw)
    rospy.spin()
