from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from backend.services.case_store import get_case
from backend.services.report_generator import build_pdf

router = APIRouter(prefix="/api/v1", tags=["reports"])

@router.get("/cases/{case_id}/report.pdf")
def download_report(case_id: str, inline: bool = Query(False)):
    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case ID not found")
    pdf = build_pdf(case)
    disposition = "inline" if inline else "attachment"
    return StreamingResponse(
        pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="Aletheia_{case_id}.pdf"'}
    )
