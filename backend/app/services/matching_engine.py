"""
Matching Engine for Unify V1

Implements rule-based fuzzy matching using:
- Levenshtein distance (edit distance)
- Jaro-Winkler similarity (good for names)
- Phonetic matching (Soundex, Metaphone)
- Exact matching for structured fields (email, tax_id)
"""

import re
from typing import Dict, List, Optional, Tuple
from itertools import combinations
import jellyfish
from thefuzz import fuzz
from sqlalchemy.orm import Session

from app.models.models import CustomerRecord, MatchCandidate, MatchStatus


# Default weights for each field in overall score calculation
DEFAULT_FIELD_WEIGHTS = {
    "company_name": 0.25,
    "email": 0.20,
    "phone": 0.10,
    "first_name": 0.10,
    "last_name": 0.10,
    "address_line1": 0.05,
    "city": 0.05,
    "postal_code": 0.05,
    "tax_id": 0.05,
    "website": 0.05,
}


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for comparison: lowercase, strip, remove extra spaces."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def normalize_phone(phone: Optional[str]) -> str:
    """Normalize phone number: keep only digits."""
    if not phone:
        return ""
    return re.sub(r'[^\d]', '', phone)


def normalize_email(email: Optional[str]) -> str:
    """Normalize email: lowercase, strip."""
    if not email:
        return ""
    return email.lower().strip()


def compare_exact(a: str, b: str) -> float:
    """Exact match comparison: 1.0 if equal, 0.0 otherwise."""
    if not a or not b:
        return 0.0
    return 1.0 if a == b else 0.0


def compare_levenshtein(a: str, b: str) -> float:
    """Levenshtein similarity (normalized 0-1)."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 1.0
    distance = jellyfish.levenshtein_distance(a, b)
    return 1.0 - (distance / max_len)


def compare_jaro_winkler(a: str, b: str) -> float:
    """Jaro-Winkler similarity (optimized for names)."""
    if not a or not b:
        return 0.0
    return jellyfish.jaro_winkler_similarity(a, b)


def compare_phonetic(a: str, b: str) -> float:
    """Phonetic similarity using Metaphone."""
    if not a or not b:
        return 0.0
    meta_a = jellyfish.metaphone(a)
    meta_b = jellyfish.metaphone(b)
    if meta_a == meta_b:
        return 1.0
    # Partial phonetic match
    return compare_levenshtein(meta_a, meta_b)


def compare_fuzzy_token(a: str, b: str) -> float:
    """Token-based fuzzy matching (handles word reordering)."""
    if not a or not b:
        return 0.0
    return fuzz.token_sort_ratio(a, b) / 100.0


def compare_field(field_name: str, value_a: Optional[str], value_b: Optional[str]) -> float:
    """
    Compare two field values using the best algorithm for that field type.
    Returns a similarity score between 0.0 and 1.0.
    """
    if not value_a and not value_b:
        return 0.0  # Both empty = no signal
    if not value_a or not value_b:
        return 0.0  # One empty = no match

    # Exact match fields
    if field_name in ("email",):
        a = normalize_email(value_a)
        b = normalize_email(value_b)
        return compare_exact(a, b)

    if field_name in ("tax_id",):
        a = normalize_text(value_a)
        b = normalize_text(value_b)
        return compare_exact(a, b)

    # Phone: normalize then compare
    if field_name in ("phone",):
        a = normalize_phone(value_a)
        b = normalize_phone(value_b)
        if not a or not b:
            return 0.0
        # Check if one is a suffix of the other (handles country codes)
        if a.endswith(b) or b.endswith(a):
            return 0.95
        return compare_levenshtein(a, b)

    # Name fields: use Jaro-Winkler + phonetic
    if field_name in ("first_name", "last_name"):
        a = normalize_text(value_a)
        b = normalize_text(value_b)
        jw = compare_jaro_winkler(a, b)
        phonetic = compare_phonetic(a, b)
        return max(jw, phonetic)

    # Company name: use token sort (handles word reordering) + Jaro-Winkler
    if field_name in ("company_name",):
        a = normalize_text(value_a)
        b = normalize_text(value_b)
        jw = compare_jaro_winkler(a, b)
        token = compare_fuzzy_token(a, b)
        lev = compare_levenshtein(a, b)
        return max(jw, token, lev)

    # Address fields: Levenshtein + token
    if field_name in ("address_line1", "address_line2"):
        a = normalize_text(value_a)
        b = normalize_text(value_b)
        token = compare_fuzzy_token(a, b)
        lev = compare_levenshtein(a, b)
        return max(token, lev)

    # Website: normalize and compare
    if field_name in ("website",):
        a = normalize_text(value_a).replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
        b = normalize_text(value_b).replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
        return compare_exact(a, b) if a and b else 0.0

    # Default: Jaro-Winkler on normalized text
    a = normalize_text(value_a)
    b = normalize_text(value_b)
    return compare_jaro_winkler(a, b)


def compare_records(
    record_a: CustomerRecord,
    record_b: CustomerRecord,
    field_weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, Dict[str, float]]:
    """
    Compare two customer records across all fields.
    Returns (overall_score, field_scores_dict).
    """
    weights = field_weights or DEFAULT_FIELD_WEIGHTS
    field_scores = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for field_name, weight in weights.items():
        value_a = getattr(record_a, field_name, None)
        value_b = getattr(record_b, field_name, None)

        # Skip fields where both records are empty
        if not value_a and not value_b:
            continue

        score = compare_field(field_name, value_a, value_b)
        field_scores[field_name] = round(score, 4)
        weighted_sum += score * weight
        total_weight += weight

    # Calculate overall score (normalized by active fields)
    overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    return round(overall_score, 4), field_scores


def find_matches(
    db: Session,
    source_id: Optional[str] = None,
    threshold: float = 0.75,
    field_weights: Optional[Dict[str, float]] = None,
) -> List[MatchCandidate]:
    """
    Find duplicate match candidates among all records (or within a source).
    Uses pairwise comparison with early-exit optimization.

    Returns list of created MatchCandidate objects.
    """
    # Get records to compare
    query = db.query(CustomerRecord)
    if source_id:
        # Compare new source records against all existing records
        new_records = query.filter(CustomerRecord.source_id == source_id).all()
        existing_records = query.filter(CustomerRecord.source_id != source_id).all()
        pairs = [(a, b) for a in new_records for b in existing_records]
    else:
        # Compare all records against each other
        all_records = query.all()
        pairs = list(combinations(all_records, 2))

    matches = []
    existing_pairs = set()

    # Check for existing match candidates to avoid duplicates
    existing = db.query(MatchCandidate.record_a_id, MatchCandidate.record_b_id).all()
    for a_id, b_id in existing:
        existing_pairs.add((a_id, b_id))
        existing_pairs.add((b_id, a_id))

    for record_a, record_b in pairs:
        # Skip if already evaluated
        if (record_a.id, record_b.id) in existing_pairs:
            continue

        overall_score, field_scores = compare_records(record_a, record_b, field_weights)

        if overall_score >= threshold:
            match = MatchCandidate(
                record_a_id=record_a.id,
                record_b_id=record_b.id,
                overall_score=overall_score,
                field_scores=field_scores,
                match_method="rule_based_v1",
                status=MatchStatus.PENDING,
            )
            db.add(match)
            matches.append(match)
            existing_pairs.add((record_a.id, record_b.id))
            existing_pairs.add((record_b.id, record_a.id))

    db.commit()
    return matches
