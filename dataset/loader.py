"""
dataset/loader.py
==================
Reads a CSV components file and UPSERTs its data into our edge SQLite db.
"""

import csv
import logging
import os
from database.db import get_connection

logger = logging.getLogger("dreamvision.dataset")

def load_components_dataset(csv_path: str):
    """
    Parse CSV file and populate component_temperature_rules DB.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Missing dataset CSV at {csv_path}")

    # component_name, normal_temp_min_C, normal_temp_max_C, critical_temp_C, failure_temp_C
    required_cols = {
        "component_name", 
        "normal_temp_min_C", 
        "normal_temp_max_C", 
        "critical_temp_C", 
        "failure_temp_C"
    }

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        missing = required_cols - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        rows_processed = 0
        with get_connection() as conn:
            cursor = conn.cursor()
            
            for row in reader:
                # Use REPLACE INTO for UPSERT behavior in SQLite
                cursor.execute("""
                    REPLACE INTO component_temperature_rules (
                        component_name, normal_temp_min, normal_temp_max, critical_temp, failure_temp
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    row["component_name"],
                    float(row["normal_temp_min_C"]),
                    float(row["normal_temp_max_C"]),
                    float(row["critical_temp_C"]),
                    float(row["failure_temp_C"])
                ))
                rows_processed += 1
                
            conn.commit()
            
    logger.info(f"Dataset successfully loaded. {rows_processed} rule(s) inserted.")
    return rows_processed
