"""
analytics/anomaly_detection.py
===============================
Detects anomalous inspection values using simple Z-score / moving average deviation.
"""
import logging
from database.db import get_connection
from database.anomaly_manager import insert_anomaly

logger = logging.getLogger("dreamvision.analytics.anomaly")

def detect_anomaly(component_name: str, temperature: float, timestamp: str):
    """
    Checks if the given temperature is an anomaly based on the last 50 inspections.
    If it is, it stores the anomaly in the database.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        # Fetch last 50 temperatures for this component
        cursor.execute("""
            SELECT temperature FROM parts_inspection
            WHERE component_name = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (component_name,))
        rows = cursor.fetchall()

    if len(rows) < 10:
        return # Not enough data to confidently assert an anomaly

    temps = [r['temperature'] for r in rows]
    mean_temp = sum(temps) / len(temps)
    variance = sum((t - mean_temp) ** 2 for t in temps) / len(temps)
    std_dev = variance ** 0.5

    if std_dev == 0:
        return

    z_score = abs(temperature - mean_temp) / std_dev

    # Z-Score > 3 is generally considered an anomaly (3 standard deviations)
    if z_score > 3.0:
        description = f"Temperature {temperature}°C deviates significantly. Mean: {mean_temp:.1f}°C, StdDev: {std_dev:.1f}, Z-Score: {z_score:.2f}."
        logger.warning(f"ANOMALY DETECTED: {component_name} - {description}")
        insert_anomaly(timestamp, component_name, "Temperature Spike", description)
