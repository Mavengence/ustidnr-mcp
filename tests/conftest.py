"""Shared test fixtures — Pydantic model-based fixtures for reuse."""

from __future__ import annotations

from typing import Any

import pytest

from ustidnr_mcp.bzst_client import BZStClient
from ustidnr_mcp.models import (
    QualifiedConfirmationResult,
    ValidationResult,
)
from ustidnr_mcp.vies_client import VIESClient

# ---------------------------------------------------------------------------
# VAT ID fixtures (raw data)
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_german_vat_ids() -> list[str]:
    """Known valid German USt-IdNr format examples."""
    return [
        "DE123456789",
        "DE999999999",
        "DE000000000",
        "DE129273398",
        "DE811569869",
    ]


@pytest.fixture
def valid_eu_vat_ids() -> list[str]:
    """Known valid EU USt-IdNr format examples (various countries)."""
    return [
        "ATU12345678",
        "BE0123456789",
        "BG123456789",
        "CY12345678A",
        "CZ12345678",
        "DK12345678",
        "EE123456789",
        "EL123456789",
        "ESA12345678",
        "FI12345678",
        "FR12345678901",
        "HR12345678901",
        "HU12345678",
        "IE1234567A",
        "IT12345678901",
        "LT123456789",
        "LU12345678",
        "LV12345678901",
        "MT12345678",
        "NL123456789B01",
        "PL1234567890",
        "PT123456789",
        "RO1234567890",
        "SE123456789012",
        "SI12345678",
        "SK1234567890",
    ]


@pytest.fixture
def invalid_vat_ids() -> list[str]:
    """Known invalid USt-IdNr examples."""
    return [
        "",
        "DE12345",  # too short
        "DE1234567890",  # too long
        "XX123456789",  # unknown country
        "12345678",  # no prefix
        "ABCDEFGHIJK",  # all letters
        "DE12345678A",  # letter in digits
        "   ",  # whitespace only
    ]


# ---------------------------------------------------------------------------
# Model fixtures (Pydantic objects)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_valid_result() -> ValidationResult:
    """A sample valid ValidationResult."""
    return ValidationResult(
        vat_id="FR12345678901",
        valid=True,
        error_code="200",
        error_description="Die angefragte USt-IdNr. ist gültig.",
        country_code="FR",
        company_name="Acme SARL",
        company_address="1 Rue de Rivoli, 75001 Paris",
        request_date="2026-03-10",
    )


@pytest.fixture
def sample_invalid_result() -> ValidationResult:
    """A sample invalid ValidationResult."""
    return ValidationResult(
        vat_id="FR00000000000",
        valid=False,
        error_code="202",
        error_description="Die angefragte USt-IdNr. ist ungültig (nicht vergeben).",
        country_code="FR",
    )


@pytest.fixture
def sample_qualified_result() -> QualifiedConfirmationResult:
    """A sample QualifiedConfirmationResult with all fields matching."""
    return QualifiedConfirmationResult(
        own_vat_id="DE123456789",
        partner_vat_id="FR12345678901",
        valid=True,
        error_code="200",
        error_description="Die angefragte USt-IdNr. ist gültig.",
        company_name_match="A",
        city_match="A",
        zip_match="A",
        street_match="A",
        request_date="2026-03-10T12:00:00",
    )


@pytest.fixture
def sample_partial_match_result() -> QualifiedConfirmationResult:
    """A qualified result where street doesn't match."""
    return QualifiedConfirmationResult(
        own_vat_id="DE123456789",
        partner_vat_id="FR12345678901",
        valid=True,
        error_code="200",
        error_description="Die angefragte USt-IdNr. ist gültig.",
        company_name_match="A",
        city_match="A",
        zip_match="A",
        street_match="B",
    )


# ---------------------------------------------------------------------------
# BZSt mock response fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bzst_valid_response() -> dict[str, Any]:
    """BZSt JSON response for a valid VAT ID."""
    return {
        "status": "evatr-0000",
        "anfragendeUstid": "DE123456789",
        "angefragteUstid": "FR12345678901",
        "anfrageZeitpunkt": "2026-03-10T12:00:00",
        "firmenname": "Acme SARL",
        "strasse": "Rue de Rivoli 1",
        "ort": "Paris",
        "plz": "75001",
        "message": "Die angefragte USt-IdNr. ist gültig.",
    }


@pytest.fixture
def bzst_qualified_response() -> dict[str, Any]:
    """BZSt JSON response for a qualified confirmation."""
    return {
        "status": "evatr-0000",
        "ergFirmenname": "A",
        "ergOrt": "A",
        "ergPlz": "A",
        "ergStrasse": "A",
        "anfrageZeitpunkt": "2026-03-10T12:00:00",
        "message": "Die angefragte USt-IdNr. ist gültig.",
    }


@pytest.fixture
def bzst_invalid_response() -> dict[str, Any]:
    """BZSt JSON response for an invalid VAT ID."""
    return {
        "status": "evatr-2001",
        "anfrageZeitpunkt": "2026-03-10T12:00:00",
        "message": "Die angefragte USt-IdNr. ist nicht vergeben.",
    }


@pytest.fixture
def vies_valid_response() -> dict[str, Any]:
    """VIES JSON response for a valid VAT ID."""
    return {
        "valid": True,
        "countryCode": "FR",
        "vatNumber": "12345678901",
        "requestDate": "2026-03-10",
        "name": "Acme SARL",
        "address": "1 Rue de Rivoli\n75001 Paris",
    }


# ---------------------------------------------------------------------------
# Client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bzst_client() -> BZStClient:
    """BZSt client configured for testing."""
    return BZStClient(base_url="https://test.example.com/api/v1/abfrage")


@pytest.fixture
def vies_client() -> VIESClient:
    """VIES client configured for testing."""
    return VIESClient(timeout=5.0)
