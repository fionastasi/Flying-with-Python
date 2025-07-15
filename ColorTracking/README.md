# Color Tracking with DJI Tello

This project uses computer vision and PID controllers to autonomously track a colored object using the DJI Tello drone and OpenCV.

The drone detects an object based on its color (using HSV filtering), calculates its position relative to the center of the image, and dynamically adjusts its movement to keep the object centered — both horizontally and vertically. It also evaluates distance using the object's contour area to adjust depth.

---

## How It Works

### Methodology

1. Connects to the Tello drone and activates the video stream.
2. Converts each frame to HSV color space for better color segmentation.
3. Detects the object via color filtering and calculates its position on the image.
4. Applies PID control to stabilize the object in the center of the camera view.
5. Estimates object distance based on contour area.
6. Adjusts drone position in three axes:
   - **X (depth):** move forward/backward
   - **Y (horizontal):** strafe left/right
   - **Z (vertical):** go up/down

---

## Implementation

- The code establishes a connection with the drone and starts the video feed.
- HSV sliders (trackbars) allow tuning of the color to track.
- The largest contour is identified using `cv2.findContours`, and its center and area are computed.
- Two PID controllers are used:
  - One for horizontal centering (**Y axis**)
  - One for vertical alignment (**Z axis**)
- Based on the object's area, the drone moves forward/backward or remains still.
- A manual control mode is also included for easier testing.

The drone takes off **automatically** if battery level is above 15% and a valid object is detected. If the battery is low, it lands safely.

---

## Controls

Keyboard controls during execution:

| Key | Action                |
|-----|------------------------|
| `t` | Manual takeoff         |
| `l` | Manual landing         |
| `c` | Close program & land   |
| `w` | Move forward           |
| `s` | Move backward          |
| `a` | Move left              |
| `d` | Move right             |
| `r` | Move up                |
| `f` | Move down              |
| `q` | Rotate counterclockwise |
| `e` | Rotate clockwise       |

---

## How to Run

1. Connect your computer to the Tello's Wi-Fi network.
2. Run the Python script.
3. Use the HSV sliders to isolate the target object’s color in the camera feed.

---

## Behavior Summary

- Automatic takeoff if:
  - Battery > 15%
  - A valid colored object is detected in frame
- PID controllers keep the object centered on screen.
- Object distance is estimated using contour area:
  - Too far → move forward
  - Too close → move backward
- Visual lines and status messages appear on screen to aid in calibration and debugging.

---

## Preview
<p align="center">
  <img src="Color.gif" alt="Color Tracking Demo" width="500"/>
</p>

---

## Requirements
```bash
pip install opencv-python djitellopy numpy

