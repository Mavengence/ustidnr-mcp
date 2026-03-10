"""Tests for format validation logic."""

from __future__ import annotations

import pytest

from ustidnr_mcp.models import EU_VAT_FORMATS
from ustidnr_mcp.validator import (
    extract_country_code,
    normalize_vat_id,
    sanitize_input,
    validate_format,
    validate_german_check_digit,
)

# ---------------------------------------------------------------------------
# sanitize_input
# ---------------------------------------------------------------------------


class TestSanitizeInput:
    def test_strips_null_bytes(self) -> None:
        assert sanitize_input("DE\x00123") == "DE123"

    def test_strips_control_chars(self) -> None:
        assert sanitize_input("DE\x01\x02\x03123") == "DE123"

    def test_preserves_normal_whitespace(self) -> None:
        assert sanitize_input("DE 123") == "DE 123"

    def test_preserves_tabs_newlines(self) -> None:
        # \t and \n are useful whitespace — kept
        result = sanitize_input("DE\t123\n")
        assert "\t" in result
        assert "\n" in result

    def test_enforces_max_length(self) -> None:
        long_input = "A" * 500
        result = sanitize_input(long_input, max_length=100)
        assert len(result) == 100

    def test_default_max_length(self) -> None:
        long_input = "A" * 1000
        result = sanitize_input(long_input)
        assert len(result) <= 256

    def test_empty_string(self) -> None:
        assert sanitize_input("") == ""

    def test_unicode_preserved(self) -> None:
        assert sanitize_input("Müller GmbH") == "Müller GmbH"

    def test_chinese_chars_preserved(self) -> None:
        assert sanitize_input("公司名称") == "公司名称"

    def test_del_char_removed(self) -> None:
        assert sanitize_input("DE\x7f123") == "DE123"


# ---------------------------------------------------------------------------
# normalize_vat_id
# ---------------------------------------------------------------------------


class TestNormalizeVatId:
    def test_strips_whitespace(self) -> None:
        assert normalize_vat_id("  DE 123 456 789  ") == "DE123456789"

    def test_uppercases(self) -> None:
        assert normalize_vat_id("de123456789") == "DE123456789"

    def test_removes_dots_dashes(self) -> None:
        assert normalize_vat_id("DE-123.456.789") == "DE123456789"

    def test_removes_slashes(self) -> None:
        assert normalize_vat_id("DE/123/456/789") == "DE123456789"

    def test_empty_string(self) -> None:
        assert normalize_vat_id("") == ""

    def test_already_clean(self) -> None:
        assert normalize_vat_id("DE123456789") == "DE123456789"

    def test_strips_control_characters(self) -> None:
        assert normalize_vat_id("DE\x00123456789") == "DE123456789"

    def test_truncates_very_long_input(self) -> None:
        long_id = "DE" + "1" * 200
        result = normalize_vat_id(long_id)
        assert len(result) <= 50


# ---------------------------------------------------------------------------
# extract_country_code
# ---------------------------------------------------------------------------


class TestExtractCountryCode:
    def test_german(self) -> None:
        assert extract_country_code("DE123456789") == "DE"

    def test_french(self) -> None:
        assert extract_country_code("FR12345678901") == "FR"

    def test_austrian(self) -> None:
        assert extract_country_code("ATU12345678") == "AT"

    def test_unknown_prefix(self) -> None:
        assert extract_country_code("XX123456789") == ""

    def test_too_short(self) -> None:
        assert extract_country_code("D") == ""

    def test_empty(self) -> None:
        assert extract_country_code("") == ""

    def test_lowercase_normalized(self) -> None:
        assert extract_country_code("de123456789") == "DE"

    def test_greece_el(self) -> None:
        assert extract_country_code("EL123456789") == "EL"

    @pytest.mark.parametrize("code", sorted(EU_VAT_FORMATS.keys()))
    def test_all_27_country_codes(self, code: str) -> None:
        """Every EU country code is recognized."""
        test_id = code + "123456789"
        assert extract_country_code(test_id) == code


