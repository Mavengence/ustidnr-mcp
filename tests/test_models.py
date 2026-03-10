"""Tests for Pydantic models and enums."""

from __future__ import annotations

import pytest

from ustidnr_mcp.models import (
    BZST_STATUS_MAP,
    BatchValidationResult,
    ErrorCode,
    MatchCode,
    QualifiedConfirmationResult,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_serialization_roundtrip(self) -> None:
        result = ValidationResult(
            vat_id="DE123456789",
            valid=True,
            error_code="200",
            error_description="Gültig.",
            country_code="DE",
            company_name="Test GmbH",
            company_address="Hauptstraße 1",
            request_date="2026-03-10",
        )
        data = result.model_dump()
        restored = ValidationResult(**data)
        assert restored == result

    def test_default_values(self) -> None:
        result = ValidationResult(
            vat_id="DE123456789",
            valid=True,
            error_code="200",
            error_description="OK",
        )
        assert result.country_code == ""
        assert result.company_name == ""
        assert result.company_address == ""
        assert result.request_date == ""
        assert result.raw_response == {}

    def test_with_raw_response(self) -> None:
        raw = {"status": "evatr-0000", "id": "abc-123"}
        result = ValidationResult(
            vat_id="DE123456789",
            valid=True,
            error_code="200",
            error_description="OK",
            raw_response=raw,
        )
        assert result.raw_response["id"] == "abc-123"

    def test_json_serialization(self) -> None:
        result = ValidationResult(
            vat_id="DE123456789",
            valid=True,
            error_code="200",
            error_description="Gültig.",
        )
        json_str = result.model_dump_json()
        assert "DE123456789" in json_str
        assert "true" in json_str.lower()

    def test_empty_vat_id(self) -> None:
        result = ValidationResult(
            vat_id="",
            valid=False,
            error_code="201",
            error_description="Empty",
        )
        assert result.vat_id == ""

    def test_unicode_fields(self) -> None:
        result = ValidationResult(
            vat_id="DE123456789",
            valid=True,
            error_code="200",
            error_description="Gültig.",
            company_name="Müller & Söhne GmbH",
            company_address="Königstraße 42, München",
        )
        data = result.model_dump()
        assert data["company_name"] == "Müller & Söhne GmbH"


# ---------------------------------------------------------------------------
# QualifiedConfirmationResult
# ---------------------------------------------------------------------------


class TestQualifiedConfirmationResult:
    def test_all_fields_match_true(self) -> None:
        result = QualifiedConfirmationResult(
            own_vat_id="DE123456789",
            partner_vat_id="FR12345678901",
            valid=True,
            error_code="200",
            error_description="OK",
            company_name_match="A",
            city_match="A",
            zip_match="A",
            street_match="A",
        )
        assert result.all_fields_match is True

    def test_all_fields_match_false_with_b(self) -> None:
        result = QualifiedConfirmationResult(
            own_vat_id="DE123456789",
            partner_vat_id="FR12345678901",
            valid=True,
            error_code="200",
            error_description="OK",
            company_name_match="A",
            city_match="B",
            zip_match="A",
            street_match="A",
        )
        assert result.all_fields_match is False

    def test_c_codes_ignored(self) -> None:
        result = QualifiedConfirmationResult(
            own_vat_id="DE123456789",
            partner_vat_id="FR12345678901",
            valid=True,
            error_code="200",
            error_description="OK",
            company_name_match="A",
            city_match="C",
            zip_match="C",
            street_match="C",
        )
        assert result.all_fields_match is True

    def test_d_codes_not_ignored(self) -> None:
        """D (not available) is not a match."""
        result = QualifiedConfirmationResult(
            own_vat_id="DE123456789",
            partner_vat_id="FR12345678901",
            valid=True,
            error_code="200",
            error_description="OK",
            company_name_match="A",
            city_match="D",
            zip_match="A",
            street_match="A",
        )
        assert result.all_fields_match is False

    def test_empty_match_codes_ignored(self) -> None:
        """Empty match codes are falsy and skipped."""
        result = QualifiedConfirmationResult(
            own_vat_id="DE123456789",
            partner_vat_id="FR12345678901",
            valid=True,
            error_code="200",
            error_description="OK",
            company_name_match="",
            city_match="",
            zip_match="",
            street_match="",
        )
        # All empty → nothing to check → vacuously true
        assert result.all_fields_match is True

    def test_serialization_roundtrip(self) -> None:
        result = QualifiedConfirmationResult(
            own_vat_id="DE123456789",
            partner_vat_id="FR12345678901",
            valid=True,
            error_code="200",
            error_description="OK",
            company_name_match="A",
            city_match="B",
            zip_match="C",
            street_match="D",
        )
        data = result.model_dump()
        restored = QualifiedConfirmationResult(**data)
        assert restored.company_name_match == "A"
        assert restored.city_match == "B"

    def test_mixed_match_and_not_requested(self) -> None:
        result = QualifiedConfirmationResult(
            own_vat_id="DE123456789",
            partner_vat_id="FR12345678901",
            valid=True,
            error_code="200",
            error_description="OK",
            company_name_match="A",
            city_match="A",
            zip_match="C",
            street_match="C",
        )
        assert result.all_fields_match is True


# ---------------------------------------------------------------------------
# BatchValidationResult
# ---------------------------------------------------------------------------


class TestBatchValidationResult:
    def test_basic(self) -> None:
        results = [
            ValidationResult(
                vat_id="DE123456789", valid=True, error_code="200", error_description="OK"
            ),
            ValidationResult(
                vat_id="XX999", valid=False, error_code="201", error_description="Invalid"
            ),
        ]
        batch = BatchValidationResult(
            results=results, total=2, valid_count=1, invalid_count=1, error_count=0
        )
        assert batch.total == 2
        assert batch.valid_count == 1
        assert batch.invalid_count == 1
        assert batch.error_count == 0

    def test_serialization(self) -> None:
        batch = BatchValidationResult(
            results=[], total=0, valid_count=0, invalid_count=0, error_count=0
        )
        data = batch.model_dump()
        assert data["total"] == 0
        assert data["results"] == []

    def test_with_errors(self) -> None:
        results = [
            ValidationResult(
                vat_id="DE123456789", valid=False, error_code="217", error_description="Timeout"
            ),
        ]
        batch = BatchValidationResult(
            results=results, total=1, valid_count=0, invalid_count=0, error_count=1
        )
        assert batch.error_count == 1

    def test_all_valid(self) -> None:
        results = [
            ValidationResult(
                vat_id=f"FR{i:011d}", valid=True, error_code="200", error_description="OK"
            )
            for i in range(5)
        ]
        batch = BatchValidationResult(
            results=results, total=5, valid_count=5, invalid_count=0, error_count=0
        )
        assert batch.valid_count == 5
        assert len(batch.results) == 5


# ---------------------------------------------------------------------------
# ErrorCode enum
# ---------------------------------------------------------------------------


class TestErrorCode:
    def test_valid_code(self) -> None:
        code = ErrorCode("200")
        assert code == ErrorCode.VALID
        assert "gültig" in code.description_de

    def test_invalid_code(self) -> None:
        code = ErrorCode("202")
        assert code == ErrorCode.NOT_REGISTERED
        assert "ungültig" in code.description_de

    def test_all_codes_have_descriptions(self) -> None:
        for code in ErrorCode:
            desc = code.description_de
            assert desc != ""
            assert "Unbekannter" not in desc

    def test_all_codes_have_unique_values(self) -> None:
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))

    def test_unknown_value_raises(self) -> None:
        with pytest.raises(ValueError):
            ErrorCode("999")

    @pytest.mark.parametrize(
        "code_value,expected_name",
        [
            ("200", "VALID"),
            ("201", "INVALID_FORMAT"),
            ("202", "NOT_REGISTERED"),
            ("217", "SERVICE_TEMP_UNAVAILABLE"),
            ("219", "VALID_QUALIFIED"),
        ],
    )
    def test_code_names(self, code_value: str, expected_name: str) -> None:
        assert ErrorCode(code_value).name == expected_name


