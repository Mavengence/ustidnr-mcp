"""Integration tests — full tool flows with mocked APIs."""

from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from ustidnr_mcp.bzst_client import BZStClient
from ustidnr_mcp.errors import BZStConnectionError
from ustidnr_mcp.models import BatchValidationResult, ValidationResult
from ustidnr_mcp.validator import normalize_vat_id, validate_format
from ustidnr_mcp.vies_client import VIES_REST_URL, VIESClient


class TestSimpleValidationFlow:
    """Full flow: format check → API call → result."""

    @pytest.mark.asyncio
    async def test_valid_french_id_via_vies(self) -> None:
        vat_id = "FR12345678901"
        normalized = normalize_vat_id(vat_id)
        valid, cc, _ = validate_format(normalized)
        assert valid is True
        assert cc == "FR"

        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": True,
                        "countryCode": "FR",
                        "vatNumber": "12345678901",
                        "name": "Acme SARL",
                        "address": "Paris",
                    },
                )
            )
            result = await client.validate(normalized)

        assert result.valid is True
        assert result.company_name == "Acme SARL"
        await client.close()

    @pytest.mark.asyncio
    async def test_invalid_format_skips_api(self) -> None:
        vat_id = "XX123"
        normalized = normalize_vat_id(vat_id)
        valid, cc, error = validate_format(normalized)
        assert valid is False
        # No API call needed — format check rejects it
        result = ValidationResult(
            vat_id=normalized,
            valid=False,
            error_code="201",
            error_description=error,
            country_code=cc,
        )
        assert result.error_code == "201"

    @pytest.mark.asyncio
    async def test_german_id_format_then_vies(self) -> None:
        vat_id = "DE129273398"
        normalized = normalize_vat_id(vat_id)
        valid, cc, _ = validate_format(normalized)
        assert valid is True
        assert cc == "DE"

        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": True,
                        "countryCode": "DE",
                        "vatNumber": "129273398",
                    },
                )
            )
            result = await client.validate(normalized)

        assert result.valid is True
        await client.close()


class TestQualifiedConfirmationFlow:
    """Full flow: format check both IDs → BZSt qualified → result."""

    @pytest.mark.asyncio
    async def test_full_qualified_flow(self) -> None:
        own = normalize_vat_id("DE123456789")
        partner = normalize_vat_id("FR12345678901")

        own_valid, own_cc, _ = validate_format(own)
        assert own_valid and own_cc == "DE"

        partner_valid, _, _ = validate_format(partner)
        assert partner_valid

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(
                    200,
                    json={
                        "status": "evatr-0000",
                        "ergFirmenname": "A",
                        "ergOrt": "A",
                        "ergPlz": "A",
                        "ergStrasse": "B",
                        "anfrageZeitpunkt": "2026-03-10T12:00:00",
                    },
                )
            )
            result = await client.validate_qualified(
                own_vat_id=own,
                partner_vat_id=partner,
                company_name="Acme SARL",
                city="Paris",
                zip_code="75001",
                street="Rue de Rivoli 1",
            )

        assert result.valid is True
        assert result.company_name_match == "A"
        assert result.street_match == "B"
        assert result.all_fields_match is False
        await client.close()

    @pytest.mark.asyncio
    async def test_non_german_own_id_rejected(self) -> None:
        own = normalize_vat_id("FR12345678901")
        _, own_cc, _ = validate_format(own)
        assert own_cc != "DE"

    @pytest.mark.asyncio
    async def test_qualified_with_bzst_error(self) -> None:
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(
                    200,
                    json={
                        "status": "evatr-0011",
                        "message": "Service temporarily unavailable.",
                    },
                )
            )
            result = await client.validate_qualified(
                own_vat_id="DE123456789",
                partner_vat_id="FR12345678901",
                company_name="Test",
                city="Paris",
            )

        assert result.valid is False
        assert result.error_code == "203"
        await client.close()


class TestBatchValidationFlow:
    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_batch(self) -> None:
        vat_ids = ["FR12345678901", "XX123", "DE123456789"]
        results: list[ValidationResult] = []

        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={"valid": True, "countryCode": "FR", "vatNumber": "12345678901"},
                )
            )

            for vid in vat_ids:
                normalized = normalize_vat_id(vid)
                valid, cc, error = validate_format(normalized)
                if not valid:
                    results.append(
                        ValidationResult(
                            vat_id=normalized or vid,
                            valid=False,
                            error_code="201",
                            error_description=error,
                            country_code=cc,
                        )
                    )
                else:
                    result = await client.validate(normalized)
                    results.append(result)

        valid_count = sum(1 for r in results if r.valid)
        invalid_count = sum(1 for r in results if not r.valid and r.error_code == "201")

        assert len(results) == 3
        assert valid_count == 2  # FR and DE both return valid from mock
        assert invalid_count == 1  # XX123
        await client.close()

    @pytest.mark.asyncio
    async def test_empty_batch(self) -> None:
        results: list[ValidationResult] = []
        batch = BatchValidationResult(
            results=results,
            total=0,
            valid_count=0,
            invalid_count=0,
            error_count=0,
        )
        assert batch.total == 0


class TestErrorPropagation:
    @pytest.mark.asyncio
    async def test_bzst_timeout_raises(self) -> None:
        import httpx

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                side_effect=httpx.TimeoutException("timeout")
            )
            with pytest.raises(BZStConnectionError):
                await client.validate_simple("DE123456789", "FR12345678901")
        await client.close()

    @pytest.mark.asyncio
    async def test_vies_timeout_returns_result(self) -> None:
        """VIES client returns a result (not raises) on timeout."""
        import httpx

        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(side_effect=httpx.TimeoutException("timeout"))
            result = await client.validate("FR12345678901")

        assert result.valid is False
        assert result.error_code == "217"
        await client.close()

    @pytest.mark.asyncio
    async def test_format_error_to_json(self) -> None:
        normalized = normalize_vat_id("XX123")
        valid, cc, error = validate_format(normalized)
        assert valid is False

        result = ValidationResult(
            vat_id=normalized,
            valid=False,
            error_code="201",
            error_description=error,
            country_code=cc,
        )
        json_str = json.dumps(result.model_dump(), ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["valid"] is False
        assert parsed["error_code"] == "201"
