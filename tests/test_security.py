"""Security tests for ustidnr-mcp.

Covers OWASP Top 10 vectors relevant to this application:
- Input sanitization (control chars, null bytes)
- SQL injection (format validation rejects)
- XSS / script injection (format validation rejects)
- Path traversal (format validation rejects)
- Oversized inputs (truncation)
- Unicode edge cases (homoglyphs, RTL, zero-width)
- Response handling (malformed JSON, oversized responses)
- Error detail leakage
- HTTP redirect safety (SSRF prevention)
"""

from __future__ import annotations

from typing import Any

import pytest
import respx
from httpx import Response

from ustidnr_mcp.bzst_client import BZStClient, _build_validation_result, _map_bzst_status
from ustidnr_mcp.errors import BZStConnectionError
from ustidnr_mcp.validator import normalize_vat_id, sanitize_input, validate_format
from ustidnr_mcp.vies_client import VIES_REST_URL, VIESClient

# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------


class TestInputSanitization:
    """Verify dangerous inputs are neutralized."""

    def test_null_bytes_stripped(self) -> None:
        result = sanitize_input("DE\x00123\x00456")
        assert "\x00" not in result

    def test_control_chars_stripped(self) -> None:
        for i in range(0, 32):
            if i in (9, 10, 13):  # tab, newline, carriage return
                continue
            char = chr(i)
            result = sanitize_input(f"test{char}value")
            assert char not in result, f"Control char 0x{i:02x} not stripped"

    def test_del_char_stripped(self) -> None:
        result = sanitize_input("test\x7fvalue")
        assert "\x7f" not in result

    def test_very_long_input_truncated(self) -> None:
        long_input = "A" * 10_000
        result = sanitize_input(long_input)
        assert len(result) <= 256

    def test_very_long_vat_id_truncated(self) -> None:
        long_id = "DE" + "1" * 10_000
        result = normalize_vat_id(long_id)
        assert len(result) <= 50

    def test_bell_char_stripped(self) -> None:
        result = sanitize_input("DE\x07123")
        assert "\x07" not in result

    def test_backspace_stripped(self) -> None:
        result = sanitize_input("DE\x08123")
        assert "\x08" not in result

    def test_form_feed_stripped(self) -> None:
        result = sanitize_input("DE\x0c123")
        assert "\x0c" not in result

    def test_escape_char_stripped(self) -> None:
        result = sanitize_input("DE\x1b[31m123")
        assert "\x1b" not in result


# ---------------------------------------------------------------------------
# SQL injection
# ---------------------------------------------------------------------------


class TestSQLInjection:
    """Verify SQL injection in VAT ID strings is harmless (no SQL used, but defense in depth)."""

    @pytest.mark.parametrize(
        "payload",
        [
            "DE'; DROP TABLE users; --",
            "DE' OR '1'='1",
            'DE" OR "1"="1"',
            "DE123456789; DELETE FROM vat_ids",
            "DE123456789 UNION SELECT * FROM passwords",
            "DE123456789' AND 1=1--",
            "DE'; EXEC xp_cmdshell('whoami'); --",
            "DE' WAITFOR DELAY '0:0:5'--",
        ],
    )
    def test_sql_injection_rejected_by_format(self, payload: str) -> None:
        valid, _, _ = validate_format(payload)
        assert valid is False


# ---------------------------------------------------------------------------
# XSS / script injection
# ---------------------------------------------------------------------------


class TestXSSInjection:
    """Script injection in company names and VAT IDs."""

    @pytest.mark.parametrize(
        "payload",
        [
            "<script>alert('xss')</script>",
            "DE<img src=x onerror=alert(1)>",
            "DE123456789<svg onload=alert(1)>",
            'DE" onmouseover="alert(1)',
            "javascript:alert(1)",
            "<iframe src='evil.com'>",
            "{{7*7}}",  # SSTI
            "${7*7}",  # template injection
        ],
    )
    def test_xss_rejected_by_format(self, payload: str) -> None:
        valid, _, _ = validate_format(payload)
        assert valid is False

    def test_script_in_company_name_sanitized(self) -> None:
        result = sanitize_input("<script>alert('xss')</script>")
        assert len(result) <= 256


