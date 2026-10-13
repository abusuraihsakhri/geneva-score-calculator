"""Direct endpoint tests do not require an HTTP test client dependency."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from pydantic import ValidationError
from agents.api import GenevaScoreRequest, api_geneva_score


def _payload(**changes):
    source = {
        "age": 66, "heart_rate": 95, "previous_dvt_pe": False,
        "surgery_or_fracture_1mo": False, "active_malignancy": False,
        "unilateral_leg_pain": False, "hemoptysis": False,
        "deep_vein_tenderness_and_unilateral_edema": False,
    }
    source.update(changes)
    return source


def test_revised_geneva_api():
    assert api_geneva_score(GenevaScoreRequest(**_payload())) == {
        "score": 6, "tier": "intermediate",
        "detail": {"Age >65 years": 1, "Heart rate >=95 bpm": 5}
    }


def test_api_missing_criterion_fails():
    data = _payload()
    del data["hemoptysis"]
    with pytest.raises(ValidationError):
        GenevaScoreRequest(**data)


def test_api_string_bool_rejected():
    with pytest.raises(ValidationError):
        GenevaScoreRequest(**_payload(hemoptysis="false"))


def test_reject_unexpected_api_fields():
    with pytest.raises(ValidationError):
        GenevaScoreRequest(**_payload(patient_name="unexpected"))


def test_legacy_api_requires_configured_token(monkeypatch):
    from fastapi import HTTPException
    from agents.api import require_legacy_token
    monkeypatch.delenv("GENEVA_LEGACY_API_TOKEN", raising=False)
    with pytest.raises(HTTPException) as exc:
        require_legacy_token(None)
    assert exc.value.status_code == 403
    monkeypatch.setenv("GENEVA_LEGACY_API_TOKEN", "secret-for-test")
    with pytest.raises(HTTPException):
        require_legacy_token("wrong")
    assert require_legacy_token("secret-for-test") is None
