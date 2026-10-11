import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

LEGACY = "employee_id,name,department,bank_account,gross_pay,net_pay\nE1,A,Eng,ACC1,1000,900\nE1,A,Eng,ACC1,1000,900\nE2,B,Eng,ACC2,2000,1800\n"
TARGET = "employee_id,name,department,bank_account,gross_pay,net_pay\nE1,A,Eng,,1000,950\n"


def test_validate_and_html_report_roundtrip():
    resp = client.post(
        "/validate",
        files={
            "legacy": ("legacy.csv", io.BytesIO(LEGACY.encode()), "text/csv"),
            "target": ("target.csv", io.BytesIO(TARGET.encode()), "text/csv"),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["duplicate_count"] == 2
    assert body["missing_field_count"] == 1
    assert body["mismatch_count"] >= 1

    html_resp = client.get(f"/report/{body['report_id']}.html")
    assert html_resp.status_code == 200
    assert "Payroll Migration Validation Report" in html_resp.text


def test_report_not_found_returns_404():
    resp = client.get("/report/does-not-exist.html")
    assert resp.status_code == 404
