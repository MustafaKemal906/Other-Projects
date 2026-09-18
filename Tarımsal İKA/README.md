# ROS Crop Row Detection

A ROS 1 + OpenCV prototype for detecting crop rows and green vegetation from a live camera stream.

The scripts in this repository subscribe to a ROS image topic, convert incoming frames to OpenCV images, isolate vegetation, detect crop-row candidates, and visualize different experimental approaches for row and center detection.

## Overview

The main processing ideas used across the scripts are:

```text
ROS Camera Image
      ↓
CvBridge
      ↓
Color / Grayscale Processing
      ↓
Thresholding
      ↓
Strip-Based Feature Extraction
      ↓
Crop-Row Candidate Points
      ↓
Hough Line Detection
      ↓
Visualization
```

Several alternative detection methods are also included:

```text
Green HSV Mask
   ├── Center of Mass
   ├── Contour Detection
   └── Convex Hull / Left-Right Geometry
```

## ROS Input

The scripts subscribe to:

```text
/atom/zed2/left/image_rect_color
```

Incoming `sensor_msgs/Image` messages are converted to OpenCV images using `CvBridge`.

## Dependencies

- ROS 1
- Python 3
- `rospy`
- `sensor_msgs`
- `cv_bridge`
- OpenCV (`cv2`)
- NumPy

Example ROS dependencies:

```bash
sudo apt install ros-${ROS_DISTRO}-cv-bridge
sudo apt install ros-${ROS_DISTRO}-sensor-msgs
```

Python dependencies:

```bash
pip install numpy opencv-python
```

If OpenCV is already provided by the ROS installation, installing another OpenCV package may not be necessary.

## File Structure

```text
.
├── ekinoks.py
├── main.py
├── detection.py
├── detection_main.py
├── center_detection.py
└── 763ef48f-1564-4ab0-9626-d6a59be3a664.py
```

## Scripts

### `ekinoks.py`

The baseline crop-row detection pipeline.

It:

1. Receives images from the ROS camera topic.
2. Applies a vegetation-enhancing grayscale transform:

```python
2 * G - R - B
```

3. Uses Otsu thresholding to create a binary vegetation image.
4. Divides the image into horizontal strips.
5. Computes the vertical vegetation sum for every column.
6. Detects vegetation-region transitions.
7. Places candidate crop-row center points.
8. Applies a Hough transform to estimate crop-row lines.
9. Displays the detected lines.

Main pipeline:

```text
Camera
  ↓
2G - R - B
  ↓
Otsu Threshold
  ↓
Horizontal Strips
  ↓
Vertical Column Sum
  ↓
Transition Detection
  ↓
Candidate Row Centers
  ↓
Hough Transform
  ↓
Crop Row Lines
```

### `detection.py`

An experimental contour-based detection version.

In addition to the strip/Hough pipeline, it tests a second approach using:

```text
Binary Image
    ↓
Gaussian Blur
    ↓
Adaptive Threshold
    ↓
Morphological Closing
    ↓
Contour Detection
    ↓
Area Filtering
```

Small contours are discarded and the remaining contours are drawn as detected vegetation or crop-row regions.

### `detection_main.py`

A closely related contour-detection prototype.

It applies:

- grayscale conversion
- Gaussian blur
- adaptive Gaussian thresholding
- morphological closing
- external contour detection
- contour-area filtering

The file currently reads a test image from:

```text
./img/2_image_bin_2.jpg
```

inside the `drawer()` function.

### `center_detection.py`

An experimental green-region center detection method.

The image is converted to HSV and a green mask is generated using:

```python
lower_green = [35, 50, 50]
upper_green = [85, 255, 255]
```

Image moments are then used to estimate the center of mass of the detected vegetation:

```text
RGB Image
   ↓
HSV Conversion
   ↓
Green Mask
   ↓
Image Moments
   ↓
Center of Mass
   ↓
Reference Line
```

A vertical line is drawn from the detected center toward the bottom of the image.

### `main.py`

A geometry-based green vegetation detection prototype.

The frame is converted to HSV and thresholded for green pixels. Detected contour points are separated into left and right groups relative to a center reference line.

For each side:

1. Contour points are collected.
2. A convex hull is calculated.
3. The hull center is estimated.
4. Top and bottom points are found.
5. A direction vector is calculated.
6. A line describing the vegetation/crop-row direction is drawn.

Simplified pipeline:

```text
Camera Frame
    ↓
HSV Green Mask
    ↓
Contours
    ↓
Left / Right Separation
    ↓
Convex Hulls
    ↓
Direction Estimation
    ↓
Detected Row Geometry
```

### `763ef48f-1564-4ab0-9626-d6a59be3a664.py`

An alternative version of the convex-hull approach used in `main.py`.

It processes the live ROS frame directly inside `drawer()` and:

