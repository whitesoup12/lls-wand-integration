import cv2
import sys
import numpy as np

# Set up camera (use CAP_DSHOW for Windows, CAP_V4L2 for Linux)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW if 'win' in sys.platform.lower() else cv2.CAP_V4L2)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Try to disable auto-exposure (may not work on all cameras)
try:
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.0)  # Disable auto-exposure
    cap.set(cv2.CAP_PROP_EXPOSURE, -4)        # Set low exposure to prioritize IR
except:
    print("Warning: Could not adjust exposure settings.")

# Threshold for IR tip detection
threshold_value = 200  # Adjust based on IR brightness (0-255)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Correct upside-down (180° rotation) and horizontal flip
    frame = cv2.flip(frame, 0)  # Vertical flip (corrects upside-down)
    frame = cv2.flip(frame, 1)  # Horizontal flip (corrects left-right mirroring)

    # Convert to grayscale (IR cameras may output single-channel or color)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

    # Apply threshold to highlight IR tip
    _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)

    # Display original and thresholded images
    cv2.imshow('Camera Feed', frame)
    cv2.imshow('IR Threshold', thresh)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()