"""Persistence layer. Defaults to SQLite for local dev/tests; set DATABASE_URL to a
Postgres DSN in production (see docker-compose.yml) — this is the SDE-layer swap from
the Data Analyst version's in-memory report dict."""
import json
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./jobs.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="QUEUED")
    result_json = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


Base.metadata.create_all(engine)


def create_job() -> str:
    job_id = str(uuid.uuid4())
    with SessionLocal() as session:
        session.add(Job(id=job_id, status="QUEUED"))
        session.commit()
    return job_id


def mark_processing(job_id: str):
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        job.status = "PROCESSING"
        session.commit()


def mark_done(job_id: str, result: dict):
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        job.status = "DONE"
        job.result_json = json.dumps(result)
        job.completed_at = datetime.now(timezone.utc)
        session.commit()


def mark_failed(job_id: str, error: str):
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        job.status = "FAILED"
        job.error = error
        job.completed_at = datetime.now(timezone.utc)
        session.commit()


def get_job(job_id: str) -> dict | None:
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if job is None:
            return None
        return {
            "id": job.id, "status": job.status,
            "result": json.loads(job.result_json) if job.result_json else None,
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
