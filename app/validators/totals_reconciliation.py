"""Reconciles legacy vs target totals per employee and flags mismatches."""
import pandas as pd

TOLERANCE_CENTS = 0.01


def reconcile_totals(legacy: pd.DataFrame, target: pd.DataFrame, key: str = "employee_id",
                      fields: list[str] = None) -> pd.DataFrame:
    fields = fields or ["gross_pay", "net_pay"]
    merged = legacy.merge(target, on=key, how="outer", suffixes=("_legacy", "_target"), indicator=True)

    mismatches = []
    for _, row in merged.iterrows():
        issues = []
        if row["_merge"] == "left_only":
            issues.append("present_in_legacy_only")
        elif row["_merge"] == "right_only":
            issues.append("present_in_target_only")
        else:
            for f in fields:
                lv, tv = row.get(f"{f}_legacy"), row.get(f"{f}_target")
                if pd.notna(lv) and pd.notna(tv) and abs(float(lv) - float(tv)) > TOLERANCE_CENTS:
                    issues.append(f"{f}_mismatch(legacy={lv}, target={tv}, diff={round(float(tv)-float(lv),2)})")
        if issues:
            mismatches.append({key: row[key], "issues": issues})

    return pd.DataFrame(mismatches)
