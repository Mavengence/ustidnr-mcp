"""Tests for custom exception hierarchy."""

from __future__ import annotations

from ustidnr_mcp.errors import (
    BatchLimitError,
    BZStConnectionError,
    BZStValidationError,
    FormatValidationError,
    UstIdNrError,
    VIESConnectionError,
)


class TestExceptionHierarchy:
    def test_base_exception(self) -> None:
        err = UstIdNrError("test")
        assert str(err) == "test"
        assert isinstance(err, Exception)

    def test_bzst_connection_error_is_ustidnr_error(self) -> None:
        err = BZStConnectionError("timeout")
        assert isinstance(err, UstIdNrError)

    def test_bzst_validation_error(self) -> None:
        err = BZStValidationError("evatr-2001", "Not assigned")
        assert isinstance(err, UstIdNrError)
        assert err.status_code == "evatr-2001"
        assert err.message == "Not assigned"
        assert "evatr-2001" in str(err)

    def test_vies_connection_error(self) -> None:
        err = VIESConnectionError("timeout")
        assert isinstance(err, UstIdNrError)

    def test_format_validation_error(self) -> None:
        err = FormatValidationError("DE123", "too short")
        assert isinstance(err, UstIdNrError)
        assert err.vat_id == "DE123"
        assert err.reason == "too short"
        assert "DE123" in str(err)

    def test_batch_limit_error(self) -> None:
        err = BatchLimitError(150, 100)
        assert isinstance(err, UstIdNrError)
        assert err.requested == 150
        assert err.maximum == 100
        assert "150" in str(err)
        assert "100" in str(err)

    def test_all_catchable_by_base(self) -> None:
        errors = [
            BZStConnectionError("test"),
            BZStValidationError("code", "msg"),
            VIESConnectionError("test"),
            FormatValidationError("id", "reason"),
            BatchLimitError(1, 0),
        ]
        for err in errors:
            try:
                raise err
            except UstIdNrError:
                pass  # All should be caught
