import os
import sys
import time
import subprocess
import threading
import logging
import sqlite3
from database.db import init_db
from database.mongo_db import get_mongo_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Senior Edge AI Architect - System Startup Orchestrator
# ====================================================

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("dreamvision.startup")

def validate_connections():
    """Step 8: Connect to SQLite and MongoDB Atlas"""
    logger.info("Validating Database Connections...")
    
    # SQLite
    try:
        init_db()
        logger.info("  => SQLite Edge Database: [OK]")
    except Exception as e:
        logger.error(f"  => SQLite Edge Database: [FAILED] - {e}")
        return False

    # MongoDB Atlas
    try:
        client = get_mongo_client()
        if client:
            logger.info("  => MongoDB Atlas Cloud: [OK]")
            client.close()
        else:
            logger.warning("  => MongoDB Atlas Cloud: [SKIPPED/MISSING_URI]")
    except Exception as e:
        logger.warning(f"  => MongoDB Atlas Cloud: [CONNECT_ERROR] - {e}")

    return True

def run_services():
    """Launch all platform tiers"""
    logger.info("Starting DreamVision Platform Services...")

    # Set PYTHONPATH and defaults for simulator if hardware isn't detected
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    if "DREAMVISION_CAMERA_BACKEND" not in env:
        env["DREAMVISION_CAMERA_BACKEND"] = "SIMULATOR"

    # 1. Start Capture API (8001) - Handles Hardware/Simulation
    logger.info("Launching Capture API (8001)...")
    capture_proc = subprocess.Popen(
        [sys.executable, "main_api.py"],
        env=env
    )
    time.sleep(5) # Give it time to bind port 8001

    # 2. Start Edge Server (8002) - Includes Inspection Pipeline + Dashboard
    logger.info("Launching Edge Server (8002)...")
    server_proc = subprocess.Popen(
        [sys.executable, "edge_server/api/server.py"],
        env=env
    )
    time.sleep(3) # Give it time to bind port 8002

    # 3. Local Thermal Monitor / Forwarder
    logger.info("Launching Local Thermal Monitor...")
    monitor_proc = subprocess.Popen(
        [sys.executable, "rpi_camera_reader.py"],
        env=env
    )

    return capture_proc, server_proc, monitor_proc

if __name__ == "__main__":
    print("""
    ==================================================
        DreamVision Smart Factory platform v5.0
    ==================================================
    """)
    
    if validate_connections():
        capture, server, monitor = run_services()
        
        try:
            while True:
                time.sleep(1)
                if capture.poll() is not None:
                    logger.error("Capture API process died. Restarting system...")
                    break
                if server.poll() is not None:
                    logger.error("Server process died. Restarting system...")
                    break
                if monitor.poll() is not None:
                    logger.warning("Monitor process exited. Restarting monitor in 5s...")
                    time.sleep(5)
                    monitor = subprocess.Popen(
                        [sys.executable, "rpi_camera_reader.py"],
                        env=os.environ.copy()
                    )
        except KeyboardInterrupt:
            logger.info("Shutting down DreamVision...")
            server.terminate()
            monitor.terminate()
            sys.exit(0)
    else:
        logger.error("System startup failed due to critical dependency errors.")
        sys.exit(1)