- isolates green regions
- divides contour points into left and right groups
- calculates convex hulls
- estimates direction vectors
- draws detected geometry over the camera frame

## Strip-Based Crop Row Detection

The core row-detection algorithm divides the binary image into horizontal strips.

Default parameters:

```python
NUMBER_OF_STRIPS = 10
SUM_THRESH = 2
DIFF_NOISE_THRESH = 8
```

For each strip, the algorithm calculates the amount of vegetation in every image column:

```text
column
  ↓
sum of binary vegetation pixels
  ↓
threshold
  ↓
0 / 1 vegetation presence
```

Transitions from background to vegetation and vegetation to background define a vegetation segment.

The center of a sufficiently wide segment is stored as a crop-row candidate point.

These candidate points are later passed to the Hough transform.

## Hough Line Detection

The default Hough parameters are:

```python
HOUGH_RHO = 5
HOUGH_ANGLE = pi / 180
HOUGH_THRESH = 6
```

Detected lines are filtered using:

```python
ANGLE_THRESH = 30°
```

Only lines sufficiently close to the expected crop-row orientation are drawn.

## Green Vegetation Detection

Some experimental scripts use HSV color segmentation instead of the `2G - R - B` transform.

The current HSV range is:

```python
lower_green = np.array([35, 50, 50])
upper_green = np.array([85, 255, 255])
```

Pixels inside this interval are considered vegetation candidates.

The exact HSV range may need to be adjusted depending on:

- illumination
- camera exposure
- crop type
- soil color
- weather conditions

## Saved Debug Images

Several scripts save intermediate frames for debugging.

Frames selected for saving:

```python
images_to_save = [2, 3, 4, 5]
```

Examples of generated intermediate images include:

```text
0_image_in
1_image_gray
2_image_bin
8_crop_points
9_image_hough
nihai
```

The current source files contain hard-coded output paths such as:

```text
/home/mustafa/catkin_ws/src/atom/script/img
/home/mustafa/catkin_ws/src/atom/script2/img
```

Update these paths before running the scripts on another computer.

## Running

Start ROS and the camera driver that publishes:

```text
/atom/zed2/left/image_rect_color
```

Then source the catkin workspace:

```bash
source ~/catkin_ws/devel/setup.bash
```

Run one of the scripts with Python:

```bash
python3 ekinoks.py
```

or:

```bash
python3 main.py
```

Example for the contour experiment:

```bash
python3 detection.py
```

Example for center detection:

```bash
python3 center_detection.py
```

## Recommended Repository Layout

```text
atom/
├── README.md
├── scripts/
│   ├── ekinoks.py
│   ├── main.py
│   ├── detection.py
│   ├── detection_main.py
│   └── center_detection.py
└── img/
```

## Important Notes

### Hard-Coded Paths

Some scripts contain absolute paths tied to the original catkin workspace. Replace them with project-relative paths or configurable ROS parameters for portability.

### Test Images

Some experimental `drawer()` implementations read fixed images such as:

```text
./img/green_2.jpg
./img/2_image_bin_2.jpg
```

These files must exist if those code paths are used.

### Empty Green Regions

The center-of-mass and convex-hull experiments assume that green pixels were detected.

If the green mask is empty:

- image moments may have `m00 = 0`
- left/right point arrays may be empty
- `cv2.convexHull()` may fail

Production use should add validation before these calculations.

### Python Shebang

The current files use:

```text
#!/usr/bin python3
```

When launching the files directly, use a valid Python 3 shebang such as:

```text
#!/usr/bin/env python3
```

Alternatively, run them explicitly with:

```bash
python3 script_name.py
```

## Algorithm Summary

```text
                         ┌──────────────────────┐
                         │ ROS Camera Image     │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │ OpenCV / CvBridge    │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
       ┌─────────▼─────────┐                 ┌─────────▼─────────┐
       │ 2G - R - B        │                 │ HSV Green Mask    │
       └─────────┬─────────┘                 └─────────┬─────────┘
                 │                                     │
       ┌─────────▼─────────┐          ┌────────────────┼────────────────┐
       │ Otsu Threshold    │          │                │                │
       └─────────┬─────────┘     Center of Mass    Contours       Convex Hull
                 │
       ┌─────────▼─────────┐
       │ Strip Processing  │
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │ Candidate Points  │
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │ Hough Transform   │
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │ Crop Row Lines    │
       └───────────────────┘
```

## Purpose

This repository contains experimental computer-vision approaches for crop-row and vegetation geometry detection from a ROS camera stream.

The scripts explore multiple approaches rather than representing a single finalized detector:

- vegetation-enhanced grayscale processing
- Otsu thresholding
- strip-based crop-row center extraction
- Hough line detection
- adaptive-threshold contour detection
- HSV green segmentation
- center-of-mass estimation
- convex-hull geometry analysis
