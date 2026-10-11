from pydantic import BaseModel


class ValidationSummary(BaseModel):
    report_id: str
    duplicate_count: int
    missing_field_count: int
    mismatch_count: int
    legacy_rows: int
    target_rows: int
