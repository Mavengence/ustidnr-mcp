"""BZSt eVatR REST API client for USt-IdNr validation.

Uses the new REST API (July 2025) at https://api.evatr.vies.bzst.de/app/v1/abfrage.
The old XML-RPC endpoint was sunset November 2025.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ustidnr_mcp.config import settings
from ustidnr_mcp.errors import BZStConnectionError
from ustidnr_mcp.models import (
    BZST_STATUS_MAP,
    ErrorCode,
    QualifiedConfirmationResult,
    ValidationResult,
)

logger = logging.getLogger(__name__)


def _map_bzst_status(status: str) -> tuple[str, bool, str]:
    """Map a BZSt evatr-XXXX status code to internal (error_code, is_valid, description).

    Returns:
        Tuple of (internal_error_code, is_valid, german_description).
    """
    mapped = BZST_STATUS_MAP.get(status)
    if mapped is not None:
        internal_code, is_valid = mapped
        try:
            error_enum = ErrorCode(internal_code)
            description = error_enum.description_de
        except ValueError:
            description = f"Unbekannter Fehlercode: {internal_code}"
        return internal_code, is_valid, description

    # Unknown status code
    return "216", False, f"Unbekannter BZSt-Status: {status}"


def _build_validation_result(vat_id: str, data: dict[str, Any]) -> ValidationResult:
    """Build a ValidationResult from parsed BZSt JSON response."""
    status = data.get("status", "")
    error_code, valid, description = _map_bzst_status(status)

    # Use message from API if available, fall back to our description
    api_message = data.get("message", "")
    if api_message:
        description = api_message

    return ValidationResult(
        vat_id=vat_id,
        valid=valid,
        error_code=error_code,
        error_description=description,
        country_code=vat_id[:2] if len(vat_id) >= 2 else "",
        company_name=str(data.get("firmenname", "") or ""),
        company_address=str(data.get("strasse", "") or ""),
        request_date=str(data.get("anfrageZeitpunkt", "") or ""),
        raw_response=data,
    )


def _build_qualified_result(
    own_vat_id: str, partner_vat_id: str, data: dict[str, Any]
) -> QualifiedConfirmationResult:
    """Build a QualifiedConfirmationResult from parsed BZSt JSON response."""
    status = data.get("status", "")
    error_code, valid, description = _map_bzst_status(status)

    api_message = data.get("message", "")
    if api_message:
        description = api_message

    return QualifiedConfirmationResult(
        own_vat_id=own_vat_id,
        partner_vat_id=partner_vat_id,
        valid=valid,
        error_code=error_code,
        error_description=description,
        company_name_match=str(data.get("ergFirmenname", "") or ""),
        city_match=str(data.get("ergOrt", "") or ""),
        zip_match=str(data.get("ergPlz", "") or ""),
        street_match=str(data.get("ergStrasse", "") or ""),
        request_date=str(data.get("anfrageZeitpunkt", "") or ""),
        print_confirmation="",
        raw_response=data,
    )


class BZStClient:
    """HTTP client for BZSt eVatR REST API (new endpoint since July 2025)."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = base_url or settings.bzst_base_url
        self._timeout = timeout or settings.request_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def validate_simple(
        self,
        own_vat_id: str,
        partner_vat_id: str,
    ) -> ValidationResult:
        """Simple confirmation: checks if partner VAT ID is valid.

        Args:
            own_vat_id: Your German USt-IdNr (e.g., DE123456789).
            partner_vat_id: Partner's EU USt-IdNr to validate.

        Returns:
            ValidationResult with validity status and details.
        """
        payload: dict[str, str] = {
            "anfragendeUstid": own_vat_id,
            "angefragteUstid": partner_vat_id,
        }

        data = await self._request(payload)
        return _build_validation_result(partner_vat_id, data)

    async def validate_qualified(
        self,
        own_vat_id: str,
        partner_vat_id: str,
        company_name: str = "",
        city: str = "",
        zip_code: str = "",
        street: str = "",
    ) -> QualifiedConfirmationResult:
        """Qualified confirmation (qualifizierte Bestätigung).

        Validates partner VAT ID and matches name/address against official records.

        Args:
            own_vat_id: Your German USt-IdNr.
            partner_vat_id: Partner's EU USt-IdNr.
            company_name: Expected company name.
            city: Expected city.
            zip_code: Expected postal code.
            street: Expected street.

        Returns:
            QualifiedConfirmationResult with per-field match status.
        """
        payload: dict[str, str] = {
            "anfragendeUstid": own_vat_id,
            "angefragteUstid": partner_vat_id,
            "firmenname": company_name,
            "ort": city,
        }
        # Only include optional fields if provided
        if zip_code:
            payload["plz"] = zip_code
        if street:
            payload["strasse"] = street

        data = await self._request(payload)
        return _build_qualified_result(own_vat_id, partner_vat_id, data)

    async def _request(self, payload: dict[str, str]) -> dict[str, Any]:
        """Send POST request to BZSt eVatR REST API and parse JSON response."""
        client = await self._get_client()

        try:
            response = await client.post(
                self._base_url,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            response.raise_for_status()

            data: dict[str, Any] = response.json()
            return data
        except httpx.TimeoutException as e:
            logger.error("BZSt eVatR request timed out")
            raise BZStConnectionError("BZSt eVatR request timed out") from e
        except httpx.HTTPStatusError as e:
            logger.error("BZSt eVatR HTTP error: %s", e.response.status_code)
            # Try to extract error details from response body
            try:
                error_data: dict[str, Any] = e.response.json()
                return error_data
            except Exception:
                raise BZStConnectionError(f"BZSt eVatR HTTP error: {e.response.status_code}") from e
        except BZStConnectionError:
            raise
        except Exception as e:
            logger.exception("BZSt eVatR request failed")
            raise BZStConnectionError("BZSt eVatR request failed") from e
