"""Health data generators for patient demographics, lab results, and vitals."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from faker import Faker

from datagen.generators.base import register_generator
from datagen.models import ColumnDef

fake = Faker()

# ---------------------------------------------------------------------------
# Test definitions: (name, unit, ref_low, ref_high, result_min, result_max)
# result_min/max define the full realistic range (including out-of-range)
# ---------------------------------------------------------------------------
LAB_TESTS = [
    ("Glucose", "mg/dL", 70, 99, 55, 140),
    ("HbA1c", "%", 4.0, 5.6, 3.5, 9.0),
    ("Total Cholesterol", "mg/dL", 125, 200, 100, 280),
    ("LDL", "mg/dL", 0, 100, 10, 180),
    ("HDL", "mg/dL", 40, 60, 25, 85),
    ("Triglycerides", "mg/dL", 0, 150, 40, 250),
    ("TSH", "mIU/L", 0.4, 4.0, 0.1, 8.0),
    ("Creatinine", "mg/dL", 0.6, 1.2, 0.4, 2.0),
    ("eGFR", "mL/min", 90, 120, 50, 130),
    ("ALT", "U/L", 7, 56, 5, 90),
    ("AST", "U/L", 10, 40, 5, 70),
    ("WBC", "K/uL", 4.5, 11.0, 3.0, 15.0),
    ("Hemoglobin", "g/dL", 12.0, 17.5, 9.0, 19.0),
    ("Platelet Count", "K/uL", 150, 400, 100, 500),
]

# ---------------------------------------------------------------------------
# Vital definitions: (reading_type, unit, typical_min, typical_max, precision)
# ---------------------------------------------------------------------------
VITAL_TYPES = [
    ("Systolic BP", "mmHg", 105, 155, 0),
    ("Diastolic BP", "mmHg", 60, 95, 0),
    ("Heart Rate", "bpm", 55, 100, 0),
    ("Weight", "lbs", 120, 260, 1),
    ("BMI", "kg/m2", 18.0, 35.0, 1),
    ("Temperature", "F", 97.0, 99.8, 1),
    ("SpO2", "%", 94, 100, 0),
]

# Diverse patient pool
PATIENTS = [
    ("Alex", "Brinkerhoff", "1985-03-15", "Male"),
    ("Maria", "Santos", "1972-08-22", "Female"),
    ("James", "Chen", "1990-11-03", "Male"),
    ("Sarah", "Williams", "1968-05-19", "Female"),
    ("DeShawn", "Jackson", "1995-07-10", "Male"),
    ("Priya", "Patel", "1983-12-01", "Female"),
    ("Tomoko", "Nakamura", "1977-04-28", "Female"),
    ("Carlos", "Rivera", "1988-09-14", "Male"),
    ("Fatima", "Al-Hassan", "1992-01-30", "Female"),
    ("Liam", "O'Brien", "1965-06-05", "Male"),
    ("Anika", "Johansson", "1979-10-18", "Female"),
    ("Marcus", "Thompson", "1998-02-22", "Male"),
    ("Mei", "Lin", "1971-08-07", "Female"),
    ("David", "Kowalski", "1986-11-25", "Male"),
    ("Amara", "Okafor", "1993-03-12", "Female"),
]


def _build_lab_plan(num_patients: int, num_dates: int) -> list[dict[str, Any]]:
    """Build a full lab results panel: patient x date x test."""
    rows: list[dict[str, Any]] = []

    # Generate collection dates (roughly every 2-3 months over ~18 months)
    today = date.today()
    base_start = today - timedelta(days=540)  # ~18 months ago

    for p_idx in range(num_patients):
        patient_id = f"PAT-{p_idx + 1:03d}"

        # Each patient gets slightly different collection dates
        offset = random.randint(0, 14)
        dates = []
        for d in range(num_dates):
            collection_date = base_start + timedelta(days=offset + d * 75 + random.randint(-10, 10))
            if collection_date > today:
                collection_date = today - timedelta(days=random.randint(1, 14))
            dates.append(collection_date)
        dates.sort()

        # Give each patient a "profile" - tendency toward certain conditions
        # ~70% healthy, ~20% mildly abnormal, ~10% has a condition
        profile = random.choices(
            ["healthy", "mild", "condition"], weights=[0.7, 0.2, 0.1], k=1
        )[0]

        for col_date in dates:
            for test_name, unit, ref_low, ref_high, res_min, res_max in LAB_TESTS:
                # Generate result based on patient profile
                if profile == "healthy":
                    # Mostly normal, ~10% slightly out of range
                    if random.random() < 0.90:
                        result = random.uniform(ref_low, ref_high)
                    else:
                        result = random.uniform(res_min, res_max)
                elif profile == "mild":
                    # ~70% normal, ~30% out of range
                    if random.random() < 0.70:
                        result = random.uniform(ref_low, ref_high)
                    else:
                        result = random.uniform(res_min, res_max)
                else:
                    # ~50% normal, ~50% out of range
                    if random.random() < 0.50:
                        result = random.uniform(ref_low, ref_high)
                    else:
                        result = random.uniform(res_min, res_max)

                # Round appropriately
                if unit in ("%", "mIU/L", "mg/dL", "g/dL", "K/uL"):
                    result = round(result, 1)
                else:
                    result = round(result, 0)

                # Determine status
                if result < ref_low:
                    # Critical if very far out
                    if result < ref_low * 0.75:
                        status = "Critical"
                    else:
                        status = "Low"
                elif result > ref_high:
                    if result > ref_high * 1.3:
                        status = "Critical"
                    else:
                        status = "High"
                else:
                    status = "Normal"

                rows.append({
                    "PatientID": patient_id,
                    "TestName": test_name,
                    "Result": result,
                    "Unit": unit,
                    "ReferenceRangeLow": ref_low,
                    "ReferenceRangeHigh": ref_high,
                    "CollectionDate": col_date,
                    "Status": status,
                })

    return rows


def _build_vital_plan(num_patients: int, num_dates: int) -> list[dict[str, Any]]:
    """Build a full vitals panel: patient x date x reading type."""
    rows: list[dict[str, Any]] = []
    today = date.today()
    base_start = today - timedelta(days=365)  # 1 year of vitals

    for p_idx in range(num_patients):
        patient_id = f"PAT-{p_idx + 1:03d}"

        # Generate reading dates (~weekly)
        offset = random.randint(0, 6)
        dates = []
        for d in range(num_dates):
            rec_date = base_start + timedelta(days=offset + d * 7 + random.randint(-2, 2))
            if rec_date > today:
                rec_date = today - timedelta(days=random.randint(0, 3))
            dates.append(rec_date)
        dates.sort()

        # Patient baseline characteristics (stable with drift)
        baselines = {
            "Systolic BP": random.uniform(115, 145),
            "Diastolic BP": random.uniform(65, 90),
            "Heart Rate": random.uniform(60, 90),
            "Weight": random.uniform(130, 240),
            "BMI": random.uniform(19.0, 33.0),
            "Temperature": random.uniform(97.2, 99.0),
            "SpO2": random.uniform(95, 100),
        }

        for rec_date in dates:
            for reading_type, unit, typ_min, typ_max, precision in VITAL_TYPES:
                baseline = baselines[reading_type]
                # Add some noise around baseline
                noise_pct = 0.05  # 5% variation
                value = baseline + random.uniform(
                    -baseline * noise_pct, baseline * noise_pct
                )
                # Clamp to realistic range
                value = max(typ_min, min(typ_max, value))

                if precision == 0:
                    value = round(value)
                else:
                    value = round(value, precision)

                rows.append({
                    "PatientID": patient_id,
                    "ReadingType": reading_type,
                    "Value": value,
                    "Unit": unit,
                    "RecordedDate": rec_date,
                })

    return rows


@register_generator("health_lab_init")
def gen_health_lab_init(
    col: ColumnDef, count: int, context: dict | None = None, **kwargs
) -> list:
    """Generate PatientID for lab results AND store the full panel plan.

    The YAML row_count is ignored; actual count comes from the panel structure.
    The col.choices dict should specify:
      num_patients: int (default 15)
      num_dates: int (default 7)
    """
    params = col.choices or {}
    num_patients = params.get("num_patients", 15) if isinstance(params, dict) else 15
    num_dates = params.get("num_dates", 7) if isinstance(params, dict) else 7

    plan = _build_lab_plan(num_patients, num_dates)

    # Store plan in context for subsequent columns
    if context is not None:
        context["_lab_plan"] = plan

    return [row["PatientID"] for row in plan]


@register_generator("health_lab_field")
def gen_health_lab_field(
    col: ColumnDef, count: int, context: dict | None = None, **kwargs
) -> list:
    """Extract a field from the pre-built lab plan stored in context."""
    if not context or "_lab_plan" not in context:
        raise ValueError(
            f"Column '{col.name}': health_lab_field requires health_lab_init "
            f"to run first (must be defined after PatientID column)"
        )
    plan = context["_lab_plan"]
    field = col.field
    if not field:
        raise ValueError(f"Column '{col.name}': health_lab_field requires 'field'")
    return [row[field] for row in plan]


@register_generator("health_vital_init")
def gen_health_vital_init(
    col: ColumnDef, count: int, context: dict | None = None, **kwargs
) -> list:
    """Generate PatientID for vitals AND store the full panel plan."""
    params = col.choices or {}
    num_patients = params.get("num_patients", 15) if isinstance(params, dict) else 15
    num_dates = params.get("num_dates", 50) if isinstance(params, dict) else 50

    plan = _build_vital_plan(num_patients, num_dates)

    if context is not None:
        context["_vital_plan"] = plan

    return [row["PatientID"] for row in plan]


@register_generator("health_vital_field")
def gen_health_vital_field(
    col: ColumnDef, count: int, context: dict | None = None, **kwargs
) -> list:
    """Extract a field from the pre-built vital plan stored in context."""
    if not context or "_vital_plan" not in context:
        raise ValueError(
            f"Column '{col.name}': health_vital_field requires health_vital_init "
            f"to run first"
        )
    plan = context["_vital_plan"]
    field = col.field
    if not field:
        raise ValueError(f"Column '{col.name}': health_vital_field requires 'field'")
    return [row[field] for row in plan]


@register_generator("health_demographics")
def gen_health_demographics(
    col: ColumnDef, count: int, context: dict | None = None, **kwargs
) -> list:
    """Generate a demographics field for the fixed patient pool.

    field should be one of: PatientID, FirstName, LastName, DOB, Gender, MRN
    """
    field = col.field
    if not field:
        raise ValueError(f"Column '{col.name}': health_demographics requires 'field'")

    num_patients = len(PATIENTS)
    results = []

    for i in range(num_patients):
        first, last, dob, gender = PATIENTS[i]
        if field == "PatientID":
            results.append(f"PAT-{i + 1:03d}")
        elif field == "FirstName":
            results.append(first)
        elif field == "LastName":
            results.append(last)
        elif field == "DOB":
            results.append(dob)
        elif field == "Gender":
            results.append(gender)
        elif field == "MRN":
            results.append(str(4821093 + i))
        else:
            raise ValueError(f"Unknown demographics field: {field}")

    return results
