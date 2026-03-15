"""
analytics/production_stats.py
==============================
Computes production analytics across the tracked inspections table,
delivering insights into defect rates, component trends, and quality.
"""

from database.db import get_connection

def calculate_production_stats() -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Base count metrics
        cursor.execute("SELECT COUNT(*) AS total FROM parts_inspection")
        total_parts = cursor.fetchone()["total"]
        
        cursor.execute("SELECT status, COUNT(*) AS count FROM parts_inspection GROUP BY status")
        counts = {"OK": 0, "WARNING": 0, "NOK": 0}
        for row in cursor.fetchall():
            counts[row["status"]] = row["count"]
            
        rate = 0.0
        if total_parts > 0:
            rate = round(((counts["NOK"] + counts["WARNING"]) / total_parts) * 100, 2)
            
        # Top defective
        cursor.execute("""
            SELECT component_name, COUNT(*) as defect_count 
            FROM parts_inspection 
            WHERE status != 'OK'
            GROUP BY component_name 
            ORDER BY defect_count DESC LIMIT 5
        """)
        top_defective = [{"component": row["component_name"], "defects": row["defect_count"]} for row in cursor.fetchall()]
        
        # Averages
        cursor.execute("""
            SELECT component_name, AVG(temperature) as avg_temp
            FROM parts_inspection
            GROUP BY component_name
        """)
        averages = [{"component": row["component_name"], "average_temperature": round(row["avg_temp"], 1)} for row in cursor.fetchall()]

        return {
            "total_inspections": total_parts,
            "ok_count": counts["OK"],
            "warning_count": counts["WARNING"],
            "nok_count": counts["NOK"],
            "defect_rate_percent": rate,
            "top_defective_components": top_defective,
            "average_temperatures": averages
        }