# ---------------------------------------------------------------------------
# validate_format — valid formats (all 27 countries, multiple per country)
# ---------------------------------------------------------------------------


class TestValidateFormat:
    @pytest.mark.parametrize(
        "vat_id",
        [
            # AT — Austria
            "ATU12345678",
            "ATU00000000",
            "ATU99999999",
            # BE — Belgium
            "BE0123456789",
            "BE1123456789",
            # BG — Bulgaria (9 or 10 digits)
            "BG123456789",
            "BG1234567890",
            # CY — Cyprus
            "CY12345678A",
            "CY12345678Z",
            # CZ — Czech Republic (8, 9, or 10 digits)
            "CZ12345678",
            "CZ123456789",
            "CZ1234567890",
            # DE — Germany
            "DE123456789",
            "DE000000000",
            "DE999999999",
            # DK — Denmark
            "DK12345678",
            # EE — Estonia
            "EE123456789",
            # EL — Greece
            "EL123456789",
            # ES — Spain
            "ESA12345678",
            "ES12345678A",
            "ESA1234567B",
            # FI — Finland
            "FI12345678",
            # FR — France (2 alphanumeric + 9 digits)
            "FR12345678901",
            "FRAB123456789",
            "FR1A123456789",
            # HR — Croatia
            "HR12345678901",
            # HU — Hungary
            "HU12345678",
            # IE — Ireland
            "IE1234567A",
            "IE1234567AB",
            "IE1A23456A",
            # IT — Italy
            "IT12345678901",
            # LT — Lithuania (9 or 12 digits)
            "LT123456789",
            "LT123456789012",
            # LU — Luxembourg
            "LU12345678",
            # LV — Latvia
            "LV12345678901",
            # MT — Malta
            "MT12345678",
            # NL — Netherlands
            "NL123456789B01",
            "NL123456789B99",
            # PL — Poland
            "PL1234567890",
            # PT — Portugal
            "PT123456789",
            # RO — Romania (2-10 digits)
            "RO12",
            "RO123",
            "RO1234567890",
            # SE — Sweden
            "SE123456789012",
            # SI — Slovenia
            "SI12345678",
            # SK — Slovakia
            "SK1234567890",
        ],
    )
    def test_valid_formats(self, vat_id: str) -> None:
        valid, country_code, error = validate_format(vat_id)
        assert valid is True, f"{vat_id} should be valid, got error: {error}"
        assert country_code == vat_id[:2]
        assert error == ""

    @pytest.mark.parametrize(
        "vat_id,expected_code",
        [
            ("DE12345", "DE"),  # too short
            ("DE1234567890", "DE"),  # too long
            ("ATU1234567", "AT"),  # too short
            ("BE12345", "BE"),  # too short
            ("NL123456789A01", "NL"),  # wrong letter position
            ("DE12345678A", "DE"),  # letter in digits
            ("ATU123456789", "AT"),  # too long
            ("BG12345678901", "BG"),  # too long (max 10)
            ("CZ1234567", "CZ"),  # too short (min 8)
            ("CZ12345678901", "CZ"),  # too long (max 10)
            ("DK1234567", "DK"),  # too short
            ("DK123456789", "DK"),  # too long
            ("EE12345678", "EE"),  # too short
            ("EL12345678", "EL"),  # too short
            ("FI1234567", "FI"),  # too short
            ("HR1234567890", "HR"),  # too short
            ("HU1234567", "HU"),  # too short
            ("IT1234567890", "IT"),  # too short
            ("LU1234567", "LU"),  # too short
            ("MT1234567", "MT"),  # too short
            ("PL123456789", "PL"),  # too short
            ("PT12345678", "PT"),  # too short
            ("SE12345678901", "SE"),  # too short
            ("SI1234567", "SI"),  # too short
            ("SK123456789", "SK"),  # too short
        ],
    )
    def test_invalid_formats(self, vat_id: str, expected_code: str) -> None:
        valid, country_code, error = validate_format(vat_id)
        assert valid is False
        assert country_code == expected_code
        assert error != ""

    def test_empty_string(self) -> None:
        valid, _country_code, error = validate_format("")
        assert valid is False
        assert error == "VAT ID is empty."

    def test_unknown_country(self) -> None:
        valid, country_code, error = validate_format("XX123456789")
        assert valid is False
        assert country_code == ""
        assert "Unknown country prefix" in error

    def test_normalizes_input(self) -> None:
        valid, country_code, _error = validate_format("de 123 456 789")
        assert valid is True
        assert country_code == "DE"

    def test_all_eu_countries_have_patterns(self) -> None:
        assert len(EU_VAT_FORMATS) == 27

    def test_whitespace_only(self) -> None:
        valid, _, error = validate_format("   ")
        assert valid is False
        assert "empty" in error.lower()

    def test_single_char(self) -> None:
        valid, _, _ = validate_format("D")
        assert valid is False

    def test_two_chars(self) -> None:
        valid, _, _ = validate_format("DE")
        assert valid is False

    def test_only_country_code(self) -> None:
        valid, _cc, _ = validate_format("DE")
        assert valid is False

    @pytest.mark.parametrize(
        "separator",
        [" ", ".", "-", "/", ". "],
    )
    def test_separators_normalized(self, separator: str) -> None:
        vat_id = f"DE{separator}123{separator}456{separator}789"
        valid, _, _ = validate_format(vat_id)
        assert valid is True


