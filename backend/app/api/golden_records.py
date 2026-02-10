"""Golden record endpoints."""

import io
import csv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.models import GoldenRecord, CustomerRecord
from app.schemas.schemas import GoldenRecordResponse, MergeRequest
from app.services.golden_record_service import (
    merge_records,
    promote_unmatched_to_golden,
    CUSTOMER_FIELDS,
)

router = APIRouter(prefix="/api/golden-records", tags=["Golden Records"])


@router.get("/", response_model=list[GoldenRecordResponse])
def list_golden_records(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Search by company name, email, etc."),
    db: Session = Depends(get_db),
):
    """List all golden records."""
    query = db.query(GoldenRecord)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (GoldenRecord.company_name.ilike(search_term))
            | (GoldenRecord.email.ilike(search_term))
            | (GoldenRecord.first_name.ilike(search_term))
            | (GoldenRecord.last_name.ilike(search_term))
        )

    records = query.order_by(GoldenRecord.updated_at.desc()).offset(skip).limit(limit).all()

    result = []
    for gr in records:
        source_records = db.query(CustomerRecord).filter(
            CustomerRecord.golden_record_id == gr.id
        ).all()
        gr_dict = GoldenRecordResponse.model_validate(gr)
        gr_dict.source_records = source_records
        result.append(gr_dict)

    return result


@router.get("/count")
def golden_record_count(db: Session = Depends(get_db)):
    """Get total count of golden records."""
    count = db.query(GoldenRecord).count()
    return {"count": count}


@router.get("/export")
def export_golden_records(db: Session = Depends(get_db)):
    """Export all golden records as CSV."""
    records = db.query(GoldenRecord).order_by(GoldenRecord.updated_at.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    headers = ["id"] + CUSTOMER_FIELDS + ["source_count", "created_at", "updated_at"]
    writer.writerow(headers)

    # Data rows
    for record in records:
        row = [record.id]
        for field in CUSTOMER_FIELDS:
            row.append(getattr(record, field, "") or "")
        row.extend([record.source_count, record.created_at, record.updated_at])
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=golden_records_export.csv"},
    )


@router.get("/{record_id}", response_model=GoldenRecordResponse)
def get_golden_record(record_id: str, db: Session = Depends(get_db)):
    """Get a single golden record with its source records."""
    gr = db.query(GoldenRecord).filter(GoldenRecord.id == record_id).first()
    if not gr:
        raise HTTPException(404, "Golden record not found")

    source_records = db.query(CustomerRecord).filter(
        CustomerRecord.golden_record_id == gr.id
    ).all()

    result = GoldenRecordResponse.model_validate(gr)
    result.source_records = source_records
    return result


@router.post("/merge")
def merge_match(merge_req: MergeRequest, db: Session = Depends(get_db)):
    """Merge two matched records into a golden record."""
    try:
        golden = merge_records(
            db=db,
            match_id=merge_req.match_id,
            surviving_values=merge_req.surviving_values,
        )
        return {
            "message": "Records merged successfully",
            "golden_record_id": golden.id,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/promote-unmatched")
def promote_unmatched(db: Session = Depends(get_db)):
    """Promote all unmatched records (with no pending matches) to golden records."""
    count = promote_unmatched_to_golden(db)
    return {"message": f"Promoted {count} records to golden records", "count": count}
