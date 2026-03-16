# ustidnr-mcp

[![CI](https://github.com/Mavengence/ustidnr-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/Mavengence/ustidnr-mcp/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)](https://github.com/Mavengence/ustidnr-mcp)
[![PyPI](https://img.shields.io/pypi/v/ustidnr-mcp)](https://pypi.org/project/ustidnr-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/ustidnr-mcp)](https://pypi.org/project/ustidnr-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Smithery](https://smithery.ai/badge/ustidnr-mcp)](https://smithery.ai/servers/mavengence/ustidnr-mcp)

> **Validate EU VAT IDs directly from your AI assistant.** Ask Claude to check a VAT number, verify a trading partner's details, or batch-validate your entire customer list — powered by the official German BZSt API.

The only MCP server that supports **qualifizierte Bestätigung** (qualified confirmation) — the legally required proof for German businesses conducting EU cross-border transactions under §6a UStG.

**No API key required.** The BZSt eVatR API is a free public service.

---

## What Can It Do?

Just ask your AI assistant in plain language:

| You say... | What happens |
|------------|-------------|
| *"Is DE123456789 a valid VAT ID?"* | Format check + live API validation |
| *"Check if FR12345678901 belongs to Acme SARL in Paris"* | Qualified confirmation with name & address matching |
| *"Validate all VAT IDs in my customer list"* | Batch validation of up to 100 IDs in parallel |
| *"Can I do reverse charge with IT12345678901?"* | Checks prerequisites for §13b UStG |
| *"Prüfe die USt-IdNr und erstelle dann eine Rechnung"* | Works with [einvoice-mcp](https://github.com/Mavengence/einvoice-mcp) for a complete workflow |

Works in **German and English** — all 8 built-in prompts are in German, but the tools understand both languages.

---

## Quick Start

### Install via Smithery (recommended)

[![Smithery](https://smithery.ai/badge/ustidnr-mcp)](https://smithery.ai/servers/mavengence/ustidnr-mcp)

```bash
npx -y @smithery/cli install ustidnr-mcp --client claude
```

### Install via pip

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

### Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

---

## Features at a Glance

| Feature | Description |
|---------|-------------|
| **Simple Validation** | Format check + VIES/BZSt API lookup for any EU VAT ID |
| **Batch Validation** | Validate up to 100 VAT IDs in parallel |
| **Qualified Confirmation** | Match company name & address against official BZSt records (§6a UStG) |
| **27 EU Countries** | Full format validation with country-specific patterns |
| **German Check Digit** | ISO/IEC 7064 MOD 11,10 algorithm for DE VAT IDs |
| **8 German Prompts** | Pre-built workflows for common tax compliance tasks |
| **4 Reference Resources** | EU formats, BZSt error codes, §6a UStG guide, check digit algorithm |
| **No API Key Needed** | BZSt eVatR is a free public government API |

---

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
2. **Smart routing** — German qualified confirmation goes to BZSt; simple validation goes to VIES
3. **Structured results** — Returns JSON with German descriptions, match codes, and actionable guidance

---

## Tools

### `validate_ustidnr` — Check a single VAT ID

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

### `validate_batch` — Check up to 100 VAT IDs at once

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

### `qualified_confirmation` — Verify company identity (§6a UStG)

The legally required check for German businesses doing EU cross-border trade.

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

| Code | Meaning | What to do |
|------|---------|------------|
| **A** | Match | All good — data confirmed by the member state |
| **B** | No match | Stop — verify with your trading partner before shipping |
| **C** | Not requested | Field was not sent for checking |
| **D** | Not available | The member state does not provide this data |

---

## Why This Server?

There are 5+ existing VAT validation MCP servers — all are simple VIES wrappers. This one goes further:

| Feature | VIES-only MCPs | ustidnr-mcp |
|---------|---------------|-------------|
| Simple validation | Yes | Yes |
| Qualified confirmation | No | **Yes** (BZSt eVatR) |
| §6a UStG compliance | No | **Yes** |
| Batch validation | No | **Yes** (up to 100) |
| German check digit | No | **Yes** (MOD 11,10) |
| German prompts | No | **Yes** (8 prompts) |
| Reference resources | No | **Yes** (4 resources) |
| BZSt new REST API (2025) | N/A | **Yes** |

---

## Legal Background

### Why does this matter?

German businesses must verify EU trading partners' VAT IDs before claiming zero-rate VAT on cross-border deliveries. Without proper verification, you risk being liable for your buyer's unpaid VAT in fraud cases (§25d UStG).

The **qualified confirmation** (qualifizierte Bestätigung) creates **Vertrauensschutz** (trust protection) under §6a Abs. 4 UStG — it's your legal shield.

### Simple vs. Qualified Confirmation

| | Simple | Qualified |
|---|--------|-----------|
| Checks validity | Yes | Yes |
| Checks company name | No | Yes |
| Checks address | No | Yes (city, ZIP, street) |
| Legal protection | Basic | Full (§6a Abs. 4 UStG) |
| Use for | Routine checks | All EU cross-border deliveries |

---

## Works Great With einvoice-mcp

Use together with [einvoice-mcp](https://github.com/Mavengence/einvoice-mcp) for a complete German EU invoicing workflow:

1. **Validate** the buyer's VAT ID
2. **Qualified confirmation** to verify company identity
3. **Generate** a compliant XRechnung/ZUGFeRD invoice
4. **Embed** the confirmation result in invoice notes

> *"Prüfe die USt-IdNr von FR12345678901 und erstelle dann eine XRechnung"*

---

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

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `error_code: 203` | Member state temporarily unavailable — retry later |
| `error_code: 207` | Rate limited — wait before sending more requests |
| `error_code: 204` | Your own German USt-IdNr is invalid — double-check it |
| `error_code: 205` | Own VAT ID must be German (DE prefix) for qualified confirmation |
| All match codes `D` | That member state doesn't provide address data |
| Timeout errors | Increase `REQUEST_TIMEOUT` env variable (default: 30s) |

---

## Configuration

All settings via environment variables. See [`.env.example`](.env.example) for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `BZST_BASE_URL` | `https://api.evatr.vies.bzst.de/app/v1/abfrage` | BZSt REST API endpoint |
| `REQUEST_TIMEOUT` | `30.0` | HTTP timeout in seconds |
| `BATCH_MAX_SIZE` | `100` | Maximum batch size |

---

## Limitations

- **Qualified confirmation requires a German USt-IdNr** as `own_vat_id` — this is a BZSt requirement
- **Single validation uses VIES** — BZSt requires both own + partner IDs, so single-ID checks go through VIES
- **Current status only** — the new BZSt REST API does not support historical/date-range queries
- **Rate limits** — BZSt enforces session-based rate limits for qualified confirmations
- **Member state availability** — some EU countries temporarily refuse validation requests (error codes 203/217)

---

## Compliance Proof

> **401 tests | 98% coverage | 45 security tests | 27 EU countries | all BZSt error codes**

| Category | Tests | Coverage |
|----------|-------|----------|
| Format validation (27 EU countries) | 80+ | 98% |
| BZSt REST API client | 60+ | 96% |
| VIES fallback client | 30+ | 100% |
| Security (OWASP Top 10) | 45+ | 100% |
| Prompts & resources | 40+ | 100% |
| Models & config | 50+ | 100% |
| Integration flows | 20+ | — |
| Custom exceptions | 10+ | 100% |

| Module | Stmts | Miss | Cover |
|--------|-------|------|-------|
| `bzst_client.py` | 79 | 3 | 96% |
| `vies_client.py` | 43 | 0 | 100% |
| `validator.py` | 46 | 1 | 98% |
| `models.py` | 71 | 0 | 100% |
| `errors.py` | 19 | 0 | 100% |
| `config.py` | 15 | 0 | 100% |
| `prompts.py` | 29 | 1 | 97% |
| `resources.py` | 21 | 0 | 100% |
| **TOTAL** | **328** | **7** | **98%** |

---

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

## Documentation

- [Compliance Guide](docs/COMPLIANCE_GUIDE.md) — §6a UStG requirements, decision tree, error codes
- [Deployment Guide](docs/DEPLOYMENT.md) — Docker, Smithery, Render.com, Claude Desktop

---

## License

MIT
