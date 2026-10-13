"""Tests for Revised Geneva score, CSV handling, CLI, and security boundaries."""
import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import geneva


@pytest.fixture
def normal():
    return dict(age=40, heart_rate=70, previous_dvt_pe=False,
                surgery_or_fracture_1mo=False, active_malignancy=False,
                unilateral_leg_pain=False, hemoptysis=False,
                deep_vein_tenderness_and_unilateral_edema=False)


def test_no_criteria(normal):
    assert geneva.calculate_score(normal) == {"score": 0, "tier": "low", "detail": {}}


def test_full_score_22(normal):
    normal.update(age=66, heart_rate=95, **{k: True for k in geneva.BOOLEAN_FACTORS})
    res = geneva.calculate_score(normal)
    assert res["score"] == 22
    assert res["tier"] == "high"
    assert sum(res["detail"].values()) == 22


@pytest.mark.parametrize("heart_rate,expected", [(74, 0), (75, 3), (94, 3), (95, 5), (120, 5)])
def test_heart_rate_boundaries(normal, heart_rate, expected):
    normal["heart_rate"] = heart_rate
    assert geneva.calculate_score(normal)["score"] == expected


@pytest.mark.parametrize("age,expected", [(65, 0), (65.1, 1), (66, 1)])
def test_age_boundary(normal, age, expected):
    normal["age"] = age
    assert geneva.calculate_score(normal)["score"] == expected


@pytest.mark.parametrize("score_input,tier", [
    ({"previous_dvt_pe": True}, "low"),
    ({"deep_vein_tenderness_and_unilateral_edema": True}, "intermediate"),
    ({"heart_rate": 95, "previous_dvt_pe": True, "unilateral_leg_pain": True}, "high"),
])
def test_tier_boundaries(normal, score_input, tier):
    normal.update(score_input)
    assert geneva.calculate_score(normal)["tier"] == tier


def test_individual_factor_weights(normal):
    for factor, (_, weight) in geneva.BOOLEAN_FACTORS.items():
        patient = {**normal, factor: "YES"}
        assert geneva.calculate_score(patient)["score"] == weight


@pytest.mark.parametrize("bad", [{}, None, [], {"age": 40}, {"heart_rate": 99}])
def test_missing_criteria_rejected(bad):
    with pytest.raises(ValueError, match="required criteria|object"):
        geneva.calculate_score(bad)


@pytest.mark.parametrize("field,value", [
    ("heart_rate", 0), ("heart_rate", 301), ("heart_rate", "nan"),
    ("heart_rate", "inf"), ("age", -1), ("age", 121),
    ("age", None), ("hemoptysis", ""), ("hemoptysis", "unknown"),
    ("previous_dvt_pe", 2),
])
def test_invalid_inputs_rejected(normal, field, value):
    normal[field] = value
    with pytest.raises(ValueError):
        geneva.calculate_score(normal)


def test_cli_json(normal, capsys):
    assert geneva.main(["single", "--json", json.dumps(normal)]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 0


def test_cli_argument_flags(capsys):
    assert geneva.main(["single", "--age", "66", "--heart-rate", "95",
                        "--hemoptysis", "--previous-dvt-pe"]) == 0
    assert json.loads(capsys.readouterr().out)["score"] == 11


def test_cli_invalid_json(capsys):
    assert geneva.main(["single", "--json", "not json"]) == 1
    assert "Invalid JSON" in capsys.readouterr().err


def test_cli_missing_measurements(capsys):
    assert geneva.main(["single"]) == 1
    assert "age" in capsys.readouterr().err


def test_csv_roundtrip(normal, tmp_path):
    inp, out = tmp_path / "input.csv", tmp_path / "subdir" / "out.csv"
    with inp.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["patient_id", *geneva.REQUIRED_FIELDS])
        writer.writeheader()
        writer.writerow({"patient_id": "=1+1", **normal})
    rows = geneva.process_csv(inp, out)
    assert rows[0]["score"] == 0
    with out.open(newline="") as f:
        actual = next(csv.DictReader(f))
    assert actual["patient_id"] == "'=1+1"
    assert actual["tier"] == "low"


def test_csv_missing_headers(tmp_path):
    inp = tmp_path / "input.csv"
    inp.write_text("age,heart_rate\n65,75\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required CSV columns"):
        geneva.process_csv(inp, tmp_path / "out.csv")


def test_csv_missing_row_value(tmp_path, normal):
    inp = tmp_path / "input.csv"
    with inp.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(geneva.REQUIRED_FIELDS))
        writer.writeheader()
        writer.writerow({**normal, "hemoptysis": ""})
    with pytest.raises(ValueError, match="CSV row 2"):
        geneva.process_csv(inp, tmp_path / "out.csv")


def test_csv_cannot_overwrite_input(tmp_path, normal):
    inp = tmp_path / "input.csv"
    inp.write_text(",".join(geneva.REQUIRED_FIELDS) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="different"):
        geneva.process_csv(inp, inp)


def test_csv_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        geneva.process_csv(tmp_path / "missing.csv", tmp_path / "out.csv")


def test_csv_no_data_rows(tmp_path):
    inp = tmp_path / "empty.csv"
    inp.write_text(",".join(geneva.REQUIRED_FIELDS) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no data"):
        geneva.process_csv(inp, tmp_path / "out.csv")


class TestSecurityAudit:
    """Tests for security features."""

    def test_audit_trail_with_random_key(self):
        """Audit trail should work even without explicit key set."""
        from agents.base import AuditTrail
        # When no key is provided, a random one should be generated
        trail = AuditTrail()
        assert len(trail.secret_key) > 0

    def test_audit_trail_with_explicit_key(self):
        """Audit trail should use provided key."""
        from agents.base import AuditTrail
        trail = AuditTrail(secret_key="test-key-for-testing")
        assert trail.secret_key == b"test-key-for-testing"

    def test_audit_trail_logging(self):
        """Audit trail should log entries correctly."""
        from agents.base import AuditTrail
        trail = AuditTrail(secret_key="test-key")
        entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"action": "test"})
        assert "audit_id" in entry
        assert "current_hash" in entry
        assert entry["actor"] == "test_actor"

    def test_audit_trail_integrity(self):
        """Audit trail integrity should be verifiable."""
        from agents.base import AuditTrail
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor1", "tier1", "EVENT1", {"data": 1})
        trail.log("actor2", "tier2", "EVENT2", {"data": 2})
        assert trail.verify_integrity() is True

    def test_phi_detection_mrn(self):
        """PHI guard should detect MRN patterns."""
        from agents.base import PHIGuard, SecurityException
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_phi_detection_ssn(self):
        """PHI guard should detect SSN patterns."""
        from agents.base import PHIGuard, SecurityException
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phi_clean_text_passes(self):
        """Clean text should pass PHI check."""
        from agents.base import PHIGuard
        # Should not raise
        PHIGuard.assert_no_phi("Specimen KEY-001 optimal parameters")

    def test_phi_redaction(self):
        """PHI redaction should replace sensitive data."""
        from agents.base import PHIGuard
        redacted = PHIGuard.redact_phi("Patient MRN-12345 is positive")
        assert "REDACTED_IDENTIFIER" in redacted
        assert "MRN-12345" not in redacted
