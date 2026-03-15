import os
import sys
import cv2
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camera.camera_interface import build_camera
from camera.image_processing import ThermalProcessor

def test_capture():
    print("Initializing test capture...")
    os.environ["DREAMVISION_CAMERA_BACKEND"] = "SIMULATOR"
    
    cam = build_camera()
    processor = ThermalProcessor()
    
    cam.open()
    print("Camera opened. Capturing frame...")
    
    raw = cam.next_frame()
    if raw is not None:
        print("Frame captured successfully!")
        result = processor.process(raw)
        cv2.imwrite("data/test_capture.jpg", result.heatmap_bgr)
        print("Heatmap saved to data/test_capture.jpg")
    else:
        print("FAILED: Frames is None")
    
    cam.close()

if __name__ == "__main__":
    test_capture()
