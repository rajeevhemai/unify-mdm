"""Upload and data source management endpoints."""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.config import settings
from app.models.models import DataSource, CustomerRecord
from app.schemas.schemas import (
    DataSourceResponse,
    FilePreviewResponse,
    ColumnMappingRequest,
)
from app.services.file_processor import (
    get_file_preview,
    auto_map_columns,
    import_records,
    STANDARD_FIELDS,
)

router = APIRouter(prefix="/api/sources", tags=["Data Sources"])


@router.post("/upload", response_model=DataSourceResponse)
async def upload_file(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a CSV or Excel file."""
    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(400, "Only CSV and Excel files are supported")

    # Validate file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(400, f"File too large. Max: {settings.MAX_UPLOAD_SIZE_MB}MB")

    # Save file to disk
    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Create data source record
    source = DataSource(
        id=file_id,
        name=name or file.filename,
        file_name=file.filename,
        file_type=ext.lstrip("."),
        status="uploaded",
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/", response_model=list[DataSourceResponse])
def list_sources(db: Session = Depends(get_db)):
    """List all data sources."""
    return db.query(DataSource).order_by(DataSource.uploaded_at.desc()).all()


@router.get("/{source_id}", response_model=DataSourceResponse)
def get_source(source_id: str, db: Session = Depends(get_db)):
    """Get a single data source."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")
    return source


@router.delete("/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    """Delete a data source and all its records."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")

    # Delete file from disk
    file_path = os.path.join(settings.UPLOAD_DIR, f"{source.id}.{source.file_type}")
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(source)
    db.commit()
    return {"message": "Deleted successfully"}


@router.get("/{source_id}/preview", response_model=FilePreviewResponse)
def preview_file(source_id: str, db: Session = Depends(get_db)):
    """Preview the columns and sample rows from an uploaded file."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")

    file_path = os.path.join(settings.UPLOAD_DIR, f"{source.id}.{source.file_type}")
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found on disk")

    preview = get_file_preview(file_path)
    return preview


@router.get("/{source_id}/auto-map")
def get_auto_mapping(source_id: str, db: Session = Depends(get_db)):
    """Get automatic column mapping suggestions."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")

    file_path = os.path.join(settings.UPLOAD_DIR, f"{source.id}.{source.file_type}")
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found on disk")

    preview = get_file_preview(file_path, max_rows=1)
    mapping = auto_map_columns(preview["columns"])
    return {
        "suggested_mapping": mapping,
        "source_columns": preview["columns"],
        "standard_fields": STANDARD_FIELDS,
    }


@router.post("/{source_id}/import")
def import_file_records(
    source_id: str,
    mapping_request: ColumnMappingRequest,
    db: Session = Depends(get_db),
):
    """Import records from a file using the provided column mapping."""
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "Data source not found")

    file_path = os.path.join(settings.UPLOAD_DIR, f"{source.id}.{source.file_type}")
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found on disk")

    # Validate mapping
    for std_field in mapping_request.mapping.values():
        if std_field not in STANDARD_FIELDS:
            raise HTTPException(400, f"Invalid standard field: {std_field}")

    # Import records
    count = import_records(db, source_id, file_path, mapping_request.mapping)

    # Save mapping to source
    source.column_mapping = mapping_request.mapping
    db.commit()

    return {"message": f"Imported {count} records", "record_count": count}


@router.get("/{source_id}/records", response_model=list)
def get_source_records(
    source_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get records from a specific data source."""
    records = (
        db.query(CustomerRecord)
        .filter(CustomerRecord.source_id == source_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records
