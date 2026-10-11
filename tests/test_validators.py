import pandas as pd
from app.validators.duplicates import find_duplicates
from app.validators.missing_fields import find_missing_fields
from app.validators.totals_reconciliation import reconcile_totals


def test_find_duplicates_detects_repeated_key():
    df = pd.DataFrame({"employee_id": ["E1", "E1", "E2"], "name": ["A", "A", "B"]})
    out = find_duplicates(df)
    assert len(out) == 2
    assert set(out["employee_id"]) == {"E1"}


def test_find_duplicates_empty_when_unique():
    df = pd.DataFrame({"employee_id": ["E1", "E2"], "name": ["A", "B"]})
    assert find_duplicates(df).empty


def test_find_missing_fields_flags_blank_bank_account():
    df = pd.DataFrame({
        "employee_id": ["E1", "E2"], "name": ["A", "B"], "department": ["Eng", "Eng"],
        "bank_account": ["ACC1", ""], "gross_pay": [100, 100], "net_pay": [90, 90],
    })
    out = find_missing_fields(df)
    assert len(out) == 1
    assert out.iloc[0]["employee_id"] == "E2"


def test_reconcile_totals_flags_mismatch_and_presence():
    legacy = pd.DataFrame({"employee_id": ["E1", "E2"], "gross_pay": [100, 200], "net_pay": [90, 180]})
    target = pd.DataFrame({"employee_id": ["E1", "E3"], "gross_pay": [100, 50], "net_pay": [95, 45]})
    out = reconcile_totals(legacy, target)
    issues_by_id = {row["employee_id"]: row["issues"] for _, row in out.iterrows()}
    assert any("net_pay_mismatch" in i for i in issues_by_id["E1"])
    assert "present_in_legacy_only" in issues_by_id["E2"]
    assert "present_in_target_only" in issues_by_id["E3"]