# ---------------------------------------------------------------------------
# validate_german_check_digit
# ---------------------------------------------------------------------------


class TestValidateGermanCheckDigit:
    def test_known_valid_id(self) -> None:
        assert validate_german_check_digit("DE129273398") is True

    def test_invalid_check_digit(self) -> None:
        assert validate_german_check_digit("DE129273399") is False

    def test_invalid_format(self) -> None:
        assert validate_german_check_digit("DE12345") is False

    def test_non_german(self) -> None:
        assert validate_german_check_digit("FR12345678901") is False

    def test_normalizes_input(self) -> None:
        assert validate_german_check_digit("de 129 273 398") is True

    def test_all_zeros(self) -> None:
        result = validate_german_check_digit("DE000000000")
        assert isinstance(result, bool)

    def test_all_nines(self) -> None:
        result = validate_german_check_digit("DE999999999")
        assert isinstance(result, bool)

    @pytest.mark.parametrize(
        "vat_id",
        [
            "DE129273398",
            "DE811569869",
            "DE136695976",
            "DE260543043",
            "DE114103379",
        ],
    )
    def test_known_valid_ids(self, vat_id: str) -> None:
        assert validate_german_check_digit(vat_id) is True

    @pytest.mark.parametrize(
        "vat_id",
        [
            "DE129273390",
            "DE129273391",
            "DE129273392",
            "DE129273393",
            "DE129273394",
            "DE129273395",
            "DE129273396",
            "DE129273397",
            "DE129273399",
        ],
    )
    def test_wrong_check_digits(self, vat_id: str) -> None:
        """Only DE129273398 is valid — all others should fail."""
        assert validate_german_check_digit(vat_id) is False

    def test_empty_string(self) -> None:
        assert validate_german_check_digit("") is False

    def test_too_long(self) -> None:
        assert validate_german_check_digit("DE1234567890") is False

    def test_letters_in_digits(self) -> None:
        assert validate_german_check_digit("DE12345678A") is False

    def test_with_control_chars(self) -> None:
        # Control chars get stripped by normalize
        assert validate_german_check_digit("DE\x00129273398") is True

    def test_product_zero_transition(self) -> None:
        """Exercise the total==0 branch in the algorithm."""
        # DE100000009 — first digit is 1, rest zeros
        # (1 + 10) % 10 = 1, product = (2*1) % 11 = 2
        # (0 + 2) % 10 = 2, product = (2*2) % 11 = 4
        # ... etc.
        result = validate_german_check_digit("DE100000009")
        assert isinstance(result, bool)
