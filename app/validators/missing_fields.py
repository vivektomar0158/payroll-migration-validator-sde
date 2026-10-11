"""Required-field completeness checks on the target export."""
import pandas as pd

REQUIRED_FIELDS = ["employee_id", "name", "department", "bank_account", "gross_pay", "net_pay"]


def find_missing_fields(df: pd.DataFrame, required: list[str] = None) -> pd.DataFrame:
    """Returns rows with any blank/null value in a required field, plus which fields are missing."""
    required = required or REQUIRED_FIELDS
    present = [f for f in required if f in df.columns]

    def missing_cols(row):
        return [f for f in present if pd.isna(row[f]) or str(row[f]).strip() == ""]

    df = df.copy()
    df["missing_fields"] = df.apply(missing_cols, axis=1)
    flagged = df[df["missing_fields"].apply(len) > 0]
    return flagged
