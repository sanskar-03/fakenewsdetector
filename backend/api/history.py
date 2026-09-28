from fastapi import APIRouter, HTTPException, Query
from backend.services.case_store import delete_case, get_case, search_cases

router = APIRouter(prefix="/api/v1", tags=["case-history"])

@router.get("/cases")
def list_cases(limit: int = Query(50, ge=1, le=100), case_id: str = Query("", max_length=100)):
    # History search intentionally searches only by exact case number.
    return {"items": search_cases(limit, case_id.strip() or None)}

@router.get("/cases/{case_id}")
def read_case(case_id: str):
    data = get_case(case_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Case ID not found")
    return data

@router.delete("/cases/{case_id}")
def remove_case(case_id: str):
    if not delete_case(case_id):
        raise HTTPException(status_code=404, detail="Case ID not found")
    return {"deleted": True, "case_id": case_id}
