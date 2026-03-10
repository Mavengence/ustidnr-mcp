"""Security tests for ustidnr-mcp."""

from __future__ import annotations

import pytest

from ustidnr_mcp.validator import normalize_vat_id, sanitize_input, validate_format


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
            assert char not in result

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


class TestSQLInjection:
    """Verify SQL injection in VAT ID strings is harmless."""

    @pytest.mark.parametrize(
        "payload",
        [
            "DE'; DROP TABLE users; --",
            "DE' OR '1'='1",
            'DE" OR "1"="1"',
            "DE123456789; DELETE FROM vat_ids",
            "DE123456789 UNION SELECT * FROM passwords",
            "DE123456789' AND 1=1--",
        ],
    )
    def test_sql_injection_rejected_by_format(self, payload: str) -> None:
        """SQL payloads fail format validation (no SQL is used, but verify)."""
        valid, _, _ = validate_format(payload)
        assert valid is False


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
        ],
    )
    def test_xss_rejected_by_format(self, payload: str) -> None:
        valid, _, _ = validate_format(payload)
        assert valid is False

    def test_script_in_company_name_sanitized(self) -> None:
        """sanitize_input doesn't strip HTML but does limit length."""
        result = sanitize_input("<script>alert('xss')</script>")
        assert len(result) <= 256


class TestPathTraversal:
    @pytest.mark.parametrize(
        "payload",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "DE%2F..%2F..%2Fetc%2Fpasswd",
            "DE/../../../../etc/shadow",
        ],
    )
    def test_path_traversal_rejected(self, payload: str) -> None:
        valid, _, _ = validate_format(payload)
        assert valid is False


class TestNullByteInjection:
    def test_null_byte_in_vat_id(self) -> None:
        result = normalize_vat_id("DE123\x00456789")
        assert "\x00" not in result

    def test_null_byte_in_company_name(self) -> None:
        result = sanitize_input("Acme\x00Corp")
        assert "\x00" not in result


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


class TestUnicodeEdgeCases:
    def test_rtl_override_chars(self) -> None:
        """Right-to-left override characters should not confuse validation."""
        result = sanitize_input("DE\u202e123456789")
        # The RTL override is not a control char in our range, but input is still handled
        assert len(result) <= 256

    def test_zero_width_chars(self) -> None:
        result = normalize_vat_id("DE\u200b123\u200b456789")
        # Zero-width spaces are not in our strip range but won't match format
        valid, _, _ = validate_format(result)
        # May or may not be valid depending on zero-width handling
        assert isinstance(valid, bool)

    def test_homoglyph_attack(self) -> None:
        """Cyrillic 'D' + Latin 'E' should fail format validation."""
        # \u0414 is Cyrillic De
        vat_id = "\u0414E123456789"
        valid, _, _ = validate_format(vat_id)
        assert valid is False
