"""Integration tests against live BZSt eVatR and VIES APIs.

Run with: make test-integration
Requires network access. These tests are EXCLUDED from CI by default.
"""

from __future__ import annotations

import pytest

from ustidnr_mcp.bzst_client import BZStClient
from ustidnr_mcp.errors import BZStConnectionError
from ustidnr_mcp.validator import normalize_vat_id, validate_format, validate_german_check_digit
from ustidnr_mcp.vies_client import VIESClient


@pytest.mark.integration
class TestLiveVIES:
    """Live VIES API tests — requires internet connectivity."""

    @pytest.mark.asyncio
    async def test_validate_known_german_id(self) -> None:
        """DE129273398 is a known valid German USt-IdNr (Bundesanzeiger Verlag)."""
        client = VIESClient(timeout=15.0)
        try:
            result = await client.validate("DE129273398")
            # VIES may return valid or service unavailable — both are acceptable
            assert result.error_code in ("200", "202", "203", "207", "217")
            assert result.country_code == "DE"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_validate_invalid_id_rejected(self) -> None:
        """A fabricated VAT ID should be rejected."""
        client = VIESClient(timeout=15.0)
        try:
            result = await client.validate("DE000000001")
            # Should be invalid (not registered) or service error
            if result.error_code == "200":
                # Extremely unlikely but possible if this ID is assigned
                pass
            else:
                assert result.valid is False
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_validate_french_id(self) -> None:
        """Test with a non-German EU country."""
        client = VIESClient(timeout=15.0)
        try:
            result = await client.validate("FR40303265045")
            assert result.country_code == "FR"
            assert result.error_code in ("200", "202", "203", "207", "217")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_format_check_before_api(self) -> None:
        """End-to-end: format check → API call."""
        vat_id = "DE129273398"
        normalized = normalize_vat_id(vat_id)
        valid, cc, _ = validate_format(normalized)
        assert valid is True
        assert cc == "DE"
        assert validate_german_check_digit(normalized) is True

        client = VIESClient(timeout=15.0)
        try:
            result = await client.validate(normalized)
            assert result.vat_id == normalized
        finally:
            await client.close()


@pytest.mark.integration
class TestLiveBZSt:
    """Live BZSt eVatR REST API tests — requires internet + valid German USt-IdNr."""

    @pytest.mark.asyncio
    async def test_simple_validation(self) -> None:
        """Simple validation against live BZSt API.

        Note: This requires a valid German USt-IdNr as own_vat_id.
        DE129273398 (Bundesanzeiger Verlag) is used as a known valid ID.
        The API may reject this if the ID is not authorized for queries.
        """
        client = BZStClient(timeout=15.0)
        try:
            result = await client.validate_simple(
                own_vat_id="DE129273398",
                partner_vat_id="FR40303265045",
            )
            # Accept any response — we're testing connectivity, not validity
            assert result.vat_id == "FR40303265045"
            assert result.error_code != ""
        except BZStConnectionError:
            # Connection issues are acceptable in integration tests
            pytest.skip("BZSt API not reachable")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_qualified_confirmation(self) -> None:
        """Qualified confirmation against live BZSt API."""
        client = BZStClient(timeout=15.0)
        try:
            result = await client.validate_qualified(
                own_vat_id="DE129273398",
                partner_vat_id="FR40303265045",
                company_name="TOTAL ENERGIES SE",
                city="COURBEVOIE",
            )
            assert result.own_vat_id == "DE129273398"
            assert result.partner_vat_id == "FR40303265045"
            assert result.error_code != ""
        except BZStConnectionError:
            pytest.skip("BZSt API not reachable")
        finally:
            await client.close()
