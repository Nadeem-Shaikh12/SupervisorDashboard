"""
utils/id_generator.py
=======================
Generates a unique part ID for each inspection.
"""

from datetime import datetime
import threading

_lock = threading.Lock()
_seq = 0
_last_date = ""

def generate_part_uid() -> str:
    """
    Format: DV-{timestamp}-{sequence}
    Example: DV-20260315-0001
    """
    global _seq, _last_date
    
    with _lock:
        now_date = datetime.now().strftime("%Y%m%d")
        if now_date != _last_date:
            _last_date = now_date
            _seq = 0
            
        _seq += 1
        return f"DV-{now_date}-{_seq:04d}"
