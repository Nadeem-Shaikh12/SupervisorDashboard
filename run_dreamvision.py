"""
run_dreamvision.py
===================
UPGRADE 2 — Single-command DreamVision Platform Launcher

    python run_dreamvision.py

Starts every tier of the DreamVision Smart Factory Platform in the correct
order using subprocesses for server services and an in-process thread/window
for the live camera visualization:

  1. SQLite edge database initialisation
  2. MongoDB Atlas connectivity check
  3. Dataset rules loading
  4. Capture API server     → http://localhost:8001  (main_api.py)
  5. Edge AI server          → http://localhost:8002  (edge_server/api/server.py)
  6. Live camera window      → OpenCV window          (camera/live_view.py)

All services log their startup status.  Press Ctrl-C to shut down cleanly.
"""

import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

# ── Environment setup ─────────────────────────────────────────────────────────

# Auto-use SIMULATOR when no real ESP32 hardware is present
if "DREAMVISION_CAMERA_BACKEND" not in os.environ:
    os.environ["DREAMVISION_CAMERA_BACKEND"] = "SIMULATOR"

# Allow importing project packages from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("dreamvision.startup")

# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = r"""
  ____                        __     ___     _
 |  _ \ _ __ ___  __ _ _ __ \ \   / (_)___(_) ___  _ __
 | | | | '__/ _ \/ _` | '_ \ \ \ / /| / __| |/ _ \| '_ \
 | |_| | | |  __/ (_| | | | | \ V / | \__ \ | (_) | | | |
 |____/|_|  \___|\__,_|_| |_|  \_/  |_|___/_|\___/|_| |_|

  DreamVision Smart Factory Inspection Platform  v6.0
  Industry-4.0 Thermal AI Inspection System
  ─────────────────────────────────────────────────────
