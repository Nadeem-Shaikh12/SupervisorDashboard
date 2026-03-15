import cv2
import numpy as np
import time
import sys
import os
import requests
import base64
from datetime import datetime

# Ensure project root is in path to import camera modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from camera.camera_interface import build_camera
from camera.image_processing import ThermalProcessor
import camera.config as cfg

def push_to_dashboard(frame, stats):
    """Encodes the frame and stats, then POSTs to the Edge Server (8002)."""
    try:
        _, buf = cv2.imencode(".jpg", frame)
        b64 = base64.b64encode(buf).decode("utf-8")
        
        payload = {
            "device_id": cfg.DEVICE_ID + "-Viewer",
            "thermal_image": b64,
            "timestamp": datetime.now().isoformat()
        }
        
        # Dashboard Edge Server is on Port 8002
        url = "http://localhost:8002/inspect"
        requests.post(url, json=payload, timeout=1)
    except:
        pass # Silent fail to avoid interrupting the viewer

def main():
    print("=" * 60)
    print("  DreamVision 'Pro' Viewer & Sync Node")
    print("  [Source: API 8001 | Sync: Dashboard 8002]")
    print("=" * 60)

    # MJPEG stream URL from main_api.py
    stream_url = f"http://127.0.0.1:8001/stream"
    
    print(f"Connecting to stream: {stream_url}...")
    
    cap = None
    retry_count = 0
    while retry_count < 10:
        cap = cv2.VideoCapture(stream_url)
        if cap.isOpened():
            print(" [✓] Connected to Capture API.")
            break
        print(f" [!] Stream not ready yet. Retrying ({retry_count+1}/10)...")
        time.sleep(3)
        retry_count += 1

    if cap is None or not cap.isOpened():
        print("ERROR: Could not open stream after 10 attempts. Please ensure 'main_api.py' is running.")
        return

    # Create display window if not headless
    headless = os.environ.get("DREAMVISION_HEADLESS", "false").lower() == "true"
    window_name = "DreamVision Pro Live Feed"
    if not headless:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT)

    print(f"\n [INFO] Running in {'HEADLESS' if headless else 'GUI'} mode.")
    print("\n [INFO] Auto-syncing to Supervisor Dashboard every 3 seconds...")

    last_sync = 0
    sync_interval = 3.0 # seconds

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Stream lost. Reconnecting...")
                time.sleep(1)
                cap = cv2.VideoCapture(stream_url)
                continue

            if not headless:
                cv2.imshow(window_name, frame)

            # Automatic Sync Logic (throttled)
            if time.time() - last_sync > sync_interval:
                push_to_dashboard(frame, {})
                last_sync = time.time()

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"manual_snap_{timestamp}.png"
                cv2.imwrite(filename, frame)
                print(f" [✓] Manual snapshot saved: {filename}")
                push_to_dashboard(frame, {})

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Goodbye!")

if __name__ == "__main__":
    main()
