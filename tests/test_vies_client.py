"""Tests for VIES API client."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ustidnr_mcp.vies_client import VIES_REST_URL, VIESClient


class TestVIESClientValidation:
    @pytest.mark.asyncio
    async def test_validate_valid(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": True,
                        "countryCode": "FR",
                        "vatNumber": "12345678901",
                        "requestDate": "2026-03-10",
                        "name": "Acme SARL",
                        "address": "1 Rue de Rivoli\n75001 Paris",
                    },
                )
            )
            result = await client.validate("FR12345678901")

        assert result.valid is True
        assert result.error_code == "200"
        assert result.company_name == "Acme SARL"
        assert result.country_code == "FR"
        assert result.request_date == "2026-03-10"
        assert "Rue de Rivoli" in result.company_address
        await client.close()

    @pytest.mark.asyncio
    async def test_validate_invalid(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": False,
                        "countryCode": "FR",
                        "vatNumber": "00000000000",
                        "requestDate": "2026-03-10",
                        "name": "---",
                        "address": "---",
                    },
                )
            )
            result = await client.validate("FR00000000000")

        assert result.valid is False
        assert result.error_code == "202"
        assert result.company_name == ""
        assert result.company_address == ""
        await client.close()

    @pytest.mark.asyncio
    async def test_null_name_address(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": True,
                        "countryCode": "EL",
                        "vatNumber": "123456789",
                        "name": None,
                        "address": None,
                    },
                )
            )
            result = await client.validate("EL123456789")

        assert result.valid is True
        assert result.company_name == ""
        assert result.company_address == ""
        await client.close()

    @pytest.mark.asyncio
    async def test_missing_name_field(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": True,
                        "countryCode": "PL",
                        "vatNumber": "1234567890",
                    },
                )
            )
            result = await client.validate("PL1234567890")

        assert result.valid is True
        assert result.company_name == ""
        await client.close()

    @pytest.mark.asyncio
    async def test_extra_fields_ignored(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": True,
                        "countryCode": "DE",
                        "vatNumber": "123456789",
                        "traderName": "Extra Field",
                        "traderAddress": "Extra Address",
                        "requestIdentifier": "WAPIaaaabbbbcccc",
                    },
                )
            )
            result = await client.validate("DE123456789")

        assert result.valid is True
        assert "traderName" in result.raw_response
        await client.close()

    @pytest.mark.asyncio
    async def test_greek_el_country_code(self) -> None:
        """Greece uses EL prefix (not GR)."""
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={"valid": True, "countryCode": "EL", "vatNumber": "123456789"},
                )
            )
            result = await client.validate("EL123456789")

        assert result.country_code == "EL"
        await client.close()

    @pytest.mark.asyncio
    async def test_multiline_address(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={
                        "valid": True,
                        "countryCode": "IT",
                        "vatNumber": "12345678901",
                        "name": "Test SRL",
                        "address": "Via Roma 1\n00100 Roma\nItalia",
                    },
                )
            )
            result = await client.validate("IT12345678901")

        assert "Via Roma" in result.company_address
        assert "\n" in result.company_address
        await client.close()


class TestVIESClientErrors:
    @pytest.mark.asyncio
    async def test_timeout(self) -> None:
        import httpx

        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(side_effect=httpx.TimeoutException("timeout"))
            result = await client.validate("FR12345678901")

        assert result.valid is False
        assert result.error_code == "217"
        await client.close()

    @pytest.mark.asyncio
    async def test_http_503_error(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(return_value=Response(503, text="Service Unavailable"))
            result = await client.validate("FR12345678901")

        assert result.valid is False
        assert result.error_code == "203"
        await client.close()

    @pytest.mark.asyncio
    async def test_http_429_rate_limit(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(return_value=Response(429, text="Too Many Requests"))
            result = await client.validate("FR12345678901")

        assert result.valid is False
        assert result.error_code == "207"
        await client.close()

    @pytest.mark.asyncio
    async def test_http_500_error(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(return_value=Response(500, text="Internal Server Error"))
            result = await client.validate("FR12345678901")

        assert result.valid is False
        assert result.error_code == "203"
        await client.close()

    @pytest.mark.asyncio
    async def test_general_error(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(side_effect=RuntimeError("connection failed"))
            result = await client.validate("FR12345678901")

        assert result.valid is False
        assert result.error_code == "216"
        await client.close()

    @pytest.mark.asyncio
    async def test_dns_error(self) -> None:
        import httpx

        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(side_effect=httpx.ConnectError("DNS lookup failed"))
            result = await client.validate("FR12345678901")

        assert result.valid is False
        assert result.error_code == "216"
        await client.close()

    @pytest.mark.asyncio
    async def test_country_code_extracted_on_error(self) -> None:
        import httpx

        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(side_effect=httpx.TimeoutException("timeout"))
            result = await client.validate("PL1234567890")

        assert result.country_code == "PL"
        await client.close()


class TestVIESClientLifecycle:
    @pytest.mark.asyncio
    async def test_close_no_client(self) -> None:
        client = VIESClient()
        await client.close()

    @pytest.mark.asyncio
    async def test_reuse_client(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(
                return_value=Response(
                    200,
                    json={"valid": True, "countryCode": "FR", "vatNumber": "123"},
                )
            )
            await client.validate("FR12345678901")
            await client.validate("FR12345678902")
        await client.close()

    @pytest.mark.asyncio
    async def test_custom_timeout(self) -> None:
        client = VIESClient(timeout=5.0)
        assert client._timeout == 5.0
        await client.close()
