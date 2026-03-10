"""FastMCP server for USt-IdNr validation."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations

from ustidnr_mcp.bzst_client import BZStClient
from ustidnr_mcp.config import settings
from ustidnr_mcp.errors import BatchLimitError, BZStConnectionError
from ustidnr_mcp.models import BatchValidationResult, ValidationResult
from ustidnr_mcp.prompts import register_prompts
from ustidnr_mcp.resources import register_resources
from ustidnr_mcp.validator import normalize_vat_id, sanitize_input, validate_format
from ustidnr_mcp.vies_client import VIESClient

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Initialize and clean up API clients."""
    bzst = BZStClient()
    vies = VIESClient()
    logger.info(
        "ustidnr-mcp ready: 3 tools, %d resources, %d prompts",
        len(mcp._resource_manager._resources),
        len(mcp._prompt_manager._prompts),
    )
    try:
        yield {"bzst": bzst, "vies": vies}
    finally:
        await bzst.close()
        await vies.close()


mcp = FastMCP(
    "ustidnr-mcp",
    instructions=(
        "MCP-Server für EU USt-IdNr-Validierung über die BZSt eVatR-Schnittstelle. "
        "Ermöglicht einfache Prüfung, Batch-Validierung und qualifizierte Bestätigung "
        "gemäß §6a UStG für innergemeinschaftliche Lieferungen."
    ),
    lifespan=app_lifespan,
    host=settings.mcp_host,
    port=settings.mcp_port,
)

# Register prompts and resources
register_prompts(mcp)
register_resources(mcp)


