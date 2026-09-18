#!/usr/bin python3
# -*- coding: utf-8 -*-

import math
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import numpy as np

images_to_save = [2, 3, 4, 5]
strip_to_save = 3
curr_image = 0
timing = False
image_out_path = os.path.abspath("/home/mustafa/catkin_ws/src/atom/script/img")

NUMBER_OF_STRIPS = 10
SUM_THRESH = 2
DIFF_NOISE_THRESH = 8

HOUGH_RHO = 5
HOUGH_ANGLE = math.pi/180
HOUGH_THRESH = 6

ANGLE_THRESH = math.pi*(30.0/180)

### LAST CALL FOR FUNCS ###
def callback(data):
    br = CvBridge()
    global curr_image
    curr_image += 1
    rospy.loginfo("receiving video frame")
    current_frame = br.imgmsg_to_cv2(data)
    crop_lines, one = crop_row_detect(current_frame)
    two = drawer(one)

    if two is not None:
        cv2.imshow("bir", two)
        save_image('nihai', two)
        cv2.waitKey(1)
    else:
        rospy.logwarn("Received an invalid frame")


### İŞARETLEME & DEĞİŞTİR ###
def drawer(image):
    # Load an image (you can replace this with your own crop field image)
    image_path = "./img/2_image_bin_2.jpg"
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise and improve contour detection
    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)

    # Apply adaptive thresholding to better separate objects from the background
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Apply morphological operations to further clean up the image
    kernel = np.ones((5,5), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Find contours in the processed image
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out small contours (adjust the threshold as needed)
    min_contour_area = 100
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

    # Draw the detected crop rows on the original image
    cv2.drawContours(image, valid_contours, -1, (0, 255, 0), 2)

    return image



# THE FIRST IMAGE
def crop_row_detect(frame):
    image_edit = grayscale_transform(frame)
    _, last = cv2.threshold(image_edit, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    save_image('2_image_bin', last)
    crop_points = strip_process(last)
    crop_lines = crop_point_hough(crop_points)

    return crop_lines, last


### THE LOOP ###
def receive_message():
    rospy.init_node('video_sub_py', anonymous=True)
    rospy.Subscriber('/atom/zed2/left/image_rect_color', Image, callback)
    rospy.spin()
    cv2.destroyAllWindows()

### SAVE IMAGES FUNC ###
def save_image(image_name, image_data):
    print("saving...")
    if curr_image in images_to_save:
        image_name_new = os.path.join(image_out_path, f"{image_name}_{str(curr_image)}.jpg")
        cv2.imwrite(image_name_new, image_data)

def grayscale_transform(image_in):
    b, g, r = cv2.split(image_in)
    return 2 * g - r - b

def strip_process(image_edit):
    
    height = len(image_edit)
    width = len(image_edit[0])
    
    strip_height = height / NUMBER_OF_STRIPS
    crop_points = np.zeros((height, width), dtype=np.uint8)
    strip_height= int(strip_height)
    for strip_number in range(NUMBER_OF_STRIPS):
        image_strip = image_edit[(strip_number*strip_height):((strip_number+1)*strip_height-1), :]
        
        
        #if strip_number == strip_to_save:
            #save_image('4_image_strip_4', image_strip)
        
        v_sum = [0] * width
        v_thresh = [0] * width
        v_diff = [0] * width
        v_mid = [0] * width
        
        diff_start = 0
        diff_end = 0
        diff_end_found = True
        
        for col_number in range(width):
            
            ### Vertical Sum ###
            v_sum[col_number] = sum(image_strip[:, col_number]) / 255
            
            ### Threshold ###
            if v_sum[col_number] >= SUM_THRESH:
                v_thresh[col_number] = 1
            else:
                v_thresh[col_number] = 0
            
            ### Differential with Noise Reduction ###
            if v_thresh[col_number] > v_thresh[col_number - 1]:
                v_diff[col_number] = 1
                if (col_number - diff_end) > DIFF_NOISE_THRESH:
                    diff_start = col_number
                    diff_end_found = False
                
            elif v_thresh[col_number] < v_thresh[col_number - 1]:
                v_diff[col_number] = -1
                
                if (col_number - diff_start) > DIFF_NOISE_THRESH:
                    v_mid[int(diff_start) + int((col_number-diff_start)/2)] = 1
                    diff_end = col_number
                    diff_end_found = True
        
        if curr_image in images_to_save and strip_number == strip_to_save:
            print(v_sum)
            print(v_thresh)
            print(v_diff)
            print(v_mid)
        
        crop_points[(strip_number*strip_height), :] = v_mid
        crop_points *= 255
        
        #image_edit[(strip_number*strip_height):((strip_number+1)*strip_height-1), :] = image_strip
    return crop_points

def crop_point_hough(crop_points):
    height = len(crop_points)
    width = len(crop_points[0])
    crop_line_data = cv2.HoughLines(crop_points, HOUGH_RHO, HOUGH_ANGLE, HOUGH_THRESH)
    crop_lines = np.zeros((height, width, 3), dtype=np.uint8)
    if crop_line_data is not None:
        crop_line_data = crop_line_data[0]
        if len(crop_line_data[0]) == 2:
            for [rho, theta] in crop_line_data:
                if (theta <= ANGLE_THRESH) or (theta >= math.pi - ANGLE_THRESH):
                    a = math.cos(theta)
                    b = math.sin(theta)
                    x0 = a * rho
                    y0 = b * rho
                    point1 = (int(round(x0 + 1000 * (-b))), int(round(y0 + 1000 * (a))))
                    point2 = (int(round(x0 - 1000 * (-b))), int(round(y0 - 1000 * (a))))
                    cv2.line(crop_lines, point1, point2, (0, 0, 255), 2)
        elif len(crop_line_data[0]) == 4:
            for [x0, y0, x1, y1] in crop_line_data:
                cv2.line(crop_lines, (x0, y0), (x1, y1), (0, 0, 255), 2)
    else:
        print("No lines found")
    return crop_lines


### CALL FOR THE LOOP ###
if __name__ == '__main__':
    receive_message()
