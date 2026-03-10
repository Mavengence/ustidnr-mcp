"""EU VIES API client for non-German VAT ID validation (fallback)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ustidnr_mcp.config import settings
from ustidnr_mcp.models import ValidationResult

logger = logging.getLogger(__name__)

VIES_REST_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"


class VIESClient:
    """REST client for the EU VIES VAT validation service."""

    def __init__(self, timeout: float | None = None) -> None:
        self._timeout = timeout or settings.request_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def validate(self, vat_id: str) -> ValidationResult:
        """Validate a VAT ID via the VIES REST API.

        Args:
            vat_id: Full EU VAT ID (e.g., FR12345678901).

        Returns:
            ValidationResult with validity status.

        Raises:
            VIESConnectionError: On unrecoverable connection failures.
        """
        country_code = vat_id[:2]
        vat_number = vat_id[2:]

        client = await self._get_client()

        try:
            response = await client.post(
                VIES_REST_URL,
                json={
                    "countryCode": country_code,
                    "vatNumber": vat_number,
                },
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()

            valid = bool(data.get("valid", False))
            name = str(data.get("name", "") or "")
            address = str(data.get("address", "") or "")

            return ValidationResult(
                vat_id=vat_id,
                valid=valid,
                error_code="200" if valid else "202",
                error_description=(
                    "Die angefragte USt-IdNr. ist gültig."
                    if valid
                    else "Die angefragte USt-IdNr. ist ungültig (nicht vergeben)."
                ),
                country_code=country_code,
                company_name=name.strip() if name != "---" else "",
                company_address=address.strip() if address != "---" else "",
                request_date=str(data.get("requestDate", "") or ""),
                raw_response=data,
            )
        except httpx.TimeoutException:
            logger.error("VIES request timed out")
            return ValidationResult(
                vat_id=vat_id,
                valid=False,
                error_code="217",
                error_description="VIES-Dienst nicht erreichbar (Timeout).",
                country_code=country_code,
            )
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error("VIES HTTP error: %s", status_code)
            if status_code == 429:
                return ValidationResult(
                    vat_id=vat_id,
                    valid=False,
                    error_code="207",
                    error_description="VIES-Dienst: Zu viele Anfragen (Rate Limit).",
                    country_code=country_code,
                )
            return ValidationResult(
                vat_id=vat_id,
                valid=False,
                error_code="203",
                error_description="VIES-Dienst hat einen Fehler zurückgegeben.",
                country_code=country_code,
            )
        except Exception:
            logger.exception("VIES request failed")
            return ValidationResult(
                vat_id=vat_id,
                valid=False,
                error_code="216",
                error_description="Allgemeiner Fehler bei VIES-Anfrage.",
                country_code=country_code,
            )
