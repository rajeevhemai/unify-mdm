import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class DataSource(Base):
    """Represents an uploaded file / data source."""
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # csv, xlsx
    record_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processed")  # uploading, processing, processed, error
    column_mapping = Column(JSON, nullable=True)  # maps source columns to standard fields

    records = relationship("CustomerRecord", back_populates="source", cascade="all, delete-orphan")


class CustomerRecord(Base):
    """A single customer record from a data source."""
    __tablename__ = "customer_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    source_row_number = Column(Integer, nullable=True)

    # Standard customer fields
    company_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Metadata
    raw_data = Column(JSON, nullable=True)  # Original row data
    golden_record_id = Column(String, ForeignKey("golden_records.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("DataSource", back_populates="records")
    golden_record = relationship("GoldenRecord", back_populates="source_records")


class MatchCandidate(Base):
    """A potential duplicate match between two records."""
    __tablename__ = "match_candidates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    record_a_id = Column(String, ForeignKey("customer_records.id"), nullable=False)
    record_b_id = Column(String, ForeignKey("customer_records.id"), nullable=False)

    # Match scores
    overall_score = Column(Float, nullable=False)
    field_scores = Column(JSON, nullable=True)  # {"company_name": 0.92, "email": 1.0, ...}
    match_method = Column(String, nullable=True)  # algorithm used

    # Status
    status = Column(SAEnum(MatchStatus), default=MatchStatus.PENDING)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    record_a = relationship("CustomerRecord", foreign_keys=[record_a_id])
    record_b = relationship("CustomerRecord", foreign_keys=[record_b_id])


class GoldenRecord(Base):
    """The merged, canonical 'single source of truth' record."""
    __tablename__ = "golden_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Best-known customer fields
    company_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Metadata
    source_count = Column(Integer, default=1)  # How many source records merged
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_records = relationship("CustomerRecord", back_populates="golden_record")


class ColumnMapping(Base):
    """Saved column mapping templates for reuse."""
    __tablename__ = "column_mappings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    mapping = Column(JSON, nullable=False)  # {"source_col": "standard_field", ...}
    created_at = Column(DateTime, default=datetime.utcnow)