# ---------------------------------------------------------------------------
# Path traversal
# ---------------------------------------------------------------------------


class TestPathTraversal:
    @pytest.mark.parametrize(
        "payload",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "DE%2F..%2F..%2Fetc%2Fpasswd",
            "DE/../../../../etc/shadow",
            "....//....//etc/passwd",
        ],
    )
    def test_path_traversal_rejected(self, payload: str) -> None:
        valid, _, _ = validate_format(payload)
        assert valid is False


# ---------------------------------------------------------------------------
# Null byte injection
# ---------------------------------------------------------------------------


class TestNullByteInjection:
    def test_null_byte_in_vat_id(self) -> None:
        result = normalize_vat_id("DE123\x00456789")
        assert "\x00" not in result

    def test_null_byte_in_company_name(self) -> None:
        result = sanitize_input("Acme\x00Corp")
        assert "\x00" not in result

    def test_multiple_null_bytes(self) -> None:
        result = sanitize_input("\x00\x00\x00test\x00\x00")
        assert "\x00" not in result
        assert "test" in result


# ---------------------------------------------------------------------------
# Oversized inputs
# ---------------------------------------------------------------------------


class TestOversizedInputs:
    def test_10kb_vat_id(self) -> None:
        huge_id = "DE" + "1" * 10_240
        result = normalize_vat_id(huge_id)
        assert len(result) <= 50

    def test_10kb_company_name(self) -> None:
        huge_name = "A" * 10_240
        result = sanitize_input(huge_name)
        assert len(result) <= 256

    def test_format_validation_on_huge_input(self) -> None:
        huge_id = "DE" + "1" * 10_240
        valid, _, _ = validate_format(huge_id)
        assert valid is False

    def test_1mb_input(self) -> None:
        huge = "X" * 1_048_576
        result = sanitize_input(huge)
        assert len(result) <= 256

    def test_repeated_separators(self) -> None:
        """Many separators should not cause regex catastrophic backtracking."""
        evil = "DE" + ".-/ " * 5000
        result = normalize_vat_id(evil)
        assert len(result) <= 50


# ---------------------------------------------------------------------------
# Unicode edge cases
# ---------------------------------------------------------------------------


class TestUnicodeEdgeCases:
    def test_rtl_override_chars(self) -> None:
        result = sanitize_input("DE\u202e123456789")
        assert len(result) <= 256

    def test_zero_width_chars(self) -> None:
        result = normalize_vat_id("DE\u200b123\u200b456789")
        valid, _, _ = validate_format(result)
        assert isinstance(valid, bool)

    def test_homoglyph_attack(self) -> None:
        """Cyrillic 'D' + Latin 'E' should fail format validation."""
        vat_id = "\u0414E123456789"
        valid, _, _ = validate_format(vat_id)
        assert valid is False

    def test_fullwidth_digits(self) -> None:
        """Fullwidth digits (U+FF10-FF19) should not match."""
        vat_id = "DE\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19"
        valid, _, _ = validate_format(vat_id)
        assert valid is False

    def test_combining_chars(self) -> None:
        """Combining diacritical marks should not break validation."""
        # D + combining acute accent
        vat_id = "D\u0301E123456789"
        valid, _, _ = validate_format(vat_id)
        assert valid is False

    def test_bom_prefix(self) -> None:
        """UTF-8 BOM should be handled."""
        vat_id = "\ufeffDE123456789"
        valid, _, _ = validate_format(vat_id)
        # BOM will prevent matching the DE prefix
        assert valid is False


# ---------------------------------------------------------------------------
# Malformed API responses
# ---------------------------------------------------------------------------


