"""
dashboard/api/dashboard_routes.py
==================================
Routes extending the Edge Server to feed the Web Dashboard UI.
Links verification and analytics queries.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from database.db import get_inspection_by_id
from database.verification_manager import verify_inspection, search_inspections, filter_inspections
from analytics.production_stats import calculate_production_stats

dashboard_router = APIRouter(prefix="/dashboard", tags=["Supervisor Dashboard"])

class VerifyRequest(BaseModel):
    verified_status: str
    verified_by: str

@dashboard_router.get("/inspections")
def get_inspections(search: Optional[str] = None, status: Optional[str] = None):
    """Returns a list of inspections based on optional filtering or free-text search."""
    if search:
        return search_inspections(search)
    elif status:
        return filter_inspections(status)
    return filter_inspections() # All limit=50

@dashboard_router.get("/inspection/{part_uid}")
def get_single_inspection(part_uid: str):
    """Retrieve fine-grained details for rendering the item analysis popup."""
    row = get_inspection_by_id(part_uid)
    if not row:
        raise HTTPException(status_code=404, detail="UID Not Found")
    return row

@dashboard_router.get("/stats")
def get_statistics():
    """Returns high-level global aggregations resolving UI stats bars and charts."""
    stats = calculate_production_stats()
    # Harmonize with script.js requirements
    # Yield = (OK + WARNING) / Total
    total = stats["total_inspections"]
    yield_val = 0
    defect_val = 0
    if total > 0:
        pass_count = stats["ok_count"] + stats["warning_count"]
        yield_val = round((pass_count / total) * 100, 1)
        defect_val = round((stats["nok_count"] / total) * 100, 1)
    
    stats["yield_percent"] = yield_val
    stats["defect_percent"] = defect_val
    return stats

@dashboard_router.get("/stream")
async def sse_stream():
    """
    Simplified SSE stream for dashboard updates.
    Yields a ping every 30s to keep connection alive.
    In a real system, this would be tied to internal event brokers.
    """
    from fastapi.responses import StreamingResponse
    import asyncio

    async def event_generator():
        while True:
            # Simple keep-alive
            yield f"data: {{\"connected\": true}}\n\n"
            await asyncio.sleep(30)

    # Note: Modern script.js handles polling now, but we keep this for EventSource compatibility
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@dashboard_router.post("/verify/{part_uid}")
def post_verification(part_uid: str, req: VerifyRequest):
    """
    Called by supervisors overriding or accepting automated Edge decisions.
    Requires Role checking (prototype auth handled at frontend or simplified here).
    """
    valid_states = ["OK", "WARNING", "NOK"]
    if req.verified_status not in valid_states:
        raise HTTPException(status_code=400, detail=f"Invalid verified status. Choose {valid_states}")

    success = verify_inspection(
        part_uid=part_uid,
        verified_status=req.verified_status,
        verified_by=req.verified_by
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Update failed. ID not matched.")
        
    updated = get_inspection_by_id(part_uid)
    return {"message": "Verification Successful", "updated": updated}

@dashboard_router.get("/report/csv")
def export_csv_report():
    """Generates a CSV report summarizing the operations."""
    from fastapi.responses import PlainTextResponse
    import csv
    import io
    from database.db import get_all_inspections
    
    inspections = get_all_inspections()
    if not inspections:
        return PlainTextResponse("No records found", status_code=404)
        
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=inspections[0].keys())
    writer.writeheader()
    writer.writerows(inspections)
    
    headers = {
        'Content-Disposition': 'attachment; filename="factory_report.csv"'
    }
    return PlainTextResponse(output.getvalue(), headers=headers, media_type="text/csv")
