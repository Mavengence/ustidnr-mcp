"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def valid_german_vat_ids() -> list[str]:
    """Known valid German USt-IdNr format examples."""
    return [
        "DE123456789",
        "DE999999999",
        "DE000000000",
    ]


@pytest.fixture
def valid_eu_vat_ids() -> list[str]:
    """Known valid EU USt-IdNr format examples (various countries)."""
    return [
        "ATU12345678",
        "BE0123456789",
        "FR12345678901",
        "NL123456789B01",
        "PL1234567890",
        "IT12345678901",
        "ES A12345678",  # with space — should be normalized
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
    ]
