import os
import sys
import datetime
import random
import time
import requests
import cv2
import numpy as np
import base64

es_url = "http://localhost:8002/inspect"

# Simulated components from our components.csv dataset:
components = [
    {"name": "crankcase", "temp": 110.0},        # OK (120 is max)
    {"name": "crankcase", "temp": 145.0},        # WARNING / NOK (140 critical)
    {"name": "battery_pack", "temp": 30.0},      # OK
    {"name": "battery_pack", "temp": 60.0},      # WARNING / NOK (55 critical)
    {"name": "brake_rotor", "temp": 320.0}       # NOK (300 critical)
]

print("Injecting Live AI Dummy PIDs into running Edge Server Pipeline...")

# Generate a fast valid Dummy Base64 Grayscale Image matching ESP32 raw thermal array format
blank_frame = np.zeros((240, 320), dtype=np.uint8)
cv2.putText(blank_frame, "SIM", (120, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)
_, buf = cv2.imencode('.jpg', blank_frame)
valid_b64_mock = base64.b64encode(buf).decode('utf-8')

for comp in components:
    dummy_device = f"ESP32-S3-SIM-{random.randint(10,99)}"
    timestamp = datetime.datetime.now().isoformat()
    
    # We send the simulated reading directly via REST to the active server 
    # instead of bypassing the AI via sqlite injection like last time.
    payload = {
        "device_id": dummy_device,
        "thermal_image": valid_b64_mock, 
        "timestamp": timestamp,
        "temp_override": comp["temp"],     
        "target_component": comp["name"]
    }

    try:
        # Hit the live 8002 server endpoint
        res = requests.post(es_url, json=payload)
        
        print(f"\n[{timestamp}] -> Scanning {comp['name']} at {comp['temp']}°C ...")
        if res.status_code == 200:
            result = res.json()
            print(f"   => AI Evaluation: {result.get('status', 'OK')}")
            print(f"   => Component Processed: {result.get('component_name', comp['name'])}")
            print(f"   => Edge Database PID Saved: {result.get('part_uid', 'OK')}")
        else:
            print(f"   => [API ERROR] Code {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"Failed to reach server: {e}")
        
    time.sleep(1.0) # Slight delay purely for logs

print("\nDone! Please check the dashboard at http://localhost:8002/app/index.html to see them appear live.")
