"""MCP server for EU VAT ID validation (USt-IdNr) via BZSt eVatR API."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ustidnr-mcp")
except PackageNotFoundError:
    __version__ = "0.1.0"
