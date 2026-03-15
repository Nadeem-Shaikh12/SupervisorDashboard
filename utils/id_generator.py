"""
utils/id_generator.py
=======================
UPGRADE 3 — Improved Part UID Format

New UID format:
    DV-<line_id>-<YYYYMMDD>-<05d sequence>

Example:
    DV-L1-20260315-00012

  DV      = DreamVision
  L1      = Production line identifier (configurable via DREAMVISION_LINE_ID env var)
  YYYYMMDD = Date the inspection occurred
  00012   = Zero-padded, per-day incrementing sequence number
"""

import os
import threading
from datetime import datetime

# Production-line ID can be overridden via environment variable
LINE_ID = os.environ.get("DREAMVISION_LINE_ID", "L1")

_lock      = threading.Lock()
_seq       = 0
_last_date = ""


def generate_part_uid(line_id: str | None = None) -> str:
    """
    Generate a unique, human-readable part UID.

    Args:
        line_id: Override the default line ID for this call.
                 If None the module-level LINE_ID is used.

    Returns:
        str: e.g. ``"DV-L1-20260315-00012"``
    """
    global _seq, _last_date

    _line = line_id or LINE_ID

    with _lock:
        now_date = datetime.now().strftime("%Y%m%d")

        # Reset counter at midnight
        if now_date != _last_date:
            _last_date = now_date
            _seq = 0

        _seq += 1
        return f"DV-{_line}-{now_date}-{_seq:05d}"


def reset_sequence():
    """Force-reset the sequence counter (useful in tests)."""
    global _seq, _last_date
    with _lock:
        _seq = 0
        _last_date = ""


if __name__ == "__main__":
    # Quick smoke-test
    for _ in range(5):
        print(generate_part_uid())
