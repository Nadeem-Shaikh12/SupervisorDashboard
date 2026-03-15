"""
inspection_engine/pipeline.py
==============================
Main integration pipeline linking the thermal camera, rules dataset, 
evaluator, and database storage for an OK/NOK check on a component.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from database.db import fetch_rule, insert_inspection
from utils.id_generator import generate_part_uid
from inspection_engine.evaluator import evaluate_temperature
from camera.data_storage import save_thermal_image

logger = logging.getLogger("dreamvision.inspection")

class InspectionPipeline:
    """Takes a camera connection and configures it to run automated part inspections."""
    
    def __init__(self, camera_interface, thermal_processor):
        self.camera = camera_interface
        self.processor = thermal_processor

    def inspect_part(self, component_name: str) -> Dict[str, Any]:
        """
        Captures a frame, evaluates against dataset thresholds, saves image
        and inserts the record into the inspection database.
        
        Returns the inspection metadata.
        """
        # 1. Look up rule from loaded dataset
        rule = fetch_rule(component_name)
        if not rule:
            logger.error(f"Cannot inspect '{component_name}': no rules found in database.")
            raise ValueError(f"No rules found for component '{component_name}'. Have you loaded the dataset?")
            
        # 2. Capture and process thermal frame
        raw_frame = self.camera.next_frame()
        if raw_frame is None:
            raise RuntimeError("Camera failed to return a frame.")
            
        processed = self.processor.process(raw_frame)
        peak_temp = processed.stats.max_temp
        
        # 3. Apply evaluation engine logic
        status = evaluate_temperature(peak_temp, rule["normal_temp_max"], rule["failure_temp"])
        
        # 4. Generate UID and Timestamp
        part_uid = generate_part_uid()
        ts = datetime.now()
        ts_str = ts.isoformat(timespec="seconds")
        
        # 5. Save annotated image using camera module storage wrapper
        # The storage wrapper places this in data/thermal_images/
        image_path = save_thermal_image(processed.heatmap_bgr, part_uid, ts)
        
        # 6. Database Storage
        insert_inspection(part_uid, component_name, peak_temp, status, image_path, ts_str)
        
        # 7. Construct Result Record
        record = {
            "part_uid": part_uid,
            "component_name": component_name,
            "temperature": round(peak_temp, 2),
            "status": status,
            "image_path": image_path,
            "timestamp": ts_str
        }
        
        logger.info(f"Inspected '{component_name}' -> UID: {part_uid} | Temp: {round(peak_temp, 2)}°C | Status: {status}")
        return record
