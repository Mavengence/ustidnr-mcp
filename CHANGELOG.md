# Changelog

## [0.2.0] - 2026-03-10

### Changed
- **BREAKING**: BZSt client now uses the new REST API (July 2025) at `api.evatr.vies.bzst.de`
  - POST with JSON instead of GET with XML
  - New error codes (evatr-XXXX format) mapped to internal codes
  - Old XML-RPC endpoint was sunset November 2025
- `validate_qualified()` no longer accepts `print_confirmation` parameter (not supported by new API)
- Coverage requirement raised from 80% to 95%

### Added
- Custom exception hierarchy (`errors.py`): `UstIdNrError`, `BZStConnectionError`, `BZStValidationError`, `VIESConnectionError`, `FormatValidationError`, `BatchLimitError`
- Input sanitization: control character stripping, max length enforcement
- `BZST_STATUS_MAP` mapping from new evatr-XXXX codes to internal error codes
- VIES client now returns proper error code for HTTP 429 (rate limiting)
- CI/CD: GitHub Actions for test matrix (Python 3.11/3.12/3.13) and PyPI publishing
- `py.typed` marker for PEP 561 type stub support
- `.env.example` with documented configuration defaults
- `render.yaml` for Render.com deployment
- 25 security tests (SQL injection, XSS, path traversal, null bytes, oversized inputs)
- Tests for prompts, resources, models, config, errors, integration flows
- Comprehensive README with tool reference, error codes, architecture diagram, troubleshooting

### Stats
- **401 tests** (up from 106), **98% coverage** (up from 80%)
- 11 test files (up from 4)
- 8 source modules

## [0.1.0] - 2026-03-10

### Added
- `validate_ustidnr` tool — single VAT ID validation (format + VIES API)
- `validate_batch` tool — batch validation of up to 100 VAT IDs
- `qualified_confirmation` tool — BZSt eVatR qualified confirmation (§6a UStG)
- 8 German prompts for common validation workflows
- 4 resources: EU formats, BZSt response codes, §6a UStG guide, check digit algorithm
- Docker support with non-root container
- Smithery deployment configuration
