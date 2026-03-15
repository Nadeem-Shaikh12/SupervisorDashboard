"""
edge_server/thermal/temperature_extractor.py
=============================================
Module to extract maximum temperature and thermal insights from image.
"""

import logging
import cv2
import numpy as np
from camera.image_processing import ThermalProcessor

logger = logging.getLogger("dreamvision.thermal")
_processor = ThermalProcessor()

def extract_temperature(thermal_float_array: np.ndarray):
    """
    Extract temperature stats and an annotated visual heatmap 
    from the raw thermal float32 array leveraging Phase-1's processor.
    """
    # Using the ThermalProcessor from Phase-1
    result = _processor.process(thermal_float_array)
    
    logger.info(f"Thermal extraction complete: max_temp={result.stats.max_temp}°C")
    return result.stats.max_temp, result.heatmap_bgr
