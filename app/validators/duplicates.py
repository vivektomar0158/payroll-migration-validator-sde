"""Duplicate-record detection within a single payroll export."""
import pandas as pd


def find_duplicates(df: pd.DataFrame, key: str = "employee_id") -> pd.DataFrame:
    """Returns rows that appear more than once for the same key, with a dup count."""
    dup_mask = df.duplicated(subset=[key], keep=False)
    dups = df[dup_mask].copy()
    if dups.empty:
        return dups
    counts = dups.groupby(key).size().rename("duplicate_count")
    return dups.join(counts, on=key).sort_values(key)