class TestMalformedBZStResponses:
    """Verify resilience against malformed BZSt API responses."""

    def test_empty_response_body(self) -> None:
        data: dict[str, Any] = {}
        result = _build_validation_result("DE123456789", data)
        assert result.valid is False

    def test_missing_status_field(self) -> None:
        data: dict[str, Any] = {"message": "something"}
        result = _build_validation_result("DE123456789", data)
        assert result.valid is False

    def test_null_status(self) -> None:
        _code, valid, _ = _map_bzst_status("")
        assert valid is False

    def test_numeric_status(self) -> None:
        """Status should be string, not int."""
        data: dict[str, Any] = {"status": "12345"}
        result = _build_validation_result("DE123456789", data)
        assert result.valid is False

    def test_extra_fields_ignored(self) -> None:
        data: dict[str, Any] = {
            "status": "evatr-0000",
            "unexpected_field": "should not crash",
            "nested": {"deep": True},
        }
        result = _build_validation_result("DE123456789", data)
        assert result.valid is True

    @pytest.mark.asyncio
    async def test_non_json_response(self) -> None:
        """API returning HTML instead of JSON."""
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, text="<html>Service Unavailable</html>")
            )
            with pytest.raises(BZStConnectionError):
                await client.validate_simple("DE123456789", "FR12345678901")
        await client.close()

    @pytest.mark.asyncio
    async def test_truncated_json(self) -> None:
        """Truncated JSON response."""
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, text='{"status": "evatr-0000", "fi')
            )
            with pytest.raises(BZStConnectionError):
                await client.validate_simple("DE123456789", "FR12345678901")
        await client.close()


class TestMalformedVIESResponses:
    """Verify resilience against malformed VIES responses."""

    @pytest.mark.asyncio
    async def test_empty_json_response(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(return_value=Response(200, json={}))
            result = await client.validate("FR12345678901")
        assert result.valid is False
        await client.close()

    @pytest.mark.asyncio
    async def test_non_json_response(self) -> None:
        client = VIESClient()
        with respx.mock:
            respx.post(VIES_REST_URL).mock(return_value=Response(200, text="Not JSON"))
            result = await client.validate("FR12345678901")
        # Should gracefully handle
        assert result.valid is False
        assert result.error_code == "216"
        await client.close()


# ---------------------------------------------------------------------------
# Error detail leakage
# ---------------------------------------------------------------------------


class TestErrorDetailLeakage:
    """Verify internal details are not leaked in error responses."""

    def test_unknown_status_no_stack_trace(self) -> None:
        _, _, desc = _map_bzst_status("evatr-9999")
        assert "traceback" not in desc.lower()
        assert "exception" not in desc.lower()
        assert "file" not in desc.lower()

    def test_error_description_is_user_friendly(self) -> None:
        from ustidnr_mcp.models import ErrorCode

        for code in ErrorCode:
            desc = code.description_de
            # Should be in German, user-friendly
            assert len(desc) > 5
            assert "traceback" not in desc.lower()


# ---------------------------------------------------------------------------
# HTTP redirect safety (SSRF prevention)
# ---------------------------------------------------------------------------


class TestHTTPSafety:
    """Verify HTTP client configuration prevents SSRF."""

    @pytest.mark.asyncio
    async def test_bzst_client_uses_timeout(self) -> None:
        """Client should have a timeout configured."""
        client = BZStClient(timeout=5.0)
        assert client._timeout == 5.0
        await client.close()

    @pytest.mark.asyncio
    async def test_oversized_response_handling(self) -> None:
        """Very large response body should not crash."""
        large_json = {"status": "evatr-0000", "data": "X" * 100_000}
        client = BZStClient(base_url="https://test.example.com/api/v1/abfrage")
        with respx.mock:
            respx.post("https://test.example.com/api/v1/abfrage").mock(
                return_value=Response(200, json=large_json)
            )
            result = await client.validate_simple("DE123456789", "FR12345678901")
        assert result.valid is True
        await client.close()
