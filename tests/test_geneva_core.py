"""
Automated Pytest for geneva-score-calculator Core Module.
Tests for calculate_score, process_csv, and error handling.
"""
import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import geneva


class TestCalculateScore:
    """Tests for the core calculate_score function."""

    def test_empty_input(self):
        """Empty input should return score 0 and low tier."""
        result = geneva.calculate_score({})
        assert result["score"] == 0
        assert result["tier"] == "low"
        assert result["detail"] == {}

    def test_score_with_factors(self):
        """Score with positive factors should sum correctly."""
        present = {"Hypotension": 1, "Tachycardia": 1}
        result = geneva.calculate_score(present)
        assert result["score"] == 2
        assert "Hypotension" in result["detail"]
        assert "Tachycardia" in result["detail"]

    def test_score_with_boolean_values(self):
        """Boolean True values should be accepted."""
        present = {"Fever": True, "Tachypnea": False}
        result = geneva.calculate_score(present)
        assert result["score"] == 1
        assert "Fever" in result["detail"]
        assert "Tachypnea" not in result["detail"]

    def test_score_with_string_values(self):
        """String 'yes'/'no' values should be accepted."""
        present = {"Altered mental": "yes", "Fever": "no"}
        result = geneva.calculate_score(present)
        assert result["score"] == 1
        assert "Altered mental" in result["detail"]

    def test_score_with_y_n(self):
        """Single letter y/n values should be accepted."""
        present = {"Hypotension": "y", "Tachycardia": "n"}
        result = geneva.calculate_score(present)
        assert result["score"] == 1

    def test_tier_moderate(self):
        """Score of 3-4 should return moderate tier."""
        present = {"Hypotension": 1, "Tachycardia": 1, "Tachypnea": 1}
        result = geneva.calculate_score(present)
        assert result["score"] == 3
        assert result["tier"] == "moderate"

    def test_tier_low_boundary(self):
        """Score of 2 or less should return low tier."""
        present = {"Hypotension": 1, "Tachycardia": 1}
        result = geneva.calculate_score(present)
        assert result["score"] == 2
        assert result["tier"] == "low"

    def test_tier_high(self):
        """Score above 4 should return high tier."""
        present = {"Hypotension": 1, "Tachycardia": 1, "Tachypnea": 1,
                   "Fever": 1, "Altered mental": 1}
        result = geneva.calculate_score(present)
        assert result["score"] == 5
        assert result["tier"] == "high"

    def test_score_with_lowercase_keys(self):
        """Lowercase keys should be matched."""
        present = {"hypotension": 1, "tachycardia": 1}
        result = geneva.calculate_score(present)
        assert result["score"] == 2


class TestProcessCSV:
    """Tests for the CSV processing function."""

    def test_file_not_found(self):
        """Non-existent input file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            geneva.process_csv("nonexistent_file.csv", "output.csv")

    def test_empty_csv(self):
        """Empty CSV (no headers) should raise ValueError."""
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        try:
            with open(path, 'w') as f:
                f.write("")
            with pytest.raises(ValueError):
                geneva.process_csv(path, "output.csv")
        finally:
            os.unlink(path)

    def test_csv_no_data_rows(self):
        """CSV with headers but no data should raise ValueError."""
        fd, path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        try:
            with open(path, 'w') as f:
                f.write("patient_id,age,sex\n")
            with pytest.raises(ValueError):
                geneva.process_csv(path, "output.csv")
        finally:
            os.unlink(path)

    def test_valid_csv_processing(self):
        """Valid CSV should be processed and results written."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("patient_id,age,sex,prior_vte,cancer,immobility,surgery\n")
            f.write("P001,68,M,0,1,1,0\n")
            f.write("P002,45,F,0,0,0,1\n")
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as out:
            output_path = out.name

        try:
            results = geneva.process_csv(input_path, output_path)
            assert len(results) == 2
            assert "score" in results[0]
            assert "tier" in results[0]
            assert "detail" in results[0]

            # Verify output file exists and has content
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
                assert "score" in content
                assert "tier" in content
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_output_directory_creation(self):
        """Output directory should be created if it doesn't exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("patient_id,age,sex\n")
            f.write("P001,68,M\n")
            f.flush()
            input_path = f.name

        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "subdir", "output.csv")

        try:
            results = geneva.process_csv(input_path, output_path)
            assert len(results) == 1
            assert os.path.exists(output_path)
        finally:
            os.unlink(input_path)
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLI:
    """Tests for the CLI main function."""

    def test_single_command(self):
        """Single command should return 0."""
        result = geneva.main(["single", "--age", "68", "--sex", "M"])
        assert result == 0

    def test_batch_command_invalid_file(self):
        """Batch command with invalid file should return error code."""
        result = geneva.main(["batch", "--input", "nonexistent.csv", "--output", "out.csv"])
        assert result == 1

    def test_single_with_json(self):
        """Single command with JSON input should work."""
        result = geneva.main(["single", "--json", '{"Hypotension": 1}'])
        assert result == 0

    def test_single_with_invalid_json(self):
        """Single command with invalid JSON should return error."""
        result = geneva.main(["single", "--json", 'not valid json'])
        assert result == 1


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