# ---------------------------------------------------------------------------
# MatchCode enum
# ---------------------------------------------------------------------------


class TestMatchCode:
    def test_values(self) -> None:
        assert MatchCode.MATCH.value == "A"
        assert MatchCode.NO_MATCH.value == "B"
        assert MatchCode.NOT_REQUESTED.value == "C"
        assert MatchCode.NOT_AVAILABLE.value == "D"

    def test_all_values_unique(self) -> None:
        values = [code.value for code in MatchCode]
        assert len(values) == len(set(values))

    def test_four_members(self) -> None:
        assert len(MatchCode) == 4


# ---------------------------------------------------------------------------
# BZST_STATUS_MAP
# ---------------------------------------------------------------------------


class TestBzstStatusMap:
    def test_has_entries(self) -> None:
        assert len(BZST_STATUS_MAP) > 0

    def test_all_values_are_tuples(self) -> None:
        for _status, (code, valid) in BZST_STATUS_MAP.items():
            assert isinstance(code, str)
            assert isinstance(valid, bool)

    def test_valid_statuses(self) -> None:
        """Only evatr-0000 and evatr-2008 should be valid."""
        valid_statuses = [s for s, (_, v) in BZST_STATUS_MAP.items() if v]
        assert "evatr-0000" in valid_statuses
        assert "evatr-2008" in valid_statuses

    def test_all_internal_codes_valid(self) -> None:
        """All mapped internal codes should be valid ErrorCode values."""
        for _, (code, _) in BZST_STATUS_MAP.items():
            ErrorCode(code)  # Should not raise
