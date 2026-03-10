"""Tests for BZSt eVatR REST API client (new JSON endpoint)."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ustidnr_mcp.bzst_client import (
    BZStClient,
    _build_qualified_result,
    _build_validation_result,
    _map_bzst_status,
)
from ustidnr_mcp.errors import BZStConnectionError
from ustidnr_mcp.models import BZST_STATUS_MAP

# ---------------------------------------------------------------------------
# _map_bzst_status
# ---------------------------------------------------------------------------


class TestMapBzstStatus:
    def test_valid_status(self) -> None:
        code, valid, desc = _map_bzst_status("evatr-0000")
        assert code == "200"
        assert valid is True
        assert "gültig" in desc

    def test_not_registered(self) -> None:
        code, valid, _desc = _map_bzst_status("evatr-2001")
        assert code == "202"
        assert valid is False

    def test_own_vat_invalid(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-2005")
        assert code == "204"
        assert valid is False

    def test_rate_limited(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-0008")
        assert code == "207"
        assert valid is False

    def test_service_unavailable(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-0011")
        assert code == "203"
        assert valid is False

    def test_unknown_status(self) -> None:
        code, valid, desc = _map_bzst_status("evatr-9999")
        assert code == "216"
        assert valid is False
        assert "Unbekannter" in desc

    def test_empty_status(self) -> None:
        code, valid, _ = _map_bzst_status("")
        assert code == "216"
        assert valid is False

    @pytest.mark.parametrize("status", sorted(BZST_STATUS_MAP.keys()))
    def test_all_mapped_statuses(self, status: str) -> None:
        """Every mapped status returns a valid internal code."""
        code, valid, desc = _map_bzst_status(status)
        assert isinstance(code, str)
        assert isinstance(valid, bool)
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_valid_with_special_circumstances(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-2008")
        assert code == "200"
        assert valid is True

    def test_format_error_queried(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-0005")
        assert code == "201"
        assert valid is False

    def test_format_error_own(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-0004")
        assert code == "220"
        assert valid is False

    def test_not_eu_member(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-2003")
        assert code == "206"
        assert valid is False

    def test_qualified_not_possible(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-0003")
        assert code == "212"
        assert valid is False

    def test_processing_errors(self) -> None:
        """All processing error codes map to 208."""
        for status in [
            "evatr-1002",
            "evatr-1003",
            "evatr-1004",
            "evatr-2004",
            "evatr-2007",
            "evatr-2011",
            "evatr-3011",
        ]:
            code, valid, _ = _map_bzst_status(status)
            assert code == "208", f"{status} should map to 208"
            assert valid is False

    def test_service_unavailable_variants(self) -> None:
        """Multiple codes map to service unavailable."""
        for status in ["evatr-0011", "evatr-0013"]:
            code, _, _ = _map_bzst_status(status)
            assert code == "203"

    def test_temp_unavailable(self) -> None:
        code, _, _ = _map_bzst_status("evatr-1001")
        assert code == "217"

    def test_future_valid_date(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-2002")
        assert code == "209"
        assert valid is False

    def test_past_valid_period(self) -> None:
        code, valid, _ = _map_bzst_status("evatr-2006")
        assert code == "202"
        assert valid is False


# ---------------------------------------------------------------------------
# _build_validation_result
# ---------------------------------------------------------------------------


class TestBuildValidationResult:
    def test_valid_result(self) -> None:
        data = {
            "status": "evatr-0000",
            "angefragteUstid": "FR12345678901",
            "firmenname": "Acme SARL",
            "strasse": "Rue de Rivoli 1",
            "anfrageZeitpunkt": "2026-03-10T12:00:00",
            "message": "Die angefragte USt-IdNr. ist gültig.",
        }
        result = _build_validation_result("FR12345678901", data)
        assert result.valid is True
        assert result.error_code == "200"
        assert result.company_name == "Acme SARL"
        assert result.vat_id == "FR12345678901"
        assert result.country_code == "FR"

    def test_invalid_result(self) -> None:
        data = {
            "status": "evatr-2001",
            "anfrageZeitpunkt": "2026-03-10T12:00:00",
            "message": "Die angefragte USt-IdNr. ist ungültig.",
        }
        result = _build_validation_result("FR00000000000", data)
        assert result.valid is False
        assert result.error_code == "202"

    def test_unknown_status(self) -> None:
        data = {"status": "evatr-9999", "anfrageZeitpunkt": ""}
        result = _build_validation_result("FR12345678901", data)
        assert result.valid is False
        assert "Unbekannter" in result.error_description

    def test_missing_status(self) -> None:
        data = {"anfrageZeitpunkt": "2026-03-10"}
        result = _build_validation_result("FR12345678901", data)
        assert result.valid is False

    def test_none_company_name(self) -> None:
        data = {"status": "evatr-0000", "firmenname": None}
        result = _build_validation_result("FR12345678901", data)
        assert result.company_name == ""

    def test_empty_company_name(self) -> None:
        data = {"status": "evatr-0000", "firmenname": ""}
        result = _build_validation_result("FR12345678901", data)
        assert result.company_name == ""

    def test_api_message_used(self) -> None:
        data = {
            "status": "evatr-0000",
            "message": "Custom API message",
        }
        result = _build_validation_result("FR12345678901", data)
        assert result.error_description == "Custom API message"

    def test_empty_vat_id(self) -> None:
        data = {"status": "evatr-0000"}
        result = _build_validation_result("", data)
        assert result.country_code == ""

    def test_short_vat_id(self) -> None:
        data = {"status": "evatr-0000"}
        result = _build_validation_result("D", data)
        # "D" has len < 2, but slicing still works
        assert result.country_code == ""

    def test_unicode_company_name(self) -> None:
        data = {
            "status": "evatr-0000",
            "firmenname": "Müller & Söhne GmbH",
            "strasse": "Königstraße 42",
        }
        result = _build_validation_result("DE123456789", data)
        assert result.company_name == "Müller & Söhne GmbH"
        assert result.company_address == "Königstraße 42"

    def test_raw_response_preserved(self) -> None:
        data = {"status": "evatr-0000", "id": "abc-123", "extra": "field"}
        result = _build_validation_result("DE123456789", data)
        assert result.raw_response == data


# ---------------------------------------------------------------------------
# _build_qualified_result
# ---------------------------------------------------------------------------


class TestBuildQualifiedResult:
    def test_all_match(self) -> None:
        data = {
            "status": "evatr-0000",
            "ergFirmenname": "A",
            "ergOrt": "A",
            "ergPlz": "A",
            "ergStrasse": "A",
            "anfrageZeitpunkt": "2026-03-10T12:00:00",
        }
        result = _build_qualified_result("DE123456789", "FR12345678901", data)
        assert result.valid is True
        assert result.company_name_match == "A"
        assert result.city_match == "A"
        assert result.zip_match == "A"
        assert result.street_match == "A"
        assert result.all_fields_match is True

    def test_partial_match(self) -> None:
        data = {
            "status": "evatr-0000",
            "ergFirmenname": "A",
            "ergOrt": "A",
            "ergPlz": "B",
            "ergStrasse": "D",
        }
        result = _build_qualified_result("DE123456789", "FR12345678901", data)
        assert result.valid is True
        assert result.all_fields_match is False

    def test_not_requested_fields(self) -> None:
        data = {
            "status": "evatr-0000",
            "ergFirmenname": "A",
            "ergOrt": "C",
            "ergPlz": "C",
            "ergStrasse": "C",
        }
        result = _build_qualified_result("DE123456789", "FR12345678901", data)
        assert result.valid is True
        assert result.all_fields_match is True

    def test_all_no_match(self) -> None:
        data = {
            "status": "evatr-0000",
            "ergFirmenname": "B",
            "ergOrt": "B",
            "ergPlz": "B",
            "ergStrasse": "B",
        }
        result = _build_qualified_result("DE123456789", "FR12345678901", data)
        assert result.all_fields_match is False

    def test_all_not_available(self) -> None:
        data = {
            "status": "evatr-0000",
            "ergFirmenname": "D",
            "ergOrt": "D",
            "ergPlz": "D",
            "ergStrasse": "D",
        }
        result = _build_qualified_result("DE123456789", "FR12345678901", data)
        # D fields are not A, so all_fields_match should be False
        assert result.all_fields_match is False

    def test_missing_match_fields(self) -> None:
        data = {"status": "evatr-0000"}
        result = _build_qualified_result("DE123456789", "FR12345678901", data)
        assert result.company_name_match == ""
        assert result.city_match == ""

    def test_none_match_fields(self) -> None:
        data = {
            "status": "evatr-0000",
            "ergFirmenname": None,
            "ergOrt": None,
        }
        result = _build_qualified_result("DE123456789", "FR12345678901", data)
        assert result.company_name_match == ""
        assert result.city_match == ""


# ---------------------------------------------------------------------------
# BZStClient — simple validation
# ---------------------------------------------------------------------------


class TestBZStClientSimple:
    @pytest.mark.asyncio
    async def test_validate_simple_success(self) -> None:
        json_response = {
            "status": "evatr-0000",
            "anfragendeUstid": "DE123456789",
            "angefragteUstid": "FR12345678901",
            "anfrageZeitpunkt": "2026-03-10T12:00:00",
            "firmenname": "Acme SARL",
            "message": "Die angefragte USt-IdNr. ist gültig.",
        }

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            result = await client.validate_simple("DE123456789", "FR12345678901")

        assert result.valid is True
        assert result.error_code == "200"
        assert result.company_name == "Acme SARL"
        await client.close()

    @pytest.mark.asyncio
    async def test_validate_simple_invalid(self) -> None:
        json_response = {
            "status": "evatr-2001",
            "angefragteUstid": "FR00000000000",
            "anfrageZeitpunkt": "2026-03-10T12:00:00",
            "message": "Die angefragte USt-IdNr. ist nicht vergeben.",
        }

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            result = await client.validate_simple("DE123456789", "FR00000000000")

        assert result.valid is False
        assert result.error_code == "202"
        await client.close()

    @pytest.mark.asyncio
    async def test_timeout_raises_connection_error(self) -> None:
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
    async def test_http_error_with_json_body(self) -> None:
        """HTTP errors with JSON body are parsed (API returns error info)."""
        error_response = {
            "status": "evatr-0004",
            "message": "Requesting VAT ID has invalid syntax.",
        }
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(400, json=error_response)
            )
            result = await client.validate_simple("DE000", "FR12345678901")

        assert result.valid is False
        assert result.error_code == "220"
        await client.close()

    @pytest.mark.asyncio
    async def test_http_error_without_json_body(self) -> None:
        """HTTP errors without parseable JSON raise BZStConnectionError."""
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(500, text="Internal Server Error")
            )
            with pytest.raises(BZStConnectionError):
                await client.validate_simple("DE123456789", "FR12345678901")
        await client.close()

    @pytest.mark.asyncio
    async def test_connection_error(self) -> None:
        import httpx

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                side_effect=httpx.ConnectError("DNS failure")
            )
            with pytest.raises(BZStConnectionError):
                await client.validate_simple("DE123456789", "FR12345678901")
        await client.close()

    @pytest.mark.asyncio
    async def test_ssl_error(self) -> None:
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                side_effect=Exception("SSL certificate verify failed")
            )
            with pytest.raises(BZStConnectionError):
                await client.validate_simple("DE123456789", "FR12345678901")
        await client.close()

    @pytest.mark.asyncio
    async def test_service_unavailable(self) -> None:
        json_response = {
            "status": "evatr-0011",
            "message": "Service temporarily unavailable.",
        }
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            result = await client.validate_simple("DE123456789", "FR12345678901")

        assert result.valid is False
        assert result.error_code == "203"
        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limited(self) -> None:
        json_response = {
            "status": "evatr-0008",
            "message": "Maximum qualified confirmations reached.",
        }
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            result = await client.validate_simple("DE123456789", "FR12345678901")

        assert result.valid is False
        assert result.error_code == "207"
        await client.close()

    @pytest.mark.asyncio
    async def test_unicode_company_name(self) -> None:
        json_response = {
            "status": "evatr-0000",
            "firmenname": "Müller & Söhne GmbH",
            "strasse": "Königstraße 42",
        }
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            result = await client.validate_simple("DE123456789", "ATU12345678")

        assert result.company_name == "Müller & Söhne GmbH"
        assert result.company_address == "Königstraße 42"
        await client.close()


# ---------------------------------------------------------------------------
# BZStClient — qualified confirmation
# ---------------------------------------------------------------------------


class TestBZStClientQualified:
    @pytest.mark.asyncio
    async def test_qualified_all_match(self) -> None:
        json_response = {
            "status": "evatr-0000",
            "ergFirmenname": "A",
            "ergOrt": "A",
            "ergPlz": "A",
            "ergStrasse": "A",
            "anfrageZeitpunkt": "2026-03-10T12:00:00",
        }

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            result = await client.validate_qualified(
                own_vat_id="DE123456789",
                partner_vat_id="FR12345678901",
                company_name="Acme SARL",
                city="Paris",
                zip_code="75001",
                street="Rue de Rivoli 1",
            )

        assert result.valid is True
        assert result.company_name_match == "A"
        assert result.city_match == "A"
        assert result.zip_match == "A"
        assert result.street_match == "A"
        assert result.all_fields_match is True
        await client.close()

    @pytest.mark.asyncio
    async def test_qualified_partial_match(self) -> None:
        json_response = {
            "status": "evatr-0000",
            "ergFirmenname": "A",
            "ergOrt": "A",
            "ergPlz": "A",
            "ergStrasse": "B",
        }

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            result = await client.validate_qualified(
                own_vat_id="DE123456789",
                partner_vat_id="FR12345678901",
                company_name="Acme SARL",
                city="Paris",
            )

        assert result.all_fields_match is False
        assert result.street_match == "B"
        await client.close()

    @pytest.mark.asyncio
    async def test_qualified_sends_correct_payload(self) -> None:
        json_response = {"status": "evatr-0000"}

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            route = respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            await client.validate_qualified(
                own_vat_id="DE123456789",
                partner_vat_id="FR12345678901",
                company_name="Acme",
                city="Paris",
                zip_code="75001",
                street="Rue",
            )
            assert route.called
            request = route.calls[0].request
            import json

            body = json.loads(request.content)
            assert body["anfragendeUstid"] == "DE123456789"
            assert body["angefragteUstid"] == "FR12345678901"
            assert body["firmenname"] == "Acme"
            assert body["ort"] == "Paris"
            assert body["plz"] == "75001"
            assert body["strasse"] == "Rue"
        await client.close()

    @pytest.mark.asyncio
    async def test_qualified_optional_fields_omitted(self) -> None:
        """zip_code and street are not sent if empty."""
        json_response = {"status": "evatr-0000"}

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            route = respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            await client.validate_qualified(
                own_vat_id="DE123456789",
                partner_vat_id="FR12345678901",
                company_name="Acme",
                city="Paris",
            )
            import json

            body = json.loads(route.calls[0].request.content)
            assert "plz" not in body
            assert "strasse" not in body
        await client.close()

    @pytest.mark.asyncio
    async def test_qualified_timeout(self) -> None:
        import httpx

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                side_effect=httpx.TimeoutException("timeout")
            )
            with pytest.raises(BZStConnectionError):
                await client.validate_qualified(
                    own_vat_id="DE123456789",
                    partner_vat_id="FR12345678901",
                    company_name="Acme",
                    city="Paris",
                )
        await client.close()


# ---------------------------------------------------------------------------
# BZStClient — lifecycle
# ---------------------------------------------------------------------------


class TestBZStClientLifecycle:
    @pytest.mark.asyncio
    async def test_close_no_client(self) -> None:
        client = BZStClient()
        await client.close()

    @pytest.mark.asyncio
    async def test_reuse_client(self) -> None:
        json_response = {"status": "evatr-0000"}

        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=json_response)
            )
            await client.validate_simple("DE123456789", "FR12345678901")
            await client.validate_simple("DE123456789", "IT12345678901")
        await client.close()

    @pytest.mark.asyncio
    async def test_custom_timeout(self) -> None:
        client = BZStClient(timeout=5.0)
        assert client._timeout == 5.0
        await client.close()

    @pytest.mark.asyncio
    async def test_custom_base_url(self) -> None:
        client = BZStClient(base_url="https://custom.example.com/api")
        assert client._base_url == "https://custom.example.com/api"
        await client.close()
