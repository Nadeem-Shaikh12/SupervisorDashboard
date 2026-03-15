"""
tests/test_industry40.py
========================
Tests the Phase 5 Advanced Industry 4.0 Platform capabilities.
Validates Anomaly Detection, ML Data Science Pipeline training, 
WebSocket streaming, and DB mutations.
"""

import os
import sys
import base64
import cv2
import numpy as np
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DREAMVISION_CAMERA_BACKEND"] = "SIMULATOR"

from fastapi.testclient import TestClient
from edge_server.api.server import app

def generate_thermal_b64(temp: float) -> str:
    img = np.zeros((64, 64), dtype=np.float32) + 80.0
    cv2.circle(img, (32, 32), 10, temp, -1)
    _, buf = cv2.imencode(".png", img.astype(np.uint8))
    return base64.b64encode(buf).decode("utf-8")

def simulate_pipeline_bulk(client):
    """Seed the database with > 50 records to allow Scikit Learn to train and trend averages."""
    # Seed 50 normal crankcase ok runs (avg temp 100)
    from datetime import datetime, timedelta
    for i in range(50):
        ts = (datetime.now() - timedelta(minutes=60-i)).strftime("%Y-%m-%dT%H:%M:%S")
        client.post("/inspect", json={
            "device_id": "Glass-01",
            "thermal_image": generate_thermal_b64(100.0 + (i % 5)),
            "timestamp": ts
        })

def test_industry_40():
    print("=" * 60)
    print("  Testing Phase-5 Industry 4.0 Smart Factory")
    print("=" * 60)
    
    from database.db import get_connection, init_db
    from dataset.loader import load_components_dataset
    init_db()
    
    with get_connection() as c:
        c.cursor().execute("DELETE FROM parts_inspection")
        c.cursor().execute("DELETE FROM inspection_anomalies")
        c.commit()
    load_components_dataset(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "components.csv"))
    
    with TestClient(app) as client:
        print("\n[1] Seeding production data via Edge Pipeline...", end="")
        simulate_pipeline_bulk(client)
        print(" [DONE]")
        
        print("\n[2] Testing Anomaly & Predictive Maintenance Algorithms...")
        # Inject an absolute outlier to trigger Z-score and trend maintenance
        from datetime import datetime
        res = client.post("/inspect", json={
            "device_id": "Glass-01",
            "thermal_image": generate_thermal_b64(250.0),
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        })
        data = res.json()
        
    # Check that response included maintenance alert
    assert "maintenance_alert" in data, "Maintenance alert was missing from pipeline!"
    assert data["maintenance_alert"]["component"] == "crankcase"
    print(f"    [PASS] Predictive Maintenance generated alert ({data['maintenance_alert']['issue']})")
    
    # Check that anomaly was stored natively in the table
    with get_connection() as c:
        row = c.execute("SELECT * FROM inspection_anomalies").fetchone()
        assert row is not None
        assert row["anomaly_type"] == "Temperature Spike"
    print("    [PASS] Anomaly Engine classified Z-Score deviation securely.")
    
    print("\n[3] Testing ML Defect Predictor Training...")
    with TestClient(app) as client:
        train_res = client.post("/train_model")
        assert train_res.status_code == 200
    print("    [PASS] Historical Data Science Model Trained and Loaded!")
    
    print("\n[4] Testing WebSocket Digital Twin Real-Time Streaming...")
    with TestClient(app) as client:
        with client.websocket_connect("/ws/inspections") as websocket:
            # Trigger another capture
            client.post("/inspect", json={
                "device_id": "Glass-01",
                "thermal_image": generate_thermal_b64(160.0), # NOK
                "timestamp": "2026-03-15T11:00:00"
            })
            # WS should instantly yield the JSON
            ws_data = websocket.receive_json()
            assert ws_data["status"] == "NOK"
            assert ws_data["component_name"] == "crankcase"
            
    print("    [PASS] FastAPI WebSocket successfully pushed event payload to Digital Twin!")
    
    print("\n" + "=" * 60)
    print("  \033[32mAll Phase-5 Industry 4.0 functionality PASSED [OK]\033[0m")
    print("=" * 60)

if __name__ == "__main__":
    test_industry_40()
