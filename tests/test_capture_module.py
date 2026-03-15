"""
tests/test_capture_module.py
=============================
DreamVision Phase-1 — Integration Test Script
==============================================

This script exercises all major components of the capture module WITHOUT
requiring any physical hardware (it forces SIMULATOR mode).

What it tests
-------------
  1. Logging initialisation
  2. Directory structure creation
  3. Camera (simulator) open / next_frame / close
  4. ThermalProcessor.process() output structure and validity
  5. Image save functions (thermal + RGB placeholder)
  6. Metadata logging (append + read-back)
  7. Frame-ID counter (uniqueness across calls)
  8. Live optical feed (5 frames displayed then window auto-closes)

Run
---
    python tests/test_capture_module.py

Expected output: all checks print PASS; a thermal feed window appears
briefly then closes; saved images appear in data/thermal_images/.
"""

import os
import sys
import time
import tempfile

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Force simulator backend ────────────────────────────────────────────────
os.environ["DREAMVISION_CAMERA_BACKEND"] = "SIMULATOR"
os.environ["DREAMVISION_DEVICE_ID"]      = "TEST-DEVICE-01"

import numpy as np
import cv2

# Import *after* setting env vars so config picks them up
from camera import (
    setup_logging,
    ensure_directories,
    build_camera,
    ThermalProcessor,
    save_thermal_image,
    save_rgb_image,
    append_metadata,
    next_frame_id,
    read_metadata_all,
)
import camera.config as cfg

# ── Helpers ────────────────────────────────────────────────────────────────

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_failures = []


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  [{PASS}] {label}")
    else:
        print(f"  [{FAIL}] {label}", f"({detail})" if detail else "")
        _failures.append(label)


# ── Tests ──────────────────────────────────────────────────────────────────

def test_logging():
    print("\n[1] Logging initialisation")
    try:
        setup_logging()
        import logging
        log = logging.getLogger("dreamvision.test")
        log.info("Logging test message")
        check("setup_logging() runs without error", True)
    except Exception as e:
        check("setup_logging() runs without error", False, str(e))


def test_directories():
    print("\n[2] Directory structure")
    ensure_directories()
    check("data/thermal_images exists", os.path.isdir(cfg.THERMAL_IMAGE_DIR))
    check("data/rgb_images    exists", os.path.isdir(cfg.RGB_IMAGE_DIR))
    check("data/logs          exists", os.path.isdir(cfg.LOG_DIR))


def test_camera():
    print("\n[3] Simulator camera — open / next_frame / close")
    cam = build_camera()
    check("build_camera() returns an object", cam is not None)

    try:
        cam.open()
        check("camera.open() succeeds", True)
    except Exception as e:
        check("camera.open() succeeds", False, str(e))
        return None

    frame = cam.next_frame()
    check("next_frame() returns a numpy array",
          isinstance(frame, np.ndarray),
          f"got {type(frame)}")
    check("frame dtype is float32",
          frame is not None and frame.dtype == np.float32)
    check("frame is 2-dimensional",
          frame is not None and frame.ndim == 2)
    check("frame shape has positive dims",
          frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0)

    cam.close()
    check("camera.close() runs", True)
    return frame


def test_processor(frame: np.ndarray):
    print("\n[4] ThermalProcessor")
    proc = ThermalProcessor()
    result = proc.process(frame)

    check("process() returns a ProcessedFrame",
          result is not None)
    check("heatmap_bgr is uint8 ndarray",
          isinstance(result.heatmap_bgr, np.ndarray) and
          result.heatmap_bgr.dtype == np.uint8)
    check("heatmap_bgr is 3-channel",
          result.heatmap_bgr.ndim == 3 and result.heatmap_bgr.shape[2] == 3)
    check("stats.max_temp > stats.min_temp",
          result.stats.max_temp > result.stats.min_temp)
    check("status is a known value",
          result.status in ("SAFE", "WARNING", "DANGER", "FIRE RISK"))
    return result


