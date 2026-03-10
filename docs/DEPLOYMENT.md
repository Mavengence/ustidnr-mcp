# Deployment Guide

## Local (Claude Desktop / Claude Code)

### pip install

```bash
pip install ustidnr-mcp
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

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

## Docker

### Build and run

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

### Environment variables

See `.env.example` for the full list. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | `stdio` for local, `streamable-http` for web |
| `MCP_PORT` | `8000` | HTTP port (streamable-http only) |
| `BZST_BASE_URL` | `https://api.evatr.vies.bzst.de/app/v1/abfrage` | BZSt endpoint |
| `REQUEST_TIMEOUT` | `30.0` | HTTP timeout in seconds |
| `BATCH_MAX_SIZE` | `100` | Max batch validation size |
| `LOG_LEVEL` | `INFO` | Log verbosity |

### streamable-http mode

For web deployment, set `MCP_TRANSPORT=streamable-http`:

```bash
MCP_TRANSPORT=streamable-http MCP_PORT=8000 ustidnr-mcp
```

The server exposes:
- MCP endpoint at `/mcp/`
- Server card at `/.well-known/mcp/server-card.json`

## Smithery

Deploy to [Smithery](https://smithery.ai) using the included `smithery.yaml`:

```bash
npx @anthropic-ai/smithery publish
```

## Render.com

Use the included `render.yaml`:

1. Connect your GitHub repository to Render
2. Render auto-detects `render.yaml`
3. Deploy as a web service

## Security Considerations

- The BZSt API requires HTTPS (TLS 1.2+)
- No API keys needed — authentication is via your German USt-IdNr
- Rate limits are enforced by BZSt per session
- All inputs are sanitized (control chars stripped, length limited)
- The Docker container runs as non-root user `mcp`

## Health Check

For streamable-http mode, verify the server is running:

```bash
curl http://localhost:8000/.well-known/mcp/server-card.json
```
