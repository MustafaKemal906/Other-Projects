#!/usr/bin python3
# -*- coding: utf-8 -*-


import math
import rospy # Python library for ROS
from sensor_msgs.msg import Image # Image is the message type
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images
import cv2 # OpenCV library
import os
import numpy as np


images_to_save = [2, 3, 4, 5]
strip_to_save = 3
curr_image = 0
timing = False
image_out_path = os.path.abspath("/home/mustafa/catkin_ws/src/atom/script/img")


NUMBER_OF_STRIPS = 10             # How many strips the image is split into
SUM_THRESH = 2                    # How much green in a strip before it's a plant
DIFF_NOISE_THRESH = 8             # How close can two sections be?


HOUGH_RHO = 5                     # Distance resolution of the accumulator in pixels
HOUGH_ANGLE = math.pi/180         # Angle resolution of the accumulator in radians
HOUGH_THRESH = 6                  # Accumulator threshold parameter. Only those lines are returned that get enough votes


ANGLE_THRESH = math.pi*(30.0/180) # How steep angles the crop rows can be in radians


def callback(data):
 
    # Used to convert between ROS and OpenCV images
    br = CvBridge()
    
    global curr_image
    curr_image += 1
    
    # Output debugging information to the terminal
    rospy.loginfo("receiving video frame")

    # Convert ROS Image message to OpenCV image
    current_frame = br.imgmsg_to_cv2(data)
    image_out=crop_row_detect(current_frame)
    # Display image
    cv2.imshow("camera", image_out)

    cv2.waitKey(1)
      
def receive_message():
 
    # Tells rospy the name of the node.
    # Anonymous = True makes sure the node has a unique name. Random
    # numbers are added to the end of the name. 
    rospy.init_node('video_sub_py', anonymous=True)

    # Node is subscribing to the video_frames topic
    rospy.Subscriber('/atom/zed2/left/image_rect_color', Image, callback)

    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()

    # Close down the video stream when done
    cv2.destroyAllWindows()
  



def crop_row_detect(frame):
    save_image('0_image_in', frame)


    ### Grayscale Transform ###
    image_edit = grayscale_transform(frame)
    save_image('1_image_gray', image_edit)

    ### Binarization ###
    _, image_edit = cv2.threshold(image_edit, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    save_image('2_image_bin', image_edit)
    
    ### Stripping ###
    crop_points = strip_process(image_edit)
    save_image('8_crop_points', crop_points)
    
    ### Hough Transform ###
    crop_lines = crop_point_hough(crop_points)
    save_image('9_image_hough', cv2.addWeighted(frame, 1, crop_lines, 1, 0.0))
    
    return crop_lines
    
def save_image(image_name, image_data):
    print("save imageee")
    if curr_image in images_to_save:
        image_name_new = os.path.join(image_out_path, "{0}_{1}.jpg".format(image_name, str(curr_image) ))
        print("save image")
        cv2.imwrite(image_name_new, image_data)

def grayscale_transform(image_in):
    b, g, r = cv2.split(image_in)
    return 2*g - r - b


def strip_process(image_edit):
    
    height = len(image_edit)
    width = len(image_edit[0])
    
    strip_height = height / NUMBER_OF_STRIPS
    crop_points = np.zeros((height, width), dtype=np.uint8)
    strip_height= int(strip_height)
    for strip_number in range(NUMBER_OF_STRIPS):
        image_strip = image_edit[(strip_number*strip_height):((strip_number+1)*strip_height-1), :]
        
        
        if strip_number == strip_to_save:
            save_image('4_image_strip_4', image_strip)
        
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
    
    #crop_line_data = cv2.HoughLinesP(crop_points, 1, math.pi/180, 2, 10, 10)
    crop_line_data = cv2.HoughLines(crop_points, HOUGH_RHO, HOUGH_ANGLE, HOUGH_THRESH)
    
    crop_lines = np.zeros((height, width, 3), dtype=np.uint8)
    
    if crop_line_data.any() != None:
        crop_line_data = crop_line_data[0]
        #print(crop_line_data)
        
        if len(crop_line_data[0]) == 2:
            for [rho, theta] in crop_line_data:
                #print(rho, theta)
                if (theta <= ANGLE_THRESH) or (theta >= math.pi-ANGLE_THRESH):
                    a = math.cos(theta)
                    b = math.sin(theta)
                    x0 = a*rho
                    y0 = b*rho
                    point1 = (int(round(x0+1000*(-b))), int(round(y0+1000*(a))))
                    point2 = (int(round(x0-1000*(-b))), int(round(y0-1000*(a))))
                    cv2.line(crop_lines, point1, point2, (0, 0, 255), 2)
                
        elif len(crop_line_data[0]) == 4:
            for [x0, y0, x1, y1] in crop_line_data:
                cv2.line(crop_lines, (x0, y0), (x1, y1), (0, 0, 255), 2)
    else:
        print("No lines found")
    
    return crop_lines

if __name__ == '__main__':
  receive_message()




