"""
File processing service for CSV and Excel uploads.
Handles file parsing, preview, and column mapping.
"""

import os
import uuid
from typing import Dict, List, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import DataSource, CustomerRecord
from app.core.config import settings


STANDARD_FIELDS = [
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

# Common column name variations that map to standard fields
AUTO_MAP_HINTS = {
    "company_name": ["company", "company_name", "companyname", "organization", "org", "business", "firm"],
    "first_name": ["first_name", "firstname", "first", "given_name", "givenname"],
    "last_name": ["last_name", "lastname", "last", "surname", "family_name", "familyname"],
    "email": ["email", "e-mail", "email_address", "emailaddress", "mail"],
    "phone": ["phone", "telephone", "tel", "phone_number", "phonenumber", "mobile", "cell"],
    "address_line1": ["address", "address_line1", "address1", "street", "street_address", "addressline1"],
    "address_line2": ["address_line2", "address2", "addressline2", "suite", "apt", "unit"],
    "city": ["city", "town", "municipality"],
    "state": ["state", "province", "region", "state_province"],
    "postal_code": ["postal_code", "postalcode", "zip", "zipcode", "zip_code", "postcode"],
    "country": ["country", "nation", "country_code"],
    "tax_id": ["tax_id", "taxid", "vat", "vat_number", "ein", "tax_number", "kvk", "coc"],
    "website": ["website", "web", "url", "homepage", "site"],
}


def read_file(file_path: str) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        # Try common encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not read CSV with supported encodings")
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def get_file_preview(file_path: str, max_rows: int = 5) -> Dict[str, Any]:
    """Return column names and sample rows from a file."""
    df = read_file(file_path)
    # Replace NaN with None for JSON serialization
    sample = df.head(max_rows).where(df.notna(), None)
    return {
        "columns": list(df.columns),
        "sample_rows": sample.to_dict(orient="records"),
        "total_rows": len(df),
    }


def auto_map_columns(columns: List[str]) -> Dict[str, str]:
    """
    Automatically suggest column mappings based on column names.
    Returns {source_column: standard_field}
    """
    mapping = {}
    for col in columns:
        col_lower = col.lower().strip().replace(" ", "_").replace("-", "_")
        for std_field, hints in AUTO_MAP_HINTS.items():
            if col_lower in hints:
                mapping[col] = std_field
                break
    return mapping


def import_records(
    db: Session,
    source_id: str,
    file_path: str,
    column_mapping: Dict[str, str],
) -> int:
    """
    Import records from a file using the provided column mapping.
    Returns the number of records imported.
    """
    df = read_file(file_path)
    count = 0

    for idx, row in df.iterrows():
        record_data = {}
        raw_data = {}

        for source_col, std_field in column_mapping.items():
            if source_col in df.columns:
                value = row.get(source_col)
                # Convert to string, handle NaN
                if pd.notna(value):
                    str_value = str(value).strip()
                    if str_value:
                        record_data[std_field] = str_value
                        raw_data[source_col] = str_value

        record = CustomerRecord(
            source_id=source_id,
            source_row_number=idx + 1,
            raw_data=raw_data,
            **record_data,
        )
        db.add(record)
        count += 1

    # Update source record count
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if source:
        source.record_count = count
        source.status = "processed"

    db.commit()
    return count
