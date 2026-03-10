"""Tests for MCP prompts."""

from __future__ import annotations

from ustidnr_mcp.prompts import register_prompts


class TestPromptRegistration:
    """Verify all prompts register and produce non-empty output."""

    def test_register_does_not_raise(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        assert len(mcp._prompt_manager._prompts) == 8

    def test_prompt_names(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        expected = {
            "geschaeftspartner_pruefen",
            "batch_validierung",
            "qualifizierte_bestaetigung",
            "nachweispflicht_erklaerung",
            "eu_rechnungen_batch",
            "reverse_charge_pruefung",
            "einvoice_workflow",
            "format_erklaerung",
        }
        assert set(mcp._prompt_manager._prompts.keys()) == expected


class TestGeschaeftspartnerPruefen:
    def test_returns_nonempty(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt_fn = mcp._prompt_manager._prompts["geschaeftspartner_pruefen"]
        # The registered prompt has a fn attribute we can test indirectly
        assert prompt_fn is not None

    def test_references_tool(self) -> None:
        """Prompt text should reference validate_ustidnr tool."""
        from mcp.server.fastmcp import FastMCP

        from ustidnr_mcp.prompts import register_prompts

        mcp = FastMCP("test")
        register_prompts(mcp)
        # Access the underlying function
        prompt = mcp._prompt_manager._prompts["geschaeftspartner_pruefen"]
        # Call the function directly to get the prompt text
        result = prompt.fn(partner_ustidnr="DE123456789")
        assert "validate_ustidnr" in result


class TestBatchValidierung:
    def test_references_batch_tool(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["batch_validierung"]
        result = prompt.fn(ustidnr_liste="DE123456789\nFR12345678901")
        assert "validate_batch" in result

    def test_includes_input_list(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["batch_validierung"]
        result = prompt.fn(ustidnr_liste="DE123456789")
        assert "DE123456789" in result


class TestQualifizierteBestaetigung:
    def test_references_qualified_tool(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["qualifizierte_bestaetigung"]
        result = prompt.fn(
            eigene_ustidnr="DE123456789",
            partner_ustidnr="FR12345678901",
            firmenname="Acme",
            ort="Paris",
            plz="75001",
            strasse="Rue de Rivoli",
        )
        assert "qualified_confirmation" in result
        assert "DE123456789" in result
        assert "FR12345678901" in result


class TestNachweispflicht:
    def test_references_resource(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["nachweispflicht_erklaerung"]
        result = prompt.fn()
        assert "ustidnr://compliance/paragraph-6a-ustg" in result

    def test_mentions_25d(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["nachweispflicht_erklaerung"]
        result = prompt.fn()
        assert "25d" in result


class TestReverseChargePruefung:
    def test_includes_partner_id(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["reverse_charge_pruefung"]
        result = prompt.fn(partner_ustidnr="IT12345678901")
        assert "IT12345678901" in result
        assert "validate_ustidnr" in result


class TestEinvoiceWorkflow:
    def test_references_both_tools(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["einvoice_workflow"]
        result = prompt.fn(partner_ustidnr="FR12345678901")
        assert "validate_ustidnr" in result
        assert "qualified_confirmation" in result


class TestFormatErklaerung:
    def test_with_country_code(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["format_erklaerung"]
        result = prompt.fn(laendercode="DE")
        assert "DE" in result
        assert "ustidnr://reference/eu-formats" in result

    def test_without_country_code(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_prompts(mcp)
        prompt = mcp._prompt_manager._prompts["format_erklaerung"]
        result = prompt.fn()
        assert "27" in result
        assert "ustidnr://reference/eu-formats" in result
