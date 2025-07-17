import cv2
import numpy as np
from collections import deque
import sys
import time
import requests

# Initialize variables
points = deque(maxlen=64)  # Store past positions for drawing trail
threshold_value = 210      # Lowered for better sensitivity
min_blob_area = 3          # Further reduced to catch tiny dots
max_blob_area = 100        # Increased to accommodate slight size changes
min_circularity = 0.85     # Relaxed to handle shape variations
last_detection_time = time.time()  # Track last detection time
no_detection_threshold = 2.0  # 2 seconds timeout

# Set up camera (use CAP_DSHOW for Windows, CAP_V4L2 for Linux)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if 'win' in sys.platform.lower() else cv2.CAP_V4L2)
if not cap.isOpened():
    print("Error: Could not open IR camera.")
    exit()

# Try to set camera properties
try:
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.0)  # Disable auto-exposure
    cap.set(cv2.CAP_PROP_EXPOSURE, -100)       # Low exposure to prioritize IR
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)    # Set resolution for better focus
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)   # Adjust as needed
except:
    print("Warning: Could not adjust camera settings.")

# Set up SimpleBlobDetector parameters
params = cv2.SimpleBlobDetector_Params()
params.filterByArea = True
params.minArea = min_blob_area
params.maxArea = max_blob_area
params.filterByCircularity = True
params.minCircularity = min_circularity
params.filterByColor = True
params.blobColor = 255  # Bright blobs (IR tip)
params.filterByInertia = True
params.minInertiaRatio = 0.6  # Very relaxed to handle motion blur
params.filterByConvexity = True
params.minConvexity = 0.8  # Relaxed to handle slight distortions
detector = cv2.SimpleBlobDetector_create(params)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Correct upside-down (vertical flip) and horizontal flip
    frame = cv2.flip(frame, 0)  # Vertical flip (corrects upside-down)
    frame = cv2.flip(frame, 1)  # Horizontal flip (corrects left-right mirroring)

    # Convert to grayscale (IR cameras may output single-channel or color)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

    # Apply threshold to isolate bright IR tip
    _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)

    # Minimal erosion/dilation to preserve the dot
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.erode(thresh, kernel, iterations=1)
    thresh = cv2.dilate(thresh, kernel, iterations=1)

    # Detect blobs
    keypoints = detector.detect(thresh)
    current_time = time.time()
    if keypoints:
        # Filter and select the best blob
        valid_keypoints = [kp for kp in keypoints if min_blob_area <= kp.size**2 <= max_blob_area]
        if valid_keypoints:
            keypoint = max(valid_keypoints, key=lambda k: k.response, default=None)
            if keypoint:
                x, y = int(keypoint.pt[0]), int(keypoint.pt[1])
                size = keypoint.size
                points.appendleft((x, y))
                last_detection_time = current_time  # Update last detection time
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                # print(f"Detected blob: x={x}, y={y}, size={size:.2f}, response={keypoint.response:.2f}")
    else:
        # print("No keypoints detected in this frame.")
        if current_time - last_detection_time >= no_detection_threshold:
            # print("No detection for 2 seconds, refreshing...")
            points.clear()  # Reset trail
            threshold_value = max(200, threshold_value - 10)  # Lower threshold to re-detect
            params.minArea = max(1, min_blob_area - 1)  # Relax min area
            params.maxArea = min(120, max_blob_area + 20)  # Expand max area
            detector = cv2.SimpleBlobDetector_create(params)  # Recreate detector

    # Detect triangle shape for larger pattern
    if len(points) >= 30:  # Use last 30 points to cover 25+ point triangle
        p1, p15, p30 = points[-30], points[-15], points[-1]  # First, middle, last
        if all(p for p in [p1, p15, p30]):
            # Calculate distances
            d1_15 = np.sqrt((p1[0] - p15[0])**2 + (p1[1] - p15[1])**2)
            d15_30 = np.sqrt((p15[0] - p30[0])**2 + (p15[1] - p30[1])**2)
            d30_1 = np.sqrt((p30[0] - p1[0])**2 + (p30[1] - p1[1])**2)
            # Minimum distance to ensure meaningful shape
            min_distance = 10  # Adjust based on your setup
            if all(d > min_distance for d in [d1_15, d15_30, d30_1]):
                # Check if side lengths are roughly similar (forgiving ratio)
                sides = [d1_15, d15_30, d30_1]
                if 0.5 < min(sides) / max(sides) < 1.5:
                    # Check closure (distance from p30 back to p1 relative to max side)
                    max_side = max(sides)
                    if d30_1 < max_side * 1.5:  # Allow some deviation for closure
                        print("Incendio!")
                        # Call the endpoint
                        endpoint = "http://octoplus.local/api/command/Insert Playlist Immediate/Incendio/1/1"
                        try:
                            response = requests.get(endpoint)
                            if response.status_code == 200:
                                print("Endpoint call successful")
                            else:
                                print(f"Endpoint call failed with status code {response.status_code}")
                        except requests.RequestException as e:
                            print(f"Error calling endpoint: {e}")
                        points.clear()  # Clear keypoints
                        time.sleep(5)  # Pause for 5 seconds

    # Draw the trail (use last known position if no new detection)
    if points and not keypoints:
        points.appendleft(points[0])  # Hold last position if dot is missed
    for i in range(1, len(points)):
        if points[i - 1] is None or points[i] is None:
            continue
        thickness = int(np.sqrt(64 / (i + 1)) * 2.5)
        cv2.line(frame, points[i - 1], points[i], (0, 0, 255), thickness)

    # Display the frame and thresholded image
    cv2.imshow('IR Wand Tracker', frame)
    cv2.imshow('Threshold', thresh)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()