# --- Tools ---


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def validate_ustidnr(vat_id: str, ctx: Context) -> str:
    """Validiert eine EU USt-IdNr (Format + BZSt/VIES-Prüfung).

    Prüft zunächst das Format, dann die Gültigkeit über die BZSt eVatR-
    oder VIES-Schnittstelle. Für deutsche USt-IdNr wird zusätzlich die
    Prüfziffer validiert.

    Args:
        vat_id: Die zu prüfende USt-IdNr (z.B. DE123456789, FR12345678901).
    """
    normalized = normalize_vat_id(vat_id)

    # Step 1: Format validation
    format_valid, country_code, format_error = validate_format(normalized)
    if not format_valid:
        result = ValidationResult(
            vat_id=normalized or vat_id,
            valid=False,
            error_code="201",
            error_description=format_error,
            country_code=country_code,
        )
        return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)

    # Step 2: API validation
    lifespan_ctx = ctx.request_context.lifespan_context
    vies: VIESClient = lifespan_ctx["vies"]

    # Both German and non-German IDs go via VIES for single validation.
    # BZSt requires a *different* German own USt-IdNr, which we don't have here.
    # For BZSt validation, use the qualified_confirmation tool instead.
    result = await vies.validate(normalized)

    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def validate_batch(vat_ids: list[str], ctx: Context) -> str:
    """Batch-Validierung mehrerer EU USt-IdNr (bis zu 100).

    Validiert alle übergebenen USt-IdNr parallel und gibt eine
    Zusammenfassung mit Einzelergebnissen zurück.

    Args:
        vat_ids: Liste der zu prüfenden USt-IdNr (max. 100).
    """
    if len(vat_ids) > settings.batch_max_size:
        raise BatchLimitError(requested=len(vat_ids), maximum=settings.batch_max_size)

    if not vat_ids:
        return json.dumps(
            {"error": "Keine USt-IdNr übergeben."},
            ensure_ascii=False,
            indent=2,
        )

    lifespan_ctx = ctx.request_context.lifespan_context
    vies: VIESClient = lifespan_ctx["vies"]

    semaphore = asyncio.Semaphore(settings.batch_concurrency)

    async def _validate_one(vid: str) -> ValidationResult:
        normalized = normalize_vat_id(vid)
        format_valid, country_code, format_error = validate_format(normalized)
        if not format_valid:
            return ValidationResult(
                vat_id=normalized or vid,
                valid=False,
                error_code="201",
                error_description=format_error,
                country_code=country_code,
            )
        async with semaphore:
            return await vies.validate(normalized)

    results = await asyncio.gather(*[_validate_one(v) for v in vat_ids])

    valid_count = sum(1 for r in results if r.valid)
    invalid_count = sum(1 for r in results if not r.valid and r.error_code in ("201", "202"))
    error_count = len(results) - valid_count - invalid_count

    batch_result = BatchValidationResult(
        results=list(results),
        total=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
        error_count=error_count,
    )

    return json.dumps(batch_result.model_dump(), ensure_ascii=False, indent=2)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    )
)
async def qualified_confirmation(
    own_vat_id: str,
    partner_vat_id: str,
    company_name: str,
    city: str,
    zip_code: str,
    street: str,
    ctx: Context = None,  # type: ignore[assignment]
) -> str:
    """Qualifizierte Bestätigung nach §6a UStG (BZSt eVatR).

    Prüft die USt-IdNr des Geschäftspartners und vergleicht Name,
    Ort, PLZ und Straße mit den offiziellen Daten des Mitgliedstaats.

    Ergebniscodes pro Feld:
    - A = Übereinstimmung
    - B = Keine Übereinstimmung
    - C = Nicht angefragt
    - D = Vom Mitgliedstaat nicht unterstützt

    Args:
        own_vat_id: Eigene deutsche USt-IdNr (z.B. DE123456789).
        partner_vat_id: USt-IdNr des Geschäftspartners.
        company_name: Erwarteter Firmenname des Partners.
        city: Erwarteter Ort des Partners.
        zip_code: Erwartete PLZ des Partners.
        street: Erwartete Straße des Partners.
    """
    # Sanitize text inputs
    company_name = sanitize_input(company_name)
    city = sanitize_input(city)
    zip_code = sanitize_input(zip_code, max_length=20)
    street = sanitize_input(street)

    # Validate own VAT ID format (must be German)
    own_normalized = normalize_vat_id(own_vat_id)
    own_valid, own_cc, own_error = validate_format(own_normalized)
    if not own_valid:
        return json.dumps(
            {"error": f"Eigene USt-IdNr ungültig: {own_error}"},
            ensure_ascii=False,
            indent=2,
        )
    if own_cc != "DE":
        return json.dumps(
            {
                "error": "Eigene USt-IdNr muss eine deutsche USt-IdNr sein (Präfix DE). "
                f"Übergeben: {own_cc}"
            },
            ensure_ascii=False,
            indent=2,
        )

    # Validate partner VAT ID format
    partner_normalized = normalize_vat_id(partner_vat_id)
    partner_valid, _partner_cc, partner_error = validate_format(partner_normalized)
    if not partner_valid:
        return json.dumps(
            {"error": f"Partner USt-IdNr ungültig: {partner_error}"},
            ensure_ascii=False,
            indent=2,
        )

    lifespan_ctx = ctx.request_context.lifespan_context
    bzst: BZStClient = lifespan_ctx["bzst"]

    try:
        result = await bzst.validate_qualified(
            own_vat_id=own_normalized,
            partner_vat_id=partner_normalized,
            company_name=company_name,
            city=city,
            zip_code=zip_code,
            street=street,
        )
    except BZStConnectionError as e:
        return json.dumps(
            {"error": f"BZSt-Verbindungsfehler: {e}"},
            ensure_ascii=False,
            indent=2,
        )

    return json.dumps(result.model_dump(), ensure_ascii=False, indent=2)


# --- Server Card ---


def _server_card() -> dict[str, Any]:
    """Build the MCP server card for Smithery discovery."""
    return {
        "serverInfo": {"name": "ustidnr-mcp", "version": "0.1.0"},
        "authentication": {"required": False},
        "tools": [
            {
                "name": name,
                "description": (tool.description or "")[:200],
            }
            for name, tool in mcp._tool_manager._tools.items()
        ],
        "resources": [{"name": uri} for uri in mcp._resource_manager._resources],
        "prompts": [{"name": name} for name in mcp._prompt_manager._prompts],
    }


# --- Entry Point ---


def main() -> None:
    """Run the MCP server."""
    if settings.mcp_transport == "streamable-http":
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        async def well_known(_request: Request) -> JSONResponse:
            return JSONResponse(_server_card())

        app = mcp.streamable_http_app()
        app.routes.insert(0, Route("/.well-known/mcp/server-card.json", well_known))
        import uvicorn

        uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
