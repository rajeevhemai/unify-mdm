"""
Golden Record Service

Handles merging matched records into canonical golden records.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import (
    CustomerRecord,
    MatchCandidate,
    GoldenRecord,
    MatchStatus,
)


CUSTOMER_FIELDS = [
    "company_name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "address_line1",
    "address_line2",
    "city",
    "state",
    "postal_code",
    "country",
    "tax_id",
    "website",
]


def auto_select_best_values(
    record_a: CustomerRecord,
    record_b: CustomerRecord,
) -> Dict[str, Any]:
    """
    Automatically select the best value for each field.
    Strategy: prefer non-empty, longer, more complete values.
    """
    best = {}
    for field in CUSTOMER_FIELDS:
        val_a = getattr(record_a, field, None) or ""
        val_b = getattr(record_b, field, None) or ""

        if val_a and not val_b:
            best[field] = val_a
        elif val_b and not val_a:
            best[field] = val_b
        elif val_a and val_b:
            # Prefer the longer (more complete) value
            best[field] = val_a if len(val_a) >= len(val_b) else val_b
        else:
            best[field] = None

    return best


def merge_records(
    db: Session,
    match_id: str,
    surviving_values: Optional[Dict[str, Any]] = None,
) -> GoldenRecord:
    """
    Merge two matched records into a golden record.

    If surviving_values is provided, use those values.
    Otherwise, auto-select the best values from each record.
    """
    match = db.query(MatchCandidate).filter(MatchCandidate.id == match_id).first()
    if not match:
        raise ValueError(f"Match candidate {match_id} not found")

    record_a = db.query(CustomerRecord).filter(CustomerRecord.id == match.record_a_id).first()
    record_b = db.query(CustomerRecord).filter(CustomerRecord.id == match.record_b_id).first()

    if not record_a or not record_b:
        raise ValueError("One or both matched records not found")

    # Determine field values for the golden record
    if surviving_values:
        values = surviving_values
    else:
        values = auto_select_best_values(record_a, record_b)

    # Check if either record already has a golden record
    existing_golden = None
    if record_a.golden_record_id:
        existing_golden = db.query(GoldenRecord).filter(
            GoldenRecord.id == record_a.golden_record_id
        ).first()
    elif record_b.golden_record_id:
        existing_golden = db.query(GoldenRecord).filter(
            GoldenRecord.id == record_b.golden_record_id
        ).first()

    if existing_golden:
        # Update existing golden record with new merged values
        for field in CUSTOMER_FIELDS:
            if field in values and values[field]:
                setattr(existing_golden, field, values[field])
        existing_golden.source_count += 1
        existing_golden.updated_at = datetime.utcnow()
        golden = existing_golden
    else:
        # Create new golden record
        golden_data = {f: values.get(f) for f in CUSTOMER_FIELDS}
        golden = GoldenRecord(source_count=2, **golden_data)
        db.add(golden)
        db.flush()  # Get the ID

    # Link source records to golden record
    record_a.golden_record_id = golden.id
    record_b.golden_record_id = golden.id

    # Update match status
    match.status = MatchStatus.MERGED
    match.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(golden)
    return golden


def create_golden_from_single(db: Session, record_id: str) -> GoldenRecord:
    """Create a golden record from a single unmatched record."""
    record = db.query(CustomerRecord).filter(CustomerRecord.id == record_id).first()
    if not record:
        raise ValueError(f"Record {record_id} not found")

    values = {f: getattr(record, f) for f in CUSTOMER_FIELDS}
    golden = GoldenRecord(source_count=1, **values)
    db.add(golden)
    db.flush()

    record.golden_record_id = golden.id
    db.commit()
    db.refresh(golden)
    return golden


def promote_unmatched_to_golden(db: Session) -> int:
    """
    Find all records without a golden record that have no pending matches,
    and promote them to individual golden records.
    Returns count of new golden records created.
    """
    # Records without golden records
    unmatched = db.query(CustomerRecord).filter(
        CustomerRecord.golden_record_id.is_(None)
    ).all()

    count = 0
    for record in unmatched:
        # Check if this record has any pending matches
        pending = db.query(MatchCandidate).filter(
            ((MatchCandidate.record_a_id == record.id) | (MatchCandidate.record_b_id == record.id)),
            MatchCandidate.status == MatchStatus.PENDING,
        ).first()

        if not pending:
            create_golden_from_single(db, record.id)
            count += 1

    return count
