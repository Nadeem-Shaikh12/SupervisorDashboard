"""
main_capture.py
================
DreamVision Phase-1 — Main Thermal Capture Entry Point
========================================================

Orchestrates the full live-capture pipeline:
  1. Initialise logging and storage directories
  2. Open the thermal camera (backend selected in capture/config.py)
  3. Optionally open the RGB camera
  4. Loop:
       a. Grab a thermal frame
       b. Process → heatmap + stats + status
       c. Display live thermal feed in an OpenCV window
       d. Auto-save every N frames (configurable)
       e. Allow manual save with 's' key
  5. Handle errors gracefully; clean up on 'q' / Ctrl-C

Usage
-----
    # Run with the simulator (no hardware needed)
    python main_capture.py

    # Use a real camera backend
    DREAMVISION_CAMERA_BACKEND=MLX90640 python main_capture.py

    # Force a specific device ID
    DREAMVISION_DEVICE_ID=DreamVision-02 python main_capture.py
"""

import logging
import signal
import sys
from datetime import datetime

import cv2

# Capture package (local)
from camera import (
    setup_logging,
    build_camera,
    RGBCamera,
    ThermalProcessor,
    ensure_directories,
    save_thermal_image,
    save_rgb_image,
    append_metadata,
    next_frame_id,
)
import camera.config as cfg

# ---------------------------------------------------------------------------
# Signal handler for graceful shutdown on SIGTERM / SIGINT
# ---------------------------------------------------------------------------

_shutdown = False

def _handle_signal(sig, frame):
    global _shutdown
    _shutdown = True
    print("\n[SHUTDOWN] Signal received – stopping capture loop …")

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ---------------------------------------------------------------------------
# Main capture loop
# ---------------------------------------------------------------------------

def run_capture():
    """Full thermal capture pipeline – runs until interrupted."""
    global _shutdown

    # 1. Initialise logging and directory tree
    setup_logging()
    ensure_directories()
    logger = logging.getLogger("dreamvision.main")
    logger.info("=" * 60)
    logger.info("DreamVision Phase-1 Thermal Capture")
    logger.info("Device ID   : %s", cfg.DEVICE_ID)
    logger.info("Backend     : %s", cfg.CAMERA_BACKEND)
    logger.info("Target FPS  : %d", cfg.TARGET_FPS)
    logger.info("Auto-save   : every %d frames", cfg.AUTO_SAVE_INTERVAL)
    logger.info("Data root   : %s", cfg.DATA_ROOT)
    logger.info("=" * 60)

    # 2. Build camera objects
    thermal_cam = build_camera()
    rgb_cam     = RGBCamera() if cfg.RGB_ENABLED else None
    processor   = ThermalProcessor()

    frame_count   = 0
    saved_count   = 0
    error_count   = 0
    MAX_ERRORS    = 10      # consecutive frame errors before hard exit

    try:
        # 3. Open cameras
        logger.info("Opening thermal camera …")
        thermal_cam.open()

        if rgb_cam:
            logger.info("Opening RGB camera …")
            rgb_cam.open()

        logger.info("Camera(s) ready.  Press 's' to save, 'q' to quit.")

        cv2.namedWindow("DreamVision – Live Thermal Feed", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("DreamVision – Live Thermal Feed",
                         cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT)

        # 4. Capture loop
        while not _shutdown:
            # ── Grab thermal frame ─────────────────────────────────────
            try:
                raw_frame = thermal_cam.next_frame()
            except Exception as exc:
                error_count += 1
                logger.error("Camera.next_frame() raised: %s (%d/%d)",
                             exc, error_count, MAX_ERRORS)
                if error_count >= MAX_ERRORS:
                    logger.critical("Too many consecutive errors. Exiting.")
                    break
                continue

            if raw_frame is None:
                error_count += 1
                logger.warning("No frame returned (%d/%d).", error_count, MAX_ERRORS)
                if error_count >= MAX_ERRORS:
                    logger.critical("Too many consecutive None frames. Exiting.")
                    break
                continue

            error_count = 0   # reset on successful frame
            frame_count += 1

            # ── Process ────────────────────────────────────────────────
            try:
                result = processor.process(raw_frame)
            except Exception as exc:
                logger.error("Processing error on frame %d: %s", frame_count, exc)
                continue

            # ── Display ────────────────────────────────────────────────
            try:
                cv2.imshow("DreamVision – Live Thermal Feed", result.heatmap_bgr)
            except Exception as exc:
                logger.warning("Display error: %s (headless environment?)", exc)

            # ── Auto-save ──────────────────────────────────────────────
            do_save = (cfg.AUTO_SAVE_INTERVAL > 0 and
                       frame_count % cfg.AUTO_SAVE_INTERVAL == 0)

            # ── Keyboard input ─────────────────────────────────────────
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("'q' pressed – exiting capture loop.")
                break
            elif key == ord('s'):
                logger.info("Manual save triggered by user.")
                do_save = True

            # ── Save frame ─────────────────────────────────────────────
            if do_save:
                try:
                    ts        = datetime.now()
                    frame_id  = next_frame_id()
                    img_path  = save_thermal_image(result.heatmap_bgr, frame_id, ts)
                    rgb_path  = None

                    if rgb_cam:
                        rgb_bgr = rgb_cam.read()
                        if rgb_bgr is not None:
                            rgb_path = save_rgb_image(rgb_bgr, frame_id, ts)
                        else:
                            logger.warning("RGB frame is None – skipping RGB save.")

                    append_metadata(
                        frame_id=frame_id,
                        timestamp=ts,
                        stats_dict=result.stats.to_dict(),
                        image_path=img_path,
                        status=result.status,
                        rgb_image_path=rgb_path,
                    )
                    saved_count += 1

                except Exception as exc:
                    logger.error("Storage error on frame %d: %s", frame_count, exc)

    finally:
        # 5. Clean up
        logger.info("Closing cameras …")
        try:
            thermal_cam.close()
        except Exception as exc:
            logger.warning("Error closing thermal camera: %s", exc)

        if rgb_cam:
            try:
                rgb_cam.close()
            except Exception as exc:
                logger.warning("Error closing RGB camera: %s", exc)

        cv2.destroyAllWindows()

        logger.info("─" * 60)
        logger.info("Session complete.")
        logger.info("  Frames captured : %d", frame_count)
        logger.info("  Frames saved    : %d", saved_count)
        logger.info("─" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_capture()
