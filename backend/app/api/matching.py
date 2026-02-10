"""Match candidate endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.models import MatchCandidate, MatchStatus, CustomerRecord
from app.schemas.schemas import (
    MatchCandidateResponse,
    MatchReviewRequest,
    MatchingConfig,
    CustomerRecordResponse,
)
from app.services.matching_engine import find_matches

router = APIRouter(prefix="/api/matches", tags=["Matching"])


@router.post("/run")
def run_matching(
    config: Optional[MatchingConfig] = None,
    source_id: Optional[str] = Query(None, description="Only match records from this source"),
    db: Session = Depends(get_db),
):
    """
    Run the matching engine to find duplicate candidates.
    Optionally scope to a specific data source.
    """
    cfg = config or MatchingConfig()
    matches = find_matches(
        db=db,
        source_id=source_id,
        threshold=cfg.threshold,
        field_weights=cfg.field_weights,
    )
    return {
        "message": f"Found {len(matches)} match candidates",
        "match_count": len(matches),
    }


@router.get("/", response_model=list[MatchCandidateResponse])
def list_matches(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, merged"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List match candidates with optional status filter."""
    query = db.query(MatchCandidate)

    if status:
        try:
            status_enum = MatchStatus(status)
            query = query.filter(MatchCandidate.status == status_enum)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    matches = query.order_by(MatchCandidate.overall_score.desc()).offset(skip).limit(limit).all()

    # Enrich with record data
    result = []
    for match in matches:
        record_a = db.query(CustomerRecord).filter(CustomerRecord.id == match.record_a_id).first()
        record_b = db.query(CustomerRecord).filter(CustomerRecord.id == match.record_b_id).first()

        match_dict = {
            "id": match.id,
            "record_a_id": match.record_a_id,
            "record_b_id": match.record_b_id,
            "overall_score": match.overall_score,
            "field_scores": match.field_scores,
            "match_method": match.match_method,
            "status": match.status.value if isinstance(match.status, MatchStatus) else match.status,
            "reviewed_at": match.reviewed_at,
            "notes": match.notes,
            "created_at": match.created_at,
            "record_a": record_a,
            "record_b": record_b,
        }
        result.append(MatchCandidateResponse(**match_dict))

    return result


@router.get("/stats")
def match_stats(db: Session = Depends(get_db)):
    """Get match statistics."""
    total = db.query(MatchCandidate).count()
    pending = db.query(MatchCandidate).filter(MatchCandidate.status == MatchStatus.PENDING).count()
    approved = db.query(MatchCandidate).filter(MatchCandidate.status == MatchStatus.APPROVED).count()
    rejected = db.query(MatchCandidate).filter(MatchCandidate.status == MatchStatus.REJECTED).count()
    merged = db.query(MatchCandidate).filter(MatchCandidate.status == MatchStatus.MERGED).count()

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "merged": merged,
    }


@router.get("/{match_id}", response_model=MatchCandidateResponse)
def get_match(match_id: str, db: Session = Depends(get_db)):
    """Get a single match candidate with full record data."""
    match = db.query(MatchCandidate).filter(MatchCandidate.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match candidate not found")

    record_a = db.query(CustomerRecord).filter(CustomerRecord.id == match.record_a_id).first()
    record_b = db.query(CustomerRecord).filter(CustomerRecord.id == match.record_b_id).first()

    return MatchCandidateResponse(
        id=match.id,
        record_a_id=match.record_a_id,
        record_b_id=match.record_b_id,
        overall_score=match.overall_score,
        field_scores=match.field_scores,
        match_method=match.match_method,
        status=match.status.value if isinstance(match.status, MatchStatus) else match.status,
        reviewed_at=match.reviewed_at,
        notes=match.notes,
        created_at=match.created_at,
        record_a=record_a,
        record_b=record_b,
    )


@router.put("/{match_id}/review")
def review_match(
    match_id: str,
    review: MatchReviewRequest,
    db: Session = Depends(get_db),
):
    """Approve or reject a match candidate."""
    match = db.query(MatchCandidate).filter(MatchCandidate.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match candidate not found")

    if review.status not in ("approved", "rejected"):
        raise HTTPException(400, "Status must be 'approved' or 'rejected'")

    match.status = MatchStatus(review.status)
    match.reviewed_at = datetime.utcnow()
    match.notes = review.notes
    db.commit()

    return {"message": f"Match {review.status}", "id": match_id}
