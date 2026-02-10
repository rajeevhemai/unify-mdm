from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime


# --- Data Source ---
class DataSourceBase(BaseModel):
    name: str

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceResponse(DataSourceBase):
    id: str
    file_name: str
    file_type: str
    record_count: int
    uploaded_at: datetime
    status: str
    column_mapping: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True


# --- Customer Record ---
class CustomerRecordResponse(BaseModel):
    id: str
    source_id: str
    source_row_number: Optional[int] = None
    company_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    website: Optional[str] = None
    golden_record_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Match Candidate ---
class MatchCandidateResponse(BaseModel):
    id: str
    record_a_id: str
    record_b_id: str
    overall_score: float
    field_scores: Optional[Dict[str, float]] = None
    match_method: Optional[str] = None
    status: str
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    # Include full record data for display
    record_a: Optional[CustomerRecordResponse] = None
    record_b: Optional[CustomerRecordResponse] = None

    class Config:
        from_attributes = True


class MatchReviewRequest(BaseModel):
    status: str  # approved, rejected
    notes: Optional[str] = None


class MergeRequest(BaseModel):
    match_id: str
    surviving_values: Dict[str, Any]  # field -> chosen value


# --- Golden Record ---
class GoldenRecordResponse(BaseModel):
    id: str
    company_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    website: Optional[str] = None
    source_count: int
    created_at: datetime
    updated_at: datetime
    source_records: Optional[List[CustomerRecordResponse]] = None

    class Config:
        from_attributes = True


# --- Column Mapping ---
class ColumnMappingRequest(BaseModel):
    source_id: str
    mapping: Dict[str, str]  # source_column -> standard_field


class ColumnMappingResponse(BaseModel):
    id: str
    name: str
    mapping: Dict[str, str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_sources: int
    total_records: int
    total_matches_pending: int
    total_matches_approved: int
    total_matches_rejected: int
    total_golden_records: int
    duplicate_rate: float  # percentage


# --- File Preview ---
class FilePreviewResponse(BaseModel):
    columns: List[str]
    sample_rows: List[Dict[str, Any]]
    total_rows: int


# --- Matching Config ---
class MatchingConfig(BaseModel):
    threshold: float = 0.75  # Minimum overall score to be a match candidate
    field_weights: Optional[Dict[str, float]] = None  # Override default weights