"""

# ── Step 1 & 2: Database Setup ────────────────────────────────────────────────

def step_databases() -> bool:
    """Initialise SQLite and verify MongoDB Atlas."""
    logger.info("──── [STEP 1] Initialising Edge Database (SQLite) …")
    try:
        from database.db import init_db
        init_db()
        logger.info("  ✓ SQLite edge database: READY")
    except Exception as exc:
        logger.error("  ✗ SQLite init failed: %s", exc)
        return False

    logger.info("──── [STEP 2] Verifying Cloud Database (MongoDB Atlas) …")
    try:
        from database.mongo_db import get_mongo_client
        client = get_mongo_client()
        if client:
            logger.info("  ✓ MongoDB Atlas: CONNECTED")
            client.close()
        else:
            logger.warning("  ⚠ MongoDB Atlas: SKIPPED (MONGO_URI not set)")
    except Exception as exc:
        logger.warning("  ⚠ MongoDB Atlas: CONNECT ERROR — %s", exc)

    return True


# ── Step 3: Dataset rules ─────────────────────────────────────────────────────

def step_dataset():
    """Load component temperature rules from CSV into SQLite."""
    logger.info("──── [STEP 3] Loading Component Temperature Rules …")
    csv_path = os.path.join("data", "components.csv")
    if not os.path.exists(csv_path):
        logger.warning("  ⚠ components.csv not found at %s — skipping.", csv_path)
        return
    try:
        import dataset.loader as loader
        loader.load_components_dataset(csv_path)
        logger.info("  ✓ Component rules: LOADED from %s", csv_path)
    except Exception as exc:
        logger.warning("  ⚠ Dataset load error: %s", exc)


# ── Step 4: Capture API (port 8001) ──────────────────────────────────────────

def start_capture_api(env: dict) -> subprocess.Popen:
    """Launch main_api.py as a subprocess."""
    logger.info("──── [STEP 4] Starting Capture API on port 8001 …")
    proc = subprocess.Popen(
        [sys.executable, "main_api.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
    )
    # Relay stdout so operator can see logs
    def _relay(p):
        for line in p.stdout:
            print(f"  [capture] {line}", end="")
    threading.Thread(target=_relay, args=(proc,), daemon=True).start()

    time.sleep(4)     # allow the server to bind port 8001
    if proc.poll() is not None:
        logger.error("  ✗ Capture API exited prematurely (code %s).", proc.returncode)
    else:
        logger.info("  ✓ Capture API: RUNNING  → http://localhost:8001")
    return proc


# ── Step 5: Edge AI Server (port 8002) ───────────────────────────────────────

def start_edge_server(env: dict) -> subprocess.Popen:
    """Launch edge_server/api/server.py as a subprocess."""
    logger.info("──── [STEP 5] Starting Edge AI Server on port 8002 …")
    proc = subprocess.Popen(
        [sys.executable, "edge_server/api/server.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        text=True,
    )
    def _relay(p):
        for line in p.stdout:
            print(f"  [server]  {line}", end="")
    threading.Thread(target=_relay, args=(proc,), daemon=True).start()

    time.sleep(4)
    if proc.poll() is not None:
        logger.error("  ✗ Edge Server exited prematurely (code %s).", proc.returncode)
    else:
        logger.info("  ✓ Edge AI Server:  RUNNING  → http://localhost:8002")
        logger.info("     Dashboard     → http://localhost:8002/app/index.html")
        logger.info("     API Docs      → http://localhost:8002/docs")
    return proc


# ── Step 6: Live Camera Visualization ────────────────────────────────────────

def start_live_view() -> "LiveView | None":
    """
    Imports and starts the LiveView in a background capture thread.
    The display loop must be called on the main thread later.
    Returns the LiveView instance (or None if headless).
    """
    logger.info("──── [STEP 6] Starting Live Camera Visualization …")
    try:
        from camera.live_view import LiveView
        lv = LiveView(line_id=os.environ.get("DREAMVISION_LINE_ID", "L1"))
        lv.start()
        logger.info("  ✓ Live View:   STARTED  (window: 'DreamVision Thermal Feed')")
        return lv
    except Exception as exc:
        logger.warning("  ⚠ Live View could not start: %s", exc)
        return None


# ── System monitor ────────────────────────────────────────────────────────────

def _monitor_processes(procs: dict, env: dict):
    """
    Watches child processes and restarts them if they die unexpectedly.
    Runs in a background daemon thread.
    """
    restart_delay = 5
    restartable   = {"capture": ("main_api.py",),
                     "server":  ("edge_server/api/server.py",)}

    while True:
        time.sleep(2)
        for name, proc in list(procs.items()):
            if proc.poll() is not None:
                logger.warning("  [monitor] '%s' process died — restarting in %ds …",
                               name, restart_delay)
                time.sleep(restart_delay)
                new_proc = subprocess.Popen(
                    [sys.executable, *restartable[name]],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1, text=True,
                )
                def _relay(p, nm=name):
                    for line in p.stdout:
                        print(f"  [{nm}] {line}", end="")
                threading.Thread(target=_relay, args=(new_proc,), daemon=True).start()
                procs[name] = new_proc
                logger.info("  [monitor] '%s' restarted (PID %d).", name, new_proc.pid)


# ── Demo smoke test ───────────────────────────────────────────────────────────

def _run_demo_inspection():
    """
    After the servers are up, fire a single simulated inspection through the
    entire pipeline so the operator can see the system working immediately.
    """
    import base64
    import requests
    import numpy as np
    import cv2

    logger.info("──── [DEMO] Running simulated inspection …")
    try:
        # Create a synthetic thermal frame
        frame = np.random.uniform(100, 850, (64, 64)).astype(np.float32)
        _, buf = cv2.imencode(".jpg", (frame / 850 * 255).astype(np.uint8))
        b64 = base64.b64encode(buf).decode()

        resp = requests.post(
            "http://localhost:8002/inspect",
            json={
                "device_id": "DV-DEMO-01",
                "thermal_image": b64,
                "timestamp": datetime.now().isoformat(),
            },
            timeout=10,
        )
        if resp.status_code == 200:
            r = resp.json()
            logger.info("  ✓ Demo inspection OK — UID: %s | Status: %s | Temp: %.1f°C",
                        r.get("part_uid"), r.get("status"), r.get("temperature", 0))
        else:
            logger.warning("  ⚠ Demo inspection returned HTTP %d", resp.status_code)
    except Exception as exc:
        logger.warning("  ⚠ Demo inspection failed: %s", exc)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(BANNER)
    logger.info("DreamVision Platform starting …  [%s]", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("Camera backend: %s", os.environ.get("DREAMVISION_CAMERA_BACKEND"))
    logger.info("Line ID:        %s", os.environ.get("DREAMVISION_LINE_ID", "L1"))
    print()

    # ── 1-3: Databases and dataset
    if not step_databases():
        logger.error("Critical dependency failure.  Aborting.")
        sys.exit(1)
    step_dataset()
    print()

    # ── Build child-process environment
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))

    # ── 4-5: Server processes
    capture_proc = start_capture_api(env)
    server_proc  = start_edge_server(env)
    print()

    # ── 6: Live view (background capture thread)
    live_view = start_live_view()
    print()

    # ── Start process monitor daemon
    procs_dict = {"capture": capture_proc, "server": server_proc}
    threading.Thread(
        target=_monitor_processes, args=(procs_dict, env), daemon=True
    ).start()

    # ── Run a demo inspection once servers settle
    time.sleep(3)
    _run_demo_inspection()
    print()

    logger.info("=" * 55)
    logger.info("  DreamVision Platform is RUNNING")
    logger.info("  Dashboard  → http://localhost:8002/app/index.html")
    logger.info("  API Docs   → http://localhost:8002/docs")
    logger.info("  Stream     → http://localhost:8001/stream")
    logger.info("  Press Ctrl-C to shut down all services")
    logger.info("=" * 55)
    print()

    try:
        if live_view:
            # Blocking OpenCV display loop on the main thread
            live_view.run_display_loop()
        else:
            # Headless: just keep the main thread alive
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down DreamVision …")
        if live_view:
            live_view.stop()
        for name, proc in procs_dict.items():
            try:
                proc.terminate()
                proc.wait(timeout=5)
                logger.info("  Stopped %s (PID %d).", name, proc.pid)
            except Exception:
                pass
        logger.info("DreamVision shutdown complete.")


if __name__ == "__main__":
    main()
