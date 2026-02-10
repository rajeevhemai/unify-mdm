"""Dashboard statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import DataSource, CustomerRecord, MatchCandidate, GoldenRecord, MatchStatus
from app.schemas.schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get overall dashboard statistics."""
    total_sources = db.query(DataSource).count()
    total_records = db.query(CustomerRecord).count()
    total_matches_pending = db.query(MatchCandidate).filter(
        MatchCandidate.status == MatchStatus.PENDING
    ).count()
    total_matches_approved = db.query(MatchCandidate).filter(
        MatchCandidate.status == MatchStatus.APPROVED
    ).count()
    total_matches_rejected = db.query(MatchCandidate).filter(
        MatchCandidate.status == MatchStatus.REJECTED
    ).count()
    total_golden_records = db.query(GoldenRecord).count()

    # Calculate duplicate rate
    total_matches_all = db.query(MatchCandidate).count()
    duplicate_rate = (total_matches_all / total_records * 100) if total_records > 0 else 0.0

    return DashboardStats(
        total_sources=total_sources,
        total_records=total_records,
        total_matches_pending=total_matches_pending,
        total_matches_approved=total_matches_approved,
        total_matches_rejected=total_matches_rejected,
        total_golden_records=total_golden_records,
        duplicate_rate=round(duplicate_rate, 1),
    )
