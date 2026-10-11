import io
import time

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

LEGACY = "employee_id,name,department,bank_account,gross_pay,net_pay\nE1,A,Eng,ACC1,1000,900\n"
TARGET = "employee_id,name,department,bank_account,gross_pay,net_pay\nE1,A,Eng,,1000,950\n"


def test_submit_job_returns_202_and_processes_to_done():
    resp = client.post(
        "/jobs",
        files={
            "legacy": ("legacy.csv", io.BytesIO(LEGACY.encode()), "text/csv"),
            "target": ("target.csv", io.BytesIO(TARGET.encode()), "text/csv"),
        },
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    # TestClient runs BackgroundTasks synchronously before returning, so it should already be done.
    status_resp = client.get(f"/jobs/{job_id}")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["status"] == "DONE"
    assert body["result"]["missing_field_count"] == 1


def test_get_unknown_job_returns_404():
    resp = client.get("/jobs/does-not-exist")
    assert resp.status_code == 404


def test_api_key_enforced_when_configured(monkeypatch):
    monkeypatch.setenv("MIGRATION_VALIDATOR_API_KEY", "secret123")
    resp = client.get("/jobs/anything")
    assert resp.status_code == 401

    resp_ok = client.get("/jobs/anything", headers={"X-API-Key": "secret123"})
    assert resp_ok.status_code == 404  # auth passes, job just doesn't exist
