import io
from datetime import datetime
from typing import Optional
import pandas as pd
from sms_engine.risk_calculator import calculate_risk_index

SHEET_NAME = "Master logsheet 2026 working"
HAZARD_COL = 8
DESC_COL = 5
SOURCE_COL = 4
DATE_COL = 2
STATUS_COL = 10
DEPT_COL = 11
REMARKS_COL = 12

HEADER_ROW = 3
DATA_START_ROW = 4

HAZARD_TRUE_VALUES = {"true", "yes", "1", "✔", "✓", "☑", "x", "checked", 1, 1.0, True}


def is_hazard_row(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val == 1 or val == 1.0
    s = str(val).strip().lower()
    return s in HAZARD_TRUE_VALUES


def parse_date(val) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, str):
        val = val.strip()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return val
    return str(val)


def clean_str(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def extract_hazards_from_excel(file_bytes: bytes) -> list[dict]:
    df = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=SHEET_NAME,
        header=None,
        skiprows=DATA_START_ROW - 1,
    )

    hazards = []

    for _, row in df.iterrows():
        hazard_val = row.iloc[HAZARD_COL] if len(row) > HAZARD_COL else None
        if not is_hazard_row(hazard_val):
            continue

        desc = clean_str(row.iloc[DESC_COL] if len(row) > DESC_COL else "")
        risk = calculate_risk_index(desc)

        hazard = {
            "source_type": clean_str(row.iloc[SOURCE_COL] if len(row) > SOURCE_COL else ""),
            "description": desc,
            "reported_date": parse_date(row.iloc[DATE_COL] if len(row) > DATE_COL else None),
            "status": clean_str(row.iloc[STATUS_COL] if len(row) > STATUS_COL else ""),
            "department": clean_str(row.iloc[DEPT_COL] if len(row) > DEPT_COL else ""),
            "remarks": clean_str(row.iloc[REMARKS_COL] if len(row) > REMARKS_COL else ""),
            "risk_assessment": risk,
        }
        hazards.append(hazard)

    return hazards


def get_risk_distribution(hazards: list[dict]) -> dict:
    dist = {"intolerable": 0, "tolerable": 0, "acceptable": 0}
    severity_dist = {}
    for h in hazards:
        zone = h["risk_assessment"]["risk_zone"]
        dist[zone] = dist.get(zone, 0) + 1
        sev = h["risk_assessment"]["severity"]
        severity_dist[sev] = severity_dist.get(sev, 0) + 1
    return {
        "risk_zone_distribution": dist,
        "severity_distribution": severity_dist,
        "total": len(hazards),
    }
