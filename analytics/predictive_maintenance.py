"""
analytics/predictive_maintenance.py
===================================
Analyzes historical inspection data to predict machine component wear resulting
in rising temperature trends causing defects or failures.
"""
import logging
from typing import Optional, Dict
from database.db import get_connection

logger = logging.getLogger("dreamvision.analytics.maintenance")

def run_predictive_maintenance(component_name: str, current_temp: float) -> Optional[Dict]:
    """
    Computes average temp for the last 500 inspections vs last 10 inspections
    to determine if there's a problematic upward trend requiring service.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # We need enough historical data to make a baseline. Let's do a fast count first.
        cursor.execute("SELECT COUNT(*) as cnt FROM parts_inspection WHERE component_name = ?", (component_name,))
        if cursor.fetchone()['cnt'] < 20:
            return None # Not enough history

        # Get long term mean (max 500 records)
        cursor.execute("""
            SELECT AVG(temperature) as lt_mean FROM (
                SELECT temperature FROM parts_inspection 
                WHERE component_name = ? ORDER BY timestamp DESC LIMIT 500
            )
        """, (component_name,))
        lt_mean = cursor.fetchone()['lt_mean']

        # Get short term mean (last 5 records, not including current)
        cursor.execute("""
            SELECT AVG(temperature) as st_mean FROM (
                SELECT temperature FROM parts_inspection 
                WHERE component_name = ? ORDER BY timestamp DESC LIMIT 5
            )
        """, (component_name,))
        st_mean = cursor.fetchone()['st_mean']

        if not lt_mean or not st_mean:
            return None

        # Check for consistent rising trend.
        # e.g., if short term is 5% higher than long term avg
        diff_percent = ((st_mean - lt_mean) / lt_mean) * 100
        
        if diff_percent > 5.0:
            issue_desc = f"Rising temperature trend detected (+{diff_percent:.1f}% vs baseline)"
            logger.warning(f"MAINTENANCE ALERT: {component_name} - {issue_desc}")
            
            return {
                "machine_line": "Factory-Line-A",  # Mocked machine line id
                "component": component_name,
                "issue": issue_desc,
                "recommendation": "Check furnace or cooling calibration",
                "lt_mean": round(lt_mean, 2),
                "st_mean": round(st_mean, 2),
            }
            
        return None
