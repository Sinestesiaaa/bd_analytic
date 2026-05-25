from __future__ import annotations

from datetime import time

import pandas as pd

# Ordered rules: first match wins
CLASSIFICATION_RULES: list[tuple[str, str, list[str]]] = [
    ("BOLT", "SEGMENT BOLT", ["BOLT SEGMENT", "BOLT SEKMENT", "BOLT SEKMENT", "BOLT MASTER LINK"]),
    ("BOLT", "MOUNTING BOLT", ["BOLT MONTING ENGINE", "BOLT MOUNTING ENGINE"]),
    ("BOLT", "GENERAL BOLT", ["BOLT"]),
    ("ENGINE", "ENGINE NOISE", ["ENGINE NOISE"]),
    ("ENGINE", "ENGINE SHUTDOWN", ["ENGINE SHUTDOWN", "ENGINE MATI", "MATI MENDADAK", "MATI SENDIRI", "CANT START", "CAN START", "CANTSTART", "CANT STAR"]),
    ("ENGINE", "LOW POWER", ["LOW POWER"]),
    ("ENGINE", "DAMPER ENGINE", ["DAMPER ENGINE", "OIL DAMPER"]),
    ("ENGINE", "GASKET HEAD", ["GASKET HEAD"]),
    ("ENGINE", "GENERAL ENGINE", ["ENGINE", "GUARD ENGINE"]),
    ("COOLING", "RADIATOR LEAK", ["RADIATOR LEAK", "RADIATOR NYEMBUR", "AIR RADIATOR LEAK", "RADIOATOR LEAK"]),
    ("COOLING", "OVERHEAT", ["OVERHEAT", "OVER HEAT"]),
    ("COOLING", "COOLANT LOW", ["COOLANT LOW", "COOLANT UNDER LOW", "COOLANT LEVEL LOW", "COLANT"]),
    ("COOLING", "COOLANT LOW", ["COOLANT KERING"]),
    ("COOLING", "RADIATOR REPAIR", ["GANTI RADIATOR", "RADIATOR"]),
    ("HYDRAULIC", "HOSE LEAK", ["HOSE", "SELANG"]),
    ("HYDRAULIC", "HYDRAULIC LOW/LEAK", ["HYDROLIK", "HYDROLIC", "HYD LOW", "HYD LEAK"]),
    ("UNDERCARRIAGE", "TRACK ISSUE", ["TRACK", "MASTERLING", "MASTER LINK"]),
    ("UNDERCARRIAGE", "ROLLER ISSUE", ["ROLLER", "IDLER", "ADJUSTER", "SEAL ADJUSTER"]),
    ("UNDERCARRIAGE", "SEGMENT ISSUE", ["SEGMEN", "SEGMENT", "UNDERCARRIAGE", "CUTTING", "END BIT"]),
    ("ATTACHMENT", "BLADE ISSUE", ["BLADE", "PIN BLADE", "FRAME BLADE"]),
    ("ATTACHMENT", "ARM ISSUE", ["ARM", "LOCK ARM", "LOCK PIN ARM", "PIN ARM"]),
    ("LUBRICATION", "TRANSMISSION OIL", ["OIL T/M", "OLI T/M", "OIL TM", "OLI TRANSMISI", "TRANSMISI LEAK", "TRANSMISI ERROR", "ERROR TM", "T/M"]),
    ("LUBRICATION", "ENGINE OIL", ["OIL ENGINE", "OLI ENGINE"]),
    ("LUBRICATION", "HYD OIL", ["OIL HYD", "OLI HYD", "OIL HYDROLIK", "OLI HYDROLIK"]),
    ("ELECTRICAL", "LIGHTING", ["LAMPU", "WIPPER"]),
    ("ELECTRICAL", "BATTERY/ACCU", ["ACCU", "BATTERY", "KEPALA ACCU", "KEPALA BATTERY"]),
    ("ELECTRICAL", "ALTERNATOR/BELT", ["V BELT ALTERNATOR", "V-BELT ALTERNATOR"]),
    ("COMMUNICATION", "RADIO/PTT", ["RADIO", "PTT"]),
    ("FUEL SYSTEM", "FUEL ISSUE", ["FUEL", "INJECTOR"]),
    ("CABIN/STRUCTURE", "CABIN BODY", ["KACA", "PINTU", "KANOPI", "KNOPI", "BRAKET", "ENGSEL"]),
    ("OPERATIONAL", "MOTION ISSUE", ["TIDAK BISA MAJU", "TIDAK MAU PINDAH", "BLADE TIDAK MAU NAIK", "BLADE LAMBAT NAIK", "GAS T/M TIDAK ADA", "GAS NYA TIDAK BISA NARIK"]),
    ("POWERTRAIN", "FINAL DRIVE", ["FINAL DRIVE", "RESEAL FINAL DRIVE"]),
    ("POWERTRAIN", "BRAKE", ["BRAKE"]),
    ("POWERTRAIN", "ROTARY", ["ROTARY"]),
    ("CABIN/STRUCTURE", "HANDLE/BODY", ["HANDLE", "ENBIT"]),
    ("ELECTRICAL", "AC SYSTEM", ["AC HOT", "V-BELT AC", "V BELT AC"]),
    ("LUBRICATION", "DAMPER OIL", ["OIL DUMPER", "OLI DAMPER"]),
    ("OPERATIONAL", "SERVICE/GENERAL", ["SERVICE", "PS 1", "FINAL CHECK", "WELDING", "PEMASANGAN"]),
]


def classify_category_subcategory(text: object) -> tuple[str, str]:
    if pd.isna(text):
        return "UNCLASSIFIED", "UNCLASSIFIED"
    value = str(text).upper()
    for category, subcategory, keywords in CLASSIFICATION_RULES:
        if any(keyword in value for keyword in keywords):
            return category, subcategory
    return "GENERAL", "GENERAL ISSUE"


def add_classification_columns(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    classified = data["Description of Breakdown"].apply(classify_category_subcategory)
    data["Category"] = classified.apply(lambda x: x[0])
    data["Subcategory"] = classified.apply(lambda x: x[1])

    duration = pd.to_numeric(data.get("Duration_Real"), errors="coerce")
    data["Severity"] = pd.cut(
        duration,
        bins=[-float("inf"), 2, 6, float("inf")],
        labels=["Minor", "Medium", "Major"],
        right=False,
    ).astype("object")
    data["Severity"] = data["Severity"].fillna("Unknown")
    if "Status_Severity_Source" in data.columns:
        src = data["Status_Severity_Source"].astype("string").str.strip()
        data["Severity"] = data["Severity"].where(src.isna(), src)

    date_ts = pd.to_datetime(data["Date"], errors="coerce")
    data["Month"] = date_ts.dt.to_period("M").astype("string")
    data["Week"] = date_ts.dt.isocalendar().week.astype("Int64")

    def _extract_hour(value: object):
        if pd.isna(value):
            return pd.NA
        if isinstance(value, time):
            return value.hour
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return pd.NA
        return int(parsed.hour)

    data["Hour_Start"] = data["Awal"].apply(_extract_hour).astype("Int64")

    shift_num = (
        data["Shift"].astype("string").str.extract(r"(\d+)")[0]
    )
    data["Shift_Num"] = pd.to_numeric(shift_num, errors="coerce").astype("Int64")
    return data
