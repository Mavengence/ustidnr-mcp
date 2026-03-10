"""Custom exceptions for ustidnr-mcp."""

from __future__ import annotations


class UstIdNrError(Exception):
    """Base exception for all ustidnr-mcp errors."""


class BZStConnectionError(UstIdNrError):
    """Failed to connect to BZSt eVatR API."""


class BZStValidationError(UstIdNrError):
    """BZSt returned a validation error."""

    def __init__(self, status_code: str, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"BZSt error {status_code}: {message}")


class VIESConnectionError(UstIdNrError):
    """Failed to connect to EU VIES service."""


class FormatValidationError(UstIdNrError):
    """VAT ID format is invalid."""

    def __init__(self, vat_id: str, reason: str) -> None:
        self.vat_id = vat_id
        self.reason = reason
        super().__init__(f"Invalid VAT ID '{vat_id}': {reason}")


class BatchLimitError(UstIdNrError):
    """Batch size exceeds the configured limit."""

    def __init__(self, requested: int, maximum: int) -> None:
        self.requested = requested
        self.maximum = maximum
        super().__init__(f"Batch size {requested} exceeds limit of {maximum}")
