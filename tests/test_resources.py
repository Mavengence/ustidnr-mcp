"""Tests for MCP resources."""

from __future__ import annotations

import json

from ustidnr_mcp.resources import register_resources


def _get_resource_fn(name: str):
    """Helper to get a resource function by name."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    register_resources(mcp)
    resource = mcp._resource_manager._resources[name]
    return resource.fn


class TestResourceRegistration:
    def test_register_does_not_raise(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_resources(mcp)
        assert len(mcp._resource_manager._resources) == 4

    def test_resource_uris(self) -> None:
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("test")
        register_resources(mcp)
        expected = {
            "ustidnr://reference/eu-formats",
            "ustidnr://reference/bzst-response-codes",
            "ustidnr://compliance/paragraph-6a-ustg",
            "ustidnr://reference/check-digit-algorithm",
        }
        assert set(mcp._resource_manager._resources.keys()) == expected


class TestEuFormatsResource:
    def test_returns_valid_json(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/eu-formats")
        result = fn()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_27_countries(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/eu-formats")
        data = json.loads(fn())
        assert len(data["formats"]) == 27

    def test_all_countries_have_required_fields(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/eu-formats")
        data = json.loads(fn())
        for fmt in data["formats"]:
            assert "country_code" in fmt
            assert "country_name" in fmt
            assert "pattern" in fmt
            assert "example" in fmt

    def test_germany_present(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/eu-formats")
        data = json.loads(fn())
        de_formats = [f for f in data["formats"] if f["country_code"] == "DE"]
        assert len(de_formats) == 1
        assert de_formats[0]["country_name"] == "Deutschland"
        assert de_formats[0]["example"] == "DE123456789"

    def test_greece_uses_el(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/eu-formats")
        data = json.loads(fn())
        el_formats = [f for f in data["formats"] if f["country_code"] == "EL"]
        assert len(el_formats) == 1

    def test_has_title(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/eu-formats")
        data = json.loads(fn())
        assert "title" in data
        assert len(data["title"]) > 0


class TestBzstResponseCodesResource:
    def test_returns_valid_json(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/bzst-response-codes")
        result = fn()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_contains_all_error_codes(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/bzst-response-codes")
        data = json.loads(fn())
        error_codes = data["error_codes"]
        # Should have codes 200-221
        for code in range(200, 222):
            assert str(code) in error_codes, f"Missing error code {code}"

    def test_contains_match_codes(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/bzst-response-codes")
        data = json.loads(fn())
        match_codes = data["match_codes"]
        for code in ["A", "B", "C", "D"]:
            assert code in match_codes

    def test_match_code_has_meaning(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/bzst-response-codes")
        data = json.loads(fn())
        for code_data in data["match_codes"].values():
            assert "meaning" in code_data
            assert "description" in code_data


class TestParagraph6aResource:
    def test_returns_valid_json(self) -> None:
        fn = _get_resource_fn("ustidnr://compliance/paragraph-6a-ustg")
        result = fn()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_has_sections(self) -> None:
        fn = _get_resource_fn("ustidnr://compliance/paragraph-6a-ustg")
        data = json.loads(fn())
        assert "sections" in data
        assert len(data["sections"]) >= 4

    def test_mentions_6a_ustg(self) -> None:
        fn = _get_resource_fn("ustidnr://compliance/paragraph-6a-ustg")
        result = fn()
        assert "6a" in result
        assert "UStG" in result

    def test_mentions_25d(self) -> None:
        fn = _get_resource_fn("ustidnr://compliance/paragraph-6a-ustg")
        result = fn()
        assert "25d" in result

    def test_has_qualified_vs_simple_section(self) -> None:
        fn = _get_resource_fn("ustidnr://compliance/paragraph-6a-ustg")
        data = json.loads(fn())
        headings = [s["heading"] for s in data["sections"]]
        assert any("Qualifizierte" in h or "qualifizierte" in h.lower() for h in headings)

    def test_sections_have_content(self) -> None:
        fn = _get_resource_fn("ustidnr://compliance/paragraph-6a-ustg")
        data = json.loads(fn())
        for section in data["sections"]:
            assert "heading" in section
            assert "content" in section
            assert len(section["content"]) > 0


class TestCheckDigitAlgorithmResource:
    def test_returns_valid_json(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/check-digit-algorithm")
        result = fn()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_has_algorithm_steps(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/check-digit-algorithm")
        data = json.loads(fn())
        assert "algorithm" in data
        assert len(data["algorithm"]) >= 4

    def test_has_example(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/check-digit-algorithm")
        data = json.loads(fn())
        assert "example" in data
        assert data["example"]["vat_id"] == "DE129273398"
        assert data["example"]["valid"] is True

    def test_references_iso_standard(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/check-digit-algorithm")
        data = json.loads(fn())
        assert "ISO" in data.get("standard", "")
        assert "7064" in data.get("standard", "")

    def test_mentions_mod_11_10(self) -> None:
        fn = _get_resource_fn("ustidnr://reference/check-digit-algorithm")
        data = json.loads(fn())
        assert "MOD 11,10" in data.get("standard", "") or "MOD 11,10" in data.get("description", "")
