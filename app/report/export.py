import io
import pandas as pd


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_xlsx_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            (df if not df.empty else pd.DataFrame(columns=["none_found"])).to_excel(writer, sheet_name=name[:31], index=False)
    return buf.getvalue()
