"""
tests/test_inspection.py
=========================
Integration test for the DreamVision Phase-2 automated edge inspection module.

1. Sets up the mock simulator infrastructure.
2. Initializes the local Edge DB.
3. Loads components dataset to memory tables.
4. Spawns an automated inspection run and checks return mapping.
"""

import os
import sys

# Ensure main module paths are searchable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force simulator and a test configuration
os.environ["DREAMVISION_CAMERA_BACKEND"] = "SIMULATOR"
os.environ["DREAMVISION_DEVICE_ID"] = "TEST-INSPECT-01"

from camera import build_camera, ThermalProcessor, setup_logging
from database import init_db
from database.db import get_connection
from dataset import load_components_dataset
from inspection_engine import InspectionPipeline

def test_inspection_pipeline():
    print("=" * 60)
    print("  Testing Phase-2 Inspection Pipeline")
    print("=" * 60)
    
    # 1. Setup logging
    setup_logging()
    
    # 2. Database Init
    print("[1] Initializing edge database...")
    init_db()

    # Clear previous test data manually to avoid false assertions
    with get_connection() as conn:
        conn.cursor().execute("DELETE FROM parts_inspection")
        conn.commit()
    
    # 3. Load dataset
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "components.csv")
    print(f"\n[2] Loading dataset from {csv_path}...")
    rows = load_components_dataset(csv_path)
    print(f"    Loaded {rows} components.")
    
    # Verify DB presence 
    with get_connection() as c:
        row = c.execute("SELECT * FROM component_temperature_rules WHERE component_name = 'crankcase'").fetchone()
        assert row is not None, "crankcase rule not inserted!"
        assert row["failure_temp"] == 150.0, f"Expected 150.0, got {row['failure_temp']}"
    print("    [PASS] Database rules verified.")
    
    # 4. Integrate Pipeline Elements
    print("\n[3] Booting inspection engine with simulator camera...")
    cam = build_camera()
    proc = ThermalProcessor()
    pipeline = InspectionPipeline(cam, proc)
    
    cam.open()
    try:
        # Simulate testing a standard crankcase
        print("\n[4] Inspecting a 'crankcase' component...")
        result = pipeline.inspect_part("crankcase")
        
        # Output evaluation constraints Check:
        assert isinstance(result, dict)
        assert result["component_name"] == "crankcase"
        assert result["part_uid"].startswith("DV-")
        assert result["status"] in ["OK", "WARNING", "NOK"]
        assert result["temperature"] > 0.0
        assert "data" in result["image_path"]
        assert "timestamp" in result
        
        print("\n    Inspection Result:")
        import json
        print(f"      {json.dumps(result, indent=2)}")
        print("    [PASS] Inspection output structure verified.")
        
        # 5. DB Verification
        with get_connection() as c:
            db_res = c.execute("SELECT * FROM parts_inspection WHERE part_uid = ?", (result["part_uid"],)).fetchone()
            assert db_res is not None
            assert db_res['status'] == result["status"]
            assert abs(db_res['temperature'] - result["temperature"]) < 0.1
        print("    [PASS] Database insertion verified.")
        
    finally:
        cam.close()
        
    print("\n" + "=" * 60)
    print("  \033[32mAll inspection integration tests PASSED [OK]\033[0m")
    print("=" * 60)

if __name__ == "__main__":
    test_inspection_pipeline()
