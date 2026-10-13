"""Smoke test for clinical Revised Geneva scoring."""
from geneva import calculate_score, BOOLEAN_FACTORS


def test_score():
    patient = {name: False for name in BOOLEAN_FACTORS}
    patient.update(age=68, heart_rate=80, active_malignancy=True)
    assert calculate_score(patient)["score"] == 6
    assert calculate_score(patient)["tier"] == "intermediate"
