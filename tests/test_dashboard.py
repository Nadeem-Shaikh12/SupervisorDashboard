"""
tests/test_dashboard.py
========================
Tests the Phase 4 Supervisor Dashboard and Web Routing API.
Ensures stats sum properly and role verifications successfully mutate SQLite.
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

client = TestClient(app)

def generate_thermal_b64(temp: float) -> str:
    img = np.zeros((64, 64), dtype=np.float32) + 80.0
    cv2.circle(img, (32, 32), 10, temp, -1)
    _, buf = cv2.imencode(".png", img.astype(np.uint8))
    return base64.b64encode(buf).decode("utf-8")

def simulate_pipeline_run():
    # 1. OK Crankcase (90 C)
    client.post("/inspect", json={
        "device_id": "Glass-01",
        "thermal_image": generate_thermal_b64(90.0),
        "timestamp": "2026-03-15T10:00:00"
    })
    
    # 2. NOK Crankcase (160 C)
    client.post("/inspect", json={
        "device_id": "Glass-01",
        "thermal_image": generate_thermal_b64(160.0),
        "timestamp": "2026-03-15T10:01:00"
    })
    
    # 3. WARNING Crankcase (140 C)
    client.post("/inspect", json={
        "device_id": "Glass-01",
        "thermal_image": generate_thermal_b64(140.0),
        "timestamp": "2026-03-15T10:02:00"
    })

def test_dashboard_routes():
    print("=" * 60)
    print("  Testing Phase-4 Supervisor Web API & Traceability")
    print("=" * 60)
    
    # Clear DB & populate a fresh dataset by doing a mock run
    from database.db import get_connection, init_db
    from dataset.loader import load_components_dataset
    init_db()
    with get_connection() as c:
        c.cursor().execute("DELETE FROM parts_inspection")
        c.commit()
    load_components_dataset(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "components.csv"))
    
    print("\n[1] Seeding production data via Edge Pipeline...", end="")
    simulate_pipeline_run()
    print(" [DONE]")
    
    print("\n[2] Testing Web Analytics (/dashboard/stats)...")
    resp = client.get("/dashboard/stats")
    stats = resp.json()
    assert resp.status_code == 200
    assert stats["total_inspections"] == 3
    assert stats["ok_count"] == 1
    assert stats["nok_count"] == 1
    assert stats["warning_count"] == 1
    print("    [PASS] Production Analytics aggregating correctly")
    
    print("\n[3] Testing Dashboard Traceability Query (/dashboard/inspections)...")
    res = client.get("/dashboard/inspections")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 3
    
    # Fetch specific NOK UID
    nok_row = next(r for r in rows if r["status"] == "NOK")
    uid = nok_row["part_uid"]
    assert nok_row["verified_status"] == 'Pending'
    print(f"    [PASS] Traceability resolved ID mapping ({uid}) marked as Pending.")
    
    print("\n[4] Testing Role Verification Override (/dashboard/verify)...")
    v_res = client.post(f"/dashboard/verify/{uid}", json={
        "verified_status": "NOK",
        "verified_by": "Supervisor_01"
    })
    assert v_res.status_code == 200
    assert v_res.json()["updated"]["verified_status"] == "NOK"
    assert v_res.json()["updated"]["verified_by"] == "Supervisor_01"
    print("    [PASS] SQLite committed verification override successfully!")

    print("\n" + "=" * 60)
    print("  \033[32mAll Phase-4 Dashboard functionality PASSED [OK]\033[0m")
    print("=" * 60)

if __name__ == "__main__":
    test_dashboard_routes()
