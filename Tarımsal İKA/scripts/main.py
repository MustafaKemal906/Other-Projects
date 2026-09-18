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
image_out_path = os.path.abspath("/home/mustafa/catkin_ws/src/atom/script2/img")

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
    #crop_lines, one = crop_row_detect(current_frame)
    two = drawer(current_frame)

    if two is not None:
        cv2.imshow("bir", two)
        save_image('nihai', two)
        cv2.waitKey(1)
    else:
        rospy.logwarn("Received an invalid frame")

#########################################################################################################
### İŞARETLEME & DEĞİŞTİR ###
def drawer(image):
    #image_path = "./img/green_2.jpg"
    #image = cv2.imread(image_path)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    green_only = cv2.bitwise_and(image, image, mask=mask)
    height, width, _ = green_only.shape
    offset = 20  # Adjust this value as needed
    middle_line_x = width // 2 - offset
    cv2.line(image, (middle_line_x, 0), (middle_line_x, height), (0, 255, 0), 2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    left_points = []
    right_points = []
    for contour in contours:
        # Get all points of the contour
        for point in contour[:, 0]:
            # Check if the point is on the left or right side of the middle line
            if point[0] < middle_line_x:
                left_points.append(point)
            else:
                right_points.append(point)

    left_points = np.array(left_points)
    right_points = np.array(right_points)

    left_hull = cv2.convexHull(left_points)
    right_hull = cv2.convexHull(right_points)
    left_center = np.mean(left_hull, axis=0)[0]
    left_center = tuple(map(int, left_center))
    left_top = tuple(left_hull[left_hull[:, :, 1].argmin()][0])
    left_bottom = tuple(left_hull[left_hull[:, :, 1].argmax()][0])
    left_edge_center = ((left_top[0] + left_bottom[0]) // 2, (left_top[1] + left_bottom[1]) // 2)
    left_direction = (left_edge_center[0] - left_center[0], left_edge_center[1] - left_center[1])
    left_extended_start = (left_center[0] - 1 * left_direction[0], left_center[1] - 1 * left_direction[1])
    left_extended_end = (left_center[0] + 1 * left_direction[0], left_center[1] + 1 * left_direction[1])
    right_center = np.mean(right_hull, axis=0)[0]
    right_center = tuple(map(int, right_center))
    right_top = tuple(right_hull[right_hull[:, :, 1].argmin()][0])
    right_bottom = tuple(right_hull[right_hull[:, :, 1].argmax()][0])
    right_edge_center = ((right_top[0] + right_bottom[0]) // 2, (right_top[1] + right_bottom[1]) // 2)
    right_direction = (right_edge_center[0] - right_center[0], right_edge_center[1] - right_center[1])
    right_extended_start = (right_center[0] - 1 * right_direction[0], right_center[1] - 1 * right_direction[1])
    right_extended_end = (right_center[0] + 1 * right_direction[0], right_center[1] + 1 * right_direction[1])
    cv2.line(image, (int(left_extended_start[0]), int(left_extended_start[1])), (int(left_extended_end[0]), int(left_extended_end[1])), (255, 0, 0), 2)
    cv2.line(image, (int(right_extended_start[0]), int(right_extended_start[1])), (int(right_extended_end[0]), int(right_extended_end[1])), (255, 0, 0), 2)

    # Draw dots for the edge centers
    # cv2.circle(image, left_edge_center, 5, (255, 0, 255), -1)
    # cv2.circle(image, right_edge_center, 5, (255, 0, 255), -1)

    cv2.drawContours(image, [left_hull], -1, (0, 0, 255), 2)
    cv2.drawContours(image, [right_hull], -1, (0, 0, 255), 2)

    return image

#########################################################################################################

# THE FIRST IMAGE
def crop_row_detect(frame):
    save_image('green', frame)
    image_edit = grayscale_transform(frame)
    save_image('1_image_gray', image_edit)
    _, last = cv2.threshold(image_edit, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    save_image('2_image_bin', last)
    crop_points = strip_process(last)
    save_image('2_image_bin', last)
    crop_lines = crop_point_hough(crop_points)
    save_image('9_image_hough', cv2.addWeighted(frame, 1, crop_lines, 1, 0.0))

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
