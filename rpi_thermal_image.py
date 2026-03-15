"""
rpi_thermal_image.py
=====================
Standalone script to capture a single thermal image from an ESP32 WiFi camera.
"""

import os
import cv2
import numpy as np
import logging
from datetime import datetime
from camera.esp32_thermal_stream import ESP32ThermalStream
from camera.image_processing import ThermalProcessor
import camera.config as cfg

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dreamvision.standalone_capture")

if __name__ == "__main__":
    import sys
    print("-" * 40)
    print(" DreamVision ESP32 Thermal Capture Tool ")
    print("-" * 40)
    
    # Check for manual IP override or simulator mode
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "simulator":
            logger.info("Running in SIMULATOR mode for verification...")
            cfg.CAMERA_BACKEND = "SIMULATOR"
            # We'll use the build_camera factory for simulator
            stream = None 
        else:
            manual_ip = sys.argv[1]
            if not manual_ip.startswith("http"):
                manual_ip = f"http://{manual_ip}"
            logger.info(f"Using manual IP override: {manual_ip}")
            stream = ESP32ThermalStream(endpoints=[manual_ip])
    else:
        stream = None 

    try:
        def capture_with_source(s_obj=None):
            save_dir = os.path.join(cfg.DATA_ROOT, "captures")
            os.makedirs(save_dir, exist_ok=True)
            
            # Use factory if simulator, else use the provided stream object
            if cfg.CAMERA_BACKEND == "SIMULATOR":
                from camera.camera_interface import build_camera
                source = build_camera()
                source.open()
                logger.info("Capturing from Simulator...")
                thermal_data = source.next_frame()
                success = thermal_data is not None
            else:
                s = s_obj if s_obj else ESP32ThermalStream()
                logger.info("Connecting to ESP32 camera...")
                if not s.connect():
                    logger.error("Failed to connect to ESP32. Check WiFi connection and IP.")
                    return False
                logger.info("Capturing frame...")
                success, thermal_data = s.read_frame()
                source = s

            if not success or thermal_data is None:
                logger.error("Failed to read thermal data.")
                if hasattr(source, 'close'): source.close()
                return False

            processor = ThermalProcessor()
            processed_frame = processor.process(thermal_data)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thermal_capture_{timestamp}.jpg"
            filepath = os.path.join(save_dir, filename)
            cv2.imwrite(filepath, processed_frame.heatmap_bgr)
            
            logger.info(f"Successfully saved thermal image to: {filepath}")
            logger.info(f"Max Temp: {processed_frame.stats.max_temp:.1f} °C")
            logger.info(f"Status: {processed_frame.status}")
            
            if hasattr(source, 'close'): source.close()
            return True

        if capture_with_source(stream):
            print("\nCapture Complete!")
        else:
            print("\nCapture Failed.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
    print("-" * 40)