def test_storage(result):
    print("\n[5] Image storage")
    from datetime import datetime
    ts  = datetime.now()
    fid = next_frame_id()
    check("next_frame_id() returns a string", isinstance(fid, str))
    check("frame ID is non-empty", bool(fid))

    # Thermal save
    try:
        path = save_thermal_image(result.heatmap_bgr, fid, ts)
        check("save_thermal_image() returns a path", bool(path))
        abs_path = os.path.join(cfg.THERMAL_IMAGE_DIR,
                                os.path.basename(path))
        check("saved PNG file exists on disk", os.path.isfile(abs_path),
              abs_path)
    except Exception as e:
        check("save_thermal_image() succeeds", False, str(e))
        path = "N/A"

    # RGB save (use a synthetic green image as placeholder)
    try:
        fake_rgb = np.zeros((480, 640, 3), dtype=np.uint8)
        fake_rgb[:, :, 1] = 128   # green channel
        rgb_path = save_rgb_image(fake_rgb, fid, ts)
        check("save_rgb_image() returns a path", bool(rgb_path))
    except Exception as e:
        check("save_rgb_image() succeeds", False, str(e))
        rgb_path = None

    return fid, ts, path, rgb_path


def test_metadata(fid, ts, img_path, rgb_path, result):
    print("\n[6] Metadata logging")
    from datetime import datetime
    record = append_metadata(
        frame_id=fid,
        timestamp=ts,
        stats_dict=result.stats.to_dict(),
        image_path=img_path,
        status=result.status,
        rgb_image_path=rgb_path,
    )
    check("append_metadata() returns a dict", isinstance(record, dict))
    check("record contains 'frame_id'",   "frame_id"  in record)
    check("record contains 'max_temp'",   "max_temp"  in record)
    check("record contains 'status'",     "status"    in record)
    check("record contains 'image_path'", "image_path" in record)
    check("record device_id matches config",
          record.get("device_id") == cfg.DEVICE_ID)

    all_records = read_metadata_all()
    check("read_metadata_all() returns a list", isinstance(all_records, list))
    check("saved record found in read-back",
          any(r.get("frame_id") == fid for r in all_records))


def test_unique_frame_ids():
    print("\n[7] Frame ID uniqueness")
    ids = [next_frame_id() for _ in range(5)]
    check("5 sequential IDs are all unique", len(set(ids)) == 5,
          str(ids))


def test_live_feed(n_frames: int = 5):
    """Display n_frames of live thermal feed, then auto-close."""
    print(f"\n[8] Live feed display ({n_frames} frames — window will close automatically)")
    cam   = build_camera()
    proc  = ThermalProcessor()
    shown = 0

    try:
        cam.open()
        cv2.namedWindow("DreamVision TEST Feed", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("DreamVision TEST Feed", 640, 480)

        for i in range(n_frames):
            frame = cam.next_frame()
            if frame is None:
                continue
            result = proc.process(frame)
            # Add test overlay
            img = result.heatmap_bgr.copy()
            cv2.putText(img, f"TEST FRAME {i+1}/{n_frames}",
                        (8, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.imshow("DreamVision TEST Feed", img)
            cv2.waitKey(200)
            shown += 1

    except Exception as e:
        check("Live feed displayed without error", False, str(e))
    finally:
        cam.close()
        cv2.destroyAllWindows()

    check(f"All {n_frames} test frames displayed", shown == n_frames,
          f"shown={shown}")


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  DreamVision Phase-1 — Capture Module Test Suite")
    print("=" * 60)

    test_logging()
    test_directories()
    test_unique_frame_ids()

    frame = test_camera()
    if frame is not None:
        result = test_processor(frame)
        if result is not None:
            fid, ts, img_path, rgb_path = test_storage(result)
            test_metadata(fid, ts, img_path, rgb_path, result)

    test_live_feed(n_frames=5)

    print("\n" + "=" * 60)
    if _failures:
        print(f"  \033[31m{len(_failures)} test(s) FAILED:\033[0m")
        for f in _failures:
            print(f"    [FAIL] {f}")
        sys.exit(1)
    else:
        print("  \033[32mAll tests PASSED [OK]\033[0m")
        print("=" * 60)
        sys.exit(0)
