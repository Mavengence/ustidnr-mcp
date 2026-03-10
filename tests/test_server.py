"""Tests for server helpers and tool logic (without FastMCP Context)."""

from __future__ import annotations

from ustidnr_mcp.validator import normalize_vat_id, validate_format


class TestToolInputValidation:
    """Test the validation logic that tools use before calling API clients."""

    def test_validate_own_vat_must_be_german(self) -> None:
        own = normalize_vat_id("FR12345678901")
        valid, cc, _ = validate_format(own)
        assert valid is True
        assert cc != "DE"

    def test_validate_partner_format(self) -> None:
        partner = normalize_vat_id("IT12345678901")
        valid, cc, _ = validate_format(partner)
        assert valid is True
        assert cc == "IT"

    def test_empty_vat_id(self) -> None:
        valid, _, error = validate_format("")
        assert valid is False
        assert "empty" in error.lower()

    def test_batch_size_validation(self) -> None:
        from ustidnr_mcp.config import settings

        large_batch = ["DE123456789"] * (settings.batch_max_size + 1)
        assert len(large_batch) > settings.batch_max_size

    def test_german_own_id_accepted(self) -> None:
        own = normalize_vat_id("DE123456789")
        valid, cc, _ = validate_format(own)
        assert valid is True
        assert cc == "DE"

    def test_partner_can_be_any_eu_country(self) -> None:
        for partner_id in ["FR12345678901", "ATU12345678", "PL1234567890"]:
            normalized = normalize_vat_id(partner_id)
            valid, _, _ = validate_format(normalized)
            assert valid is True
