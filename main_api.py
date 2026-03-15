"""
main_api.py
============
DreamVision Phase-1 — Local FastAPI Capture Server
====================================================

Runs a lightweight HTTP API alongside the thermal camera so that the existing
DreamVision dashboard (or any other consumer) can pull live data without
modifying the upstream backend.

Endpoints
---------
  GET  /status          – device health and latest frame stats
  GET  /frame/latest    – latest processed frame as JPEG (Base64 JSON)
  GET  /metadata        – all saved frame metadata records
  POST /capture         – trigger an immediate frame save
  GET  /stream          – MJPEG live stream (direct browser-viewable)

Run
---
    python main_api.py
    # Then open http://localhost:8001/stream  in your browser

Or programmatically:
    DREAMVISION_CAMERA_BACKEND=SIMULATOR python main_api.py
"""

import asyncio
import base64
import logging
import os
import threading
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

# DreamVision capture package
from camera import (
    setup_logging, build_camera, RGBCamera,
    ThermalProcessor, ensure_directories,
    save_thermal_image, save_rgb_image,
    append_metadata, next_frame_id,
    read_metadata_all,
)
import camera.config as cfg

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------

setup_logging()
ensure_directories()

app = FastAPI(
    title="DreamVision Phase-1 Capture API",
    description="Local thermal camera capture API for the DreamVision smart-factory prototype.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("dreamvision.api")

# ---------------------------------------------------------------------------
# Shared state (written by background capture thread, read by API handlers)
# ---------------------------------------------------------------------------

class _CaptureState:
    lock          = threading.Lock()
    latest_frame  : Optional[np.ndarray] = None   # BGR heatmap
    latest_stats  : Optional[dict]       = None
    latest_status : str                  = "UNKNOWN"
    frame_count   : int                  = 0
    last_ts       : Optional[datetime]   = None
    running       : bool                 = False

state = _CaptureState()


# ---------------------------------------------------------------------------
# Background capture thread
# ---------------------------------------------------------------------------

def _capture_loop():
    """Runs in a daemon thread; continuously updates shared state."""
    logger.info("[Capture Thread] Starting …")
    thermal_cam = build_camera()
    rgb_cam     = RGBCamera() if cfg.RGB_ENABLED else None
    processor   = ThermalProcessor()

    thermal_cam.open()
    if rgb_cam:
        rgb_cam.open()

    state.running = True
    frame_num = 0

    try:
        while state.running:
            raw = thermal_cam.next_frame()
            if raw is None:
                continue

            result = processor.process(raw)
            frame_num += 1

            with state.lock:
                state.latest_frame  = result.heatmap_bgr.copy()
                state.latest_stats  = result.stats.to_dict()
                state.latest_status = result.status
                state.frame_count   = frame_num
                state.last_ts       = datetime.now()

<<<<<<< HEAD
            # Auto-save & Post to Edge Server
            if cfg.AUTO_SAVE_INTERVAL > 0 and frame_num % cfg.AUTO_SAVE_INTERVAL == 0:
                _save_current_frame(result, rgb_cam)


=======
            # Auto-save
            if cfg.AUTO_SAVE_INTERVAL > 0 and frame_num % cfg.AUTO_SAVE_INTERVAL == 0:
                _save_current_frame(result, rgb_cam)

>>>>>>> origin/main
    except Exception as exc:
        logger.exception("[Capture Thread] Unhandled error: %s", exc)
    finally:
        thermal_cam.close()
        if rgb_cam:
            rgb_cam.close()
        state.running = False
        logger.info("[Capture Thread] Stopped after %d frames.", frame_num)


def _save_current_frame(result, rgb_cam: Optional[RGBCamera]) -> dict:
    """Persist the given ProcessedFrame and return the metadata record."""
    ts       = datetime.now()
    fid      = next_frame_id()
    img_path = save_thermal_image(result.heatmap_bgr, fid, ts)
    rgb_path = None
    if rgb_cam:
        rgb_bgr = rgb_cam.read()
        if rgb_bgr is not None:
            rgb_path = save_rgb_image(rgb_bgr, fid, ts)
    return append_metadata(
        frame_id=fid,
        timestamp=ts,
        stats_dict=result.stats.to_dict(),
        image_path=img_path,
        status=result.status,
        rgb_image_path=rgb_path,
    )


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
def _startup():
    t = threading.Thread(target=_capture_loop, daemon=True, name="capture-loop")
    t.start()
    logger.info("DreamVision API ready.  Capture thread started.")


@app.on_event("shutdown")
def _shutdown():
    state.running = False
    logger.info("DreamVision API shutting down.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/status", tags=["Capture"])
def get_status():
    """Health check and device status."""
    return {
        "device_id":   cfg.DEVICE_ID,
        "backend":     cfg.CAMERA_BACKEND,
        "running":     state.running,
        "frame_count": state.frame_count,
        "last_status": state.latest_status,
        "last_ts":     state.last_ts.isoformat() if state.last_ts else None,
    }


@app.get("/frame/latest", tags=["Capture"])
def get_latest_frame():
    """
    Return the latest processed thermal frame as a Base64-encoded JPEG,
    compatible with the existing DreamVision dashboard /upload format.
    """
    with state.lock:
        frame = state.latest_frame
        stats = state.latest_stats
        status = state.latest_status

    if frame is None:
        raise HTTPException(status_code=503, detail="No frame captured yet.")

    _, buf = cv2.imencode(".jpg", frame)
    b64 = base64.b64encode(buf).decode("utf-8")

    return {
        "device_id":    cfg.DEVICE_ID,
        "timestamp":    datetime.now().isoformat(timespec="seconds"),
        "status":       status,
        "temperature":  stats.get("max_temp") if stats else None,
        "thermal_image": b64,
        "stats":        stats,
    }


@app.get("/metadata", tags=["Storage"])
def get_metadata():
    """Return all saved frame metadata records."""
    return read_metadata_all()


@app.post("/capture", tags=["Capture"])
def trigger_capture():
    """
    Immediately save the current frame to disk.
    Returns the metadata record for the saved frame.
    """
    with state.lock:
        frame  = state.latest_frame
        stats  = state.latest_stats
        status = state.latest_status

    if frame is None:
        raise HTTPException(status_code=503, detail="No frame available yet.")

    # Build a minimal ProcessedFrame-like object
    class _FakeResult:
        heatmap_bgr = frame

        class _FakeStats:
            def to_dict(self_inner):
                return stats

        stats_obj = _FakeStats()

        @property
        def stats(self):
            return self.stats_obj

    ts = datetime.now()
    fid = next_frame_id()
    img_path = save_thermal_image(frame, fid, ts)
    record = append_metadata(
        frame_id=fid,
        timestamp=ts,
        stats_dict=stats or {},
        image_path=img_path,
        status=status,
    )
    return {"saved": True, "record": record}


@app.get("/stream", tags=["Capture"])
def mjpeg_stream():
    """
    MJPEG live stream.  Open this URL directly in a browser tab or
    embed it as an <img src="/stream"> in a web page.
    """
    def _generate():
        while True:
            with state.lock:
                frame = state.latest_frame

            if frame is None:
                # Send a placeholder black frame while waiting
                bk = np.zeros((cfg.DISPLAY_HEIGHT, cfg.DISPLAY_WIDTH, 3), dtype=np.uint8)
                cv2.putText(bk, "Waiting for camera...",
                            (60, cfg.DISPLAY_HEIGHT // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (100, 100, 100), 2)
                _, buf = cv2.imencode(".jpg", bk)
            else:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n"
                   + buf.tobytes()
                   + b"\r\n")

            import time
            time.sleep(cfg.LOOP_SLEEP_S)

    return StreamingResponse(
        _generate(),
        media_type="multipart/x-mixed-replace;boundary=frame",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main_api:app",
        host=cfg.API_HOST,
        port=cfg.API_PORT,
        reload=cfg.API_RELOAD,
        log_level="info",
    )
