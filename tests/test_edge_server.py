"""
tests/test_edge_server.py
==========================
End-to-End integration test covering the DreamVision Phase-3 Edge Server.
Tests the Device-to-Edge REST API POST endpoint, the Background Sync Thread, 
Database Storage, and Pipeline logic using simulated encoded imagery.
"""

import os
import sys
import time
import base64
import json
import threading
import cv2
import numpy as np
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set strict SIMULATOR mode context before imports
os.environ["DREAMVISION_CAMERA_BACKEND"] = "SIMULATOR"

from edge_server.api.server import app, cloud_worker
from database.db import get_connection, init_db
from dataset.loader import load_components_dataset

client = TestClient(app)

def create_dummy_base64_image() -> str:
    """Uses OpenCV to generate a synthetic hot crankcase representation."""
    img = np.zeros((64, 64), dtype=np.float32)
    # Background
    img += 80.0 
    # Hotspot center representing NOK failure temp (failure=150.0) -> let's make it 160.0°C!
    cv2.circle(img, (32, 32), radius=10, color=160.0, thickness=-1)
    
    # Needs to be sent as an encoded payload over REST
    _, buf = cv2.imencode(".png", img.astype(np.uint8))
    return base64.b64encode(buf).decode("utf-8")

def test_cloud_edge_infrastructure():
    print("=" * 60)
    print("  Testing Phase-3 Edge AI Infrastructure")
    print("=" * 60)
    
    print("[1] Rebuilding Edge DB & Loading Dataset Rules...")
    init_db()
    with get_connection() as c:
        c.cursor().execute("DELETE FROM parts_inspection")
        c.commit()
    load_components_dataset(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "components.csv"))
    
    print("\n[2] Booting Background Cloud Sync Thread...")
    cloud_worker.start()
    
    print("\n[3] Simulating WiFi Device to Edge API Transmission (/inspect)...")
    b64_thermal = create_dummy_base64_image()
    
    payload = {
        "device_id": "DreamVision-Glass-01",
        "thermal_image": b64_thermal,
        "rgb_image": b64_thermal,
        "timestamp": "2026-03-15T15:30:10"
    }
    
    response = client.post("/inspect", json=payload)
    data = response.json()
    
    assert response.status_code == 200
    assert data["component_name"] == "crankcase"
    assert data["status"] == "NOK" # 160.0 >= 150 failure threshold
    assert data["part_uid"].startswith("DV-")
    uid = data["part_uid"]
    
    print(f"    [PASS] Part Processed over API with ID {uid} and Temp {data['temperature']}°C")
    
    print("\n[4] Querying Supervisor Dashboard Database APIs (/inspections)...")
    fetch_resp = client.get(f"/inspection/{uid}")
    assert fetch_resp.status_code == 200
    db_record = fetch_resp.json()
    assert db_record["sync_status"] == "PENDING"
    print("    [PASS] Database successfully registered edge cache marked as PENDING")
    
    print("\n[5] Waiting for Automatic Cloud Synchronization Thread...")
    cloud_worker.sync_now() # force trigger instead of waiting the interval
    time.sleep(0.5)
    
    fetch_resp = client.get(f"/inspection/{uid}")
    db_record = fetch_resp.json()
    assert db_record["sync_status"] == "SYNCED"
    print("    [PASS] Edge Server successfully acknowledged upload completion to Factory DB")
    
    cloud_worker.stop()
    print("\n" + "=" * 60)
    print("  \033[32mAll Phase-3 Network & Edge API integration tests PASSED [OK]\033[0m")
    print("=" * 60)

if __name__ == "__main__":
    test_cloud_edge_infrastructure()
