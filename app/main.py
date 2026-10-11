import io
import logging
import uuid

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, StreamingResponse

from app.auth import require_api_key
from app.logging_config import configure_logging
from app.validators.duplicates import find_duplicates
from app.validators.missing_fields import find_missing_fields
from app.validators.totals_reconciliation import reconcile_totals
from app.report.html_report import render_html
from app.report.export import to_csv_bytes, to_xlsx_bytes
from app.models import ValidationSummary
from app import db

configure_logging()
logger = logging.getLogger("migration_validator")

app = FastAPI(title="Payroll Migration Validator — backend service")

_REPORTS: dict[str, dict] = {}  # in-memory cache of DataFrames for the sync /validate path


def _read_csv(upload: UploadFile) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(upload.file.read()))


def _json_safe_records(df: pd.DataFrame) -> list[dict]:
    """Replaces NaN (which json can't encode) with None before serialization."""
    if df.empty:
        return []
    return df.astype(object).where(pd.notnull(df), None).to_dict("records")


def _run_validation(legacy_df: pd.DataFrame, target_df: pd.DataFrame) -> dict:
    duplicates = find_duplicates(legacy_df)
    missing = find_missing_fields(target_df)
    mismatches = reconcile_totals(legacy_df, target_df)
    if not missing.empty:
        missing = missing.assign(missing_fields=lambda d: d["missing_fields"].apply(lambda x: ", ".join(x)))
    return {
        "duplicate_count": len(duplicates), "missing_field_count": len(missing),
        "mismatch_count": len(mismatches), "legacy_rows": len(legacy_df), "target_rows": len(target_df),
        "duplicates": _json_safe_records(duplicates),
        "missing": _json_safe_records(missing),
        "mismatches": _json_safe_records(mismatches),
    }


@app.post("/validate", response_model=ValidationSummary, dependencies=[Depends(require_api_key)])
async def validate(legacy: UploadFile = File(...), target: UploadFile = File(...)):
    """Synchronous path, kept for parity with the Data Analyst version."""
    legacy_df = _read_csv(legacy)
    target_df = _read_csv(target)
    duplicates = find_duplicates(legacy_df)
    missing = find_missing_fields(target_df)
    mismatches = reconcile_totals(legacy_df, target_df)

    report_id = str(uuid.uuid4())
    _REPORTS[report_id] = {"duplicates": duplicates, "missing": missing, "mismatches": mismatches,
                            "legacy_rows": len(legacy_df), "target_rows": len(target_df)}
    logger.info(f"validation completed report_id={report_id} duplicates={len(duplicates)} "
                f"missing={len(missing)} mismatches={len(mismatches)}")
    return ValidationSummary(report_id=report_id, duplicate_count=len(duplicates),
                              missing_field_count=len(missing), mismatch_count=len(mismatches),
                              legacy_rows=len(legacy_df), target_rows=len(target_df))


def _process_job(job_id: str, legacy_bytes: bytes, target_bytes: bytes):
    db.mark_processing(job_id)
    try:
        legacy_df = pd.read_csv(io.BytesIO(legacy_bytes))
        target_df = pd.read_csv(io.BytesIO(target_bytes))
        result = _run_validation(legacy_df, target_df)
        db.mark_done(job_id, result)
        logger.info(f"job completed job_id={job_id}")
    except Exception as e:
        db.mark_failed(job_id, str(e))
        logger.error(f"job failed job_id={job_id} error={e}")


@app.post("/jobs", status_code=202, dependencies=[Depends(require_api_key)])
async def submit_job(background_tasks: BackgroundTasks, legacy: UploadFile = File(...), target: UploadFile = File(...)):
    """Async path: accept the files, return 202 + job id immediately, process in the background."""
    legacy_bytes = legacy.file.read()
    target_bytes = target.file.read()
    job_id = db.create_job()
    background_tasks.add_task(_process_job, job_id, legacy_bytes, target_bytes)
    logger.info(f"job submitted job_id={job_id}")
    return {"job_id": job_id, "status": "QUEUED"}


@app.get("/jobs/{job_id}", dependencies=[Depends(require_api_key)])
async def get_job(job_id: str):
    job = db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _get_report(report_id: str) -> dict:
    report = _REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/report/{report_id}.html", response_class=HTMLResponse, dependencies=[Depends(require_api_key)])
async def report_html(report_id: str):
    r = _get_report(report_id)
    html = render_html(
        r["duplicates"].to_dict("records"),
        r["missing"].assign(missing_fields=lambda d: d["missing_fields"].apply(lambda x: ", ".join(x))).to_dict("records") if not r["missing"].empty else [],
        r["mismatches"].to_dict("records"),
    )
    return HTMLResponse(html)


@app.get("/report/{report_id}.csv", dependencies=[Depends(require_api_key)])
async def report_csv(report_id: str):
    r = _get_report(report_id)
    combined = pd.concat([
        r["duplicates"].assign(issue_type="duplicate"),
        r["missing"].assign(issue_type="missing_field"),
        r["mismatches"].assign(issue_type="total_mismatch"),
    ], ignore_index=True)
    data = to_csv_bytes(combined)
    return StreamingResponse(io.BytesIO(data), media_type="text/csv",
                              headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"})


@app.get("/report/{report_id}.xlsx", dependencies=[Depends(require_api_key)])
async def report_xlsx(report_id: str):
    r = _get_report(report_id)
    data = to_xlsx_bytes({"duplicates": r["duplicates"], "missing_fields": r["missing"], "mismatches": r["mismatches"]})
    return StreamingResponse(io.BytesIO(data), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              headers={"Content-Disposition": f"attachment; filename=report_{report_id}.xlsx"})


@app.get("/health")
async def health():
    return {"status": "ok"}
