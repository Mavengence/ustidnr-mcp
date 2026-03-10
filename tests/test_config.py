"""Tests for configuration."""

from __future__ import annotations

import pytest

from ustidnr_mcp.config import Settings


class TestSettingsDefaults:
    def test_default_log_level(self) -> None:
        s = Settings()
        assert s.log_level == "INFO"

    def test_default_transport(self) -> None:
        s = Settings()
        assert s.mcp_transport == "stdio"

    def test_default_host(self) -> None:
        s = Settings()
        assert s.mcp_host == "0.0.0.0"

    def test_default_port(self) -> None:
        s = Settings()
        assert s.mcp_port == 8000

    def test_default_bzst_url(self) -> None:
        s = Settings()
        assert "api.evatr.vies.bzst.de" in s.bzst_base_url

    def test_default_timeout(self) -> None:
        s = Settings()
        assert s.request_timeout == 30.0

    def test_default_batch_max_size(self) -> None:
        s = Settings()
        assert s.batch_max_size == 100

    def test_default_batch_concurrency(self) -> None:
        s = Settings()
        assert s.batch_concurrency == 10

    def test_default_max_input_length(self) -> None:
        s = Settings()
        assert s.max_input_length == 256

    def test_default_max_vat_id_length(self) -> None:
        s = Settings()
        assert s.max_vat_id_length == 50


class TestSettingsEnvironmentOverride:
    def test_log_level_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.log_level == "DEBUG"

    def test_transport_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
        s = Settings()
        assert s.mcp_transport == "streamable-http"

    def test_port_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_PORT", "9000")
        s = Settings()
        assert s.mcp_port == 9000

    def test_timeout_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("REQUEST_TIMEOUT", "60.0")
        s = Settings()
        assert s.request_timeout == 60.0

    def test_batch_max_size_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BATCH_MAX_SIZE", "50")
        s = Settings()
        assert s.batch_max_size == 50

    def test_bzst_url_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BZST_BASE_URL", "https://custom.example.com/api")
        s = Settings()
        assert s.bzst_base_url == "https://custom.example.com/api"


class TestSettingsValidation:
    def test_invalid_log_level_rejected(self) -> None:
        with pytest.raises(ValueError):
            Settings(log_level="INVALID")  # type: ignore[arg-type]

    def test_invalid_transport_rejected(self) -> None:
        with pytest.raises(ValueError):
            Settings(mcp_transport="invalid")  # type: ignore[arg-type]

    def test_extra_fields_ignored(self) -> None:
        # extra="ignore" in model_config means unknown fields don't raise
        s = Settings()
        assert s.log_level == "INFO"
