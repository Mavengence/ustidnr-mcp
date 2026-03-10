# ustidnr-mcp

[![CI](https://github.com/Mavengence/ustidnr-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/Mavengence/ustidnr-mcp/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)](https://github.com/Mavengence/ustidnr-mcp)
[![PyPI](https://img.shields.io/pypi/v/ustidnr-mcp)](https://pypi.org/project/ustidnr-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/ustidnr-mcp)](https://pypi.org/project/ustidnr-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Smithery](https://smithery.ai/badge/ustidnr-mcp)](https://smithery.ai/server/ustidnr-mcp)

**MCP server for EU VAT ID validation (USt-IdNr) via the BZSt eVatR REST API.**

The only MCP server that supports **qualifizierte Bestätigung** (qualified confirmation) — the legally required proof for German businesses conducting EU cross-border transactions under §6a UStG.

---

## Features

| Feature | Description |
|---------|-------------|
| **Simple Validation** | Format check + VIES/BZSt API lookup for any EU VAT ID |
| **Batch Validation** | Validate up to 100 VAT IDs in parallel |
| **Qualified Confirmation** | §6a UStG: match company name & address against official BZSt records |
| **27 EU Countries** | Full format validation with country-specific regex patterns |
| **German Check Digit** | ISO/IEC 7064 MOD 11,10 algorithm for DE USt-IdNr |
| **8 German Prompts** | Pre-built workflows for common tax compliance tasks |
| **4 Reference Resources** | EU formats, BZSt codes, §6a UStG guide, check digit algorithm |

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  MCP Client │────>│ ustidnr-mcp  │────>│  BZSt eVatR API │
│  (Claude)   │<────│              │<────│  (REST, JSON)   │
└─────────────┘     │  Format      │     └─────────────────┘
                    │  Validation  │     ┌─────────────────┐
                    │  + Routing   │────>│  EU VIES API    │
                    │              │<────│  (REST, JSON)   │
                    └──────────────┘     └─────────────────┘
```

1. **Format validation** — Checks VAT ID against country-specific regex pattern
2. **API routing** — German qualified confirmation → BZSt; simple validation → VIES
3. **Result mapping** — Translates API responses to structured JSON with German descriptions

## Tools

### `validate_ustidnr`

Validate a single EU VAT ID (format + API check).

| Parameter | Type | Description |
|-----------|------|-------------|
| `vat_id` | `str` | EU VAT ID to validate (e.g., `DE123456789`) |

```json
{
  "vat_id": "FR12345678901",
  "valid": true,
  "error_code": "200",
  "error_description": "Die angefragte USt-IdNr. ist gültig.",
  "country_code": "FR",
  "company_name": "Acme SARL",
  "company_address": "1 Rue de Rivoli, 75001 Paris"
}
```

### `validate_batch`

Batch validation of multiple VAT IDs (max 100, parallel execution).

| Parameter | Type | Description |
|-----------|------|-------------|
| `vat_ids` | `list[str]` | List of EU VAT IDs to validate |

```json
{
  "total": 3,
  "valid_count": 2,
  "invalid_count": 1,
  "error_count": 0,
  "results": [...]
}
```

### `qualified_confirmation`

Qualified confirmation via BZSt eVatR for §6a UStG compliance.

| Parameter | Type | Description |
|-----------|------|-------------|
| `own_vat_id` | `str` | Your German USt-IdNr (must start with DE) |
| `partner_vat_id` | `str` | Partner's EU USt-IdNr |
| `company_name` | `str` | Expected company name |
| `city` | `str` | Expected city |
| `zip_code` | `str` | Expected postal code |
| `street` | `str` | Expected street |

```json
{
  "own_vat_id": "DE123456789",
  "partner_vat_id": "FR12345678901",
  "valid": true,
  "error_code": "200",
  "company_name_match": "A",
  "city_match": "A",
  "zip_match": "A",
  "street_match": "B",
  "all_fields_match": false
}
```

**Match codes:**

| Code | Meaning | Action |
|------|---------|--------|
| **A** | Match | Data confirmed |
| **B** | No match | Verify with partner, do not ship |
| **C** | Not requested | Field was not sent for checking |
| **D** | Not available | Member state does not provide this field |

## Error Codes

| Code | Description |
|------|-------------|
| `200` | Valid |
| `201` | Invalid format |
| `202` | Not registered (not assigned) |
| `203` | Member state service unavailable |
| `204` | Own VAT ID invalid |
| `205` | Own VAT ID is not German |
| `206` | Not an EU member state |
| `207` | Rate limited |
| `208` | Internal BZSt error |
| `217` | Service temporarily unavailable |
| `219` | Valid with qualified confirmation |

## Installation

```bash
pip install ustidnr-mcp
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ustidnr": {
      "command": "ustidnr-mcp"
    }
  }
}
```

### Claude Code

```bash
claude mcp add ustidnr-mcp -- ustidnr-mcp
```

### Smithery

[![Smithery](https://smithery.ai/badge/ustidnr-mcp)](https://smithery.ai/server/ustidnr-mcp)

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

## Usage

### Validate a VAT ID

> *"Prüfe die USt-IdNr DE123456789"*

### Qualified Confirmation

> *"Qualifizierte Bestätigung für FR12345678901, Firma Acme SARL, Paris"*

### Batch Validation

> *"Validiere alle USt-IdNr in meiner Kundenliste: DE123456789, FR12345678901, ATU12345678"*

### Reverse Charge Check

> *"Prüfe die Voraussetzungen für Reverse-Charge mit IT12345678901"*

### Combined Workflow with einvoice-mcp

> *"Prüfe die USt-IdNr von FR12345678901 und erstelle dann eine Rechnung"*

## Legal Context

### §6a UStG — Steuerfreie innergemeinschaftliche Lieferungen

German businesses must verify their EU trading partners' VAT IDs to claim zero-rate VAT on cross-border deliveries. The **qualified confirmation** (qualifizierte Bestätigung) provides legal protection:

- **§6a Abs. 3 UStG**: Requires proof that the buyer holds a valid VAT ID
- **§6a Abs. 4 UStG**: Qualified confirmation creates trust protection (Vertrauensschutz)
- **§25d UStG**: Without confirmation, the seller may be liable for the buyer's unpaid VAT in fraud cases

### Simple vs. Qualified Confirmation

| | Simple | Qualified |
|---|--------|-----------|
| Checks validity | Yes | Yes |
| Checks company name | No | Yes |
| Checks address | No | Yes (city, ZIP, street) |
| Legal protection | Basic | Full (§6a Abs. 4 UStG) |
| Recommended for | Routine checks | All EU cross-border deliveries |

## Why This Server?

### Compared to VIES-Only MCP Servers

There are 5 existing VAT validation MCP servers on GitHub — all are VIES-only wrappers (0 stars each). This server adds:

| Feature | VIES-only MCPs | ustidnr-mcp |
|---------|---------------|-------------|
| Simple validation | Yes | Yes |
| Qualified confirmation | No | **Yes** (BZSt eVatR) |
| §6a UStG compliance | No | **Yes** |
| Batch validation | No | **Yes** (up to 100) |
| German check digit | No | **Yes** (MOD 11,10) |
| German prompts | No | **Yes** (8 prompts) |
| Reference resources | No | **Yes** (4 resources) |
| BZSt new REST API | N/A | **Yes** (July 2025) |

## Limitations

- **BZSt qualified confirmation requires a German own USt-IdNr** — you cannot use a non-DE VAT ID as `own_vat_id`
- **Single validation uses VIES** — the BZSt API requires both own + partner VAT IDs, so single-ID validation goes through VIES
- **No historical lookups** — validates current status only (the BZSt API no longer supports date-range queries in the new REST endpoint)
- **Rate limits** — BZSt enforces session-based rate limits for qualified confirmations
- **Member state availability** — some EU countries temporarily refuse validation requests (error codes 203/217)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `error_code: 203` | Member state temporarily unavailable — retry later |
| `error_code: 207` | Rate limited — wait before sending more requests |
| `error_code: 204` | Your own German USt-IdNr is invalid — check it |
| `error_code: 205` | Own VAT ID must be German (DE prefix) |
| All match codes `D` | Member state doesn't provide address data |
| Timeout errors | Increase `REQUEST_TIMEOUT` env variable |

## Companion: einvoice-mcp

Use together with [einvoice-mcp](https://github.com/Mavengence/einvoice-mcp) for a complete German EU invoicing workflow:

1. **Validate** buyer's VAT ID (`ustidnr-mcp`)
2. **Qualified confirmation** with company details (`ustidnr-mcp`)
3. **Generate** compliant XRechnung/ZUGFeRD invoice (`einvoice-mcp`)
4. **Embed** confirmation result in invoice notes

## Development

```bash
make install      # Install with dev dependencies
make test         # Run tests (95%+ coverage required)
make lint         # Lint with ruff
make type-check   # Type check with mypy --strict
make fmt          # Auto-format
make build        # Build wheel
make docker-up    # Run in Docker
```

## Configuration

All settings can be overridden via environment variables. See [`.env.example`](.env.example) for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `BZST_BASE_URL` | `https://api.evatr.vies.bzst.de/app/v1/abfrage` | BZSt REST API endpoint |
| `REQUEST_TIMEOUT` | `30.0` | HTTP timeout in seconds |
| `BATCH_MAX_SIZE` | `100` | Maximum batch size |

## License

MIT
