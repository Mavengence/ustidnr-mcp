"""MCP resources — reference data for USt-IdNr validation."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from ustidnr_mcp.models import EU_COUNTRY_NAMES, EU_VAT_FORMATS


def register_resources(mcp: FastMCP) -> None:
    """Register all resources on the MCP server."""

    @mcp.resource("ustidnr://reference/eu-formats")
    def eu_formats() -> str:
        """EU USt-IdNr-Formate nach Mitgliedstaat.

        Enthält Länderpräfix, Regex-Muster und Beispiel für alle 27 EU-Staaten.
        """
        formats = []
        examples: dict[str, str] = {
            "AT": "ATU12345678",
            "BE": "BE0123456789",
            "BG": "BG123456789",
            "CY": "CY12345678A",
            "CZ": "CZ12345678",
            "DE": "DE123456789",
            "DK": "DK12345678",
            "EE": "EE123456789",
            "EL": "EL123456789",
            "ES": "ESA12345678",
            "FI": "FI12345678",
            "FR": "FR12345678901",
            "HR": "HR12345678901",
            "HU": "HU12345678",
            "IE": "IE1234567A",
            "IT": "IT12345678901",
            "LT": "LT123456789",
            "LU": "LU12345678",
            "LV": "LV12345678901",
            "MT": "MT12345678",
            "NL": "NL123456789B01",
            "PL": "PL1234567890",
            "PT": "PT123456789",
            "RO": "RO1234567890",
            "SE": "SE123456789012",
            "SI": "SI12345678",
            "SK": "SK1234567890",
        }

        for code, pattern in sorted(EU_VAT_FORMATS.items()):
            formats.append(
                {
                    "country_code": code,
                    "country_name": EU_COUNTRY_NAMES.get(code, code),
                    "pattern": pattern,
                    "example": examples.get(code, f"{code}..."),
                }
            )

        return json.dumps(
            {
                "title": "EU USt-IdNr-Formate",
                "description": (
                    "Formatmuster für USt-IdNr aller 27 EU-Mitgliedstaaten. "
                    "Jede USt-IdNr beginnt mit dem 2-stelligen Länderpräfix."
                ),
                "formats": formats,
            },
            ensure_ascii=False,
            indent=2,
        )

    @mcp.resource("ustidnr://reference/bzst-response-codes")
    def bzst_response_codes() -> str:
        """BZSt eVatR Antwortcodes und deren Bedeutung.

        Fehlercodes (200-221) und Übereinstimmungscodes (A/B/C/D)
        für die qualifizierte Bestätigung.
        """
        return json.dumps(
            {
                "title": "BZSt eVatR Antwortcodes",
                "error_codes": {
                    "200": "Die angefragte USt-IdNr. ist gültig.",
                    "201": "Die angefragte USt-IdNr. ist ungültig (Format).",
                    "202": "Die angefragte USt-IdNr. ist ungültig (nicht vergeben).",
                    "203": "Der Mitgliedstaat kann die Anfrage derzeit nicht beantworten.",
                    "204": "Die eigene USt-IdNr. ist ungültig.",
                    "205": "Die eigene USt-IdNr. ist keine deutsche USt-IdNr.",
                    "206": "Nicht aus einem EU-Mitgliedstaat.",
                    "207": "Serverkapazität überschritten.",
                    "208": "Interner Fehler beim BZSt.",
                    "209": "Ungültiges Datum.",
                    "210": "Batch-Limit überschritten.",
                    "211": "Einzelanfrage nicht möglich.",
                    "212": "Qualifizierte Bestätigung nicht möglich für diesen Mitgliedstaat.",
                    "213": "Amtliche Bestätigungsmitteilung angefordert.",
                    "214": "Amtliche Bestätigungsmitteilung nicht angefordert.",
                    "215": "Ergebnis folgt als amtliche Bestätigungsmitteilung.",
                    "216": "Allgemeiner Fehler.",
                    "217": "Dienst vorübergehend nicht verfügbar.",
                    "218": "Doppelte Anfrage.",
                    "219": "Gültig mit qualifizierter Bestätigung.",
                    "220": "Format der eigenen USt-IdNr. ungültig.",
                    "221": "XML-Parsefehler.",
                },
                "match_codes": {
                    "A": {
                        "code": "A",
                        "meaning": "Übereinstimmung (Match)",
                        "description": (
                            "Die angefragten Daten stimmen mit den beim "
                            "Mitgliedstaat gespeicherten Daten überein."
                        ),
                    },
                    "B": {
                        "code": "B",
                        "meaning": "Keine Übereinstimmung (No Match)",
                        "description": (
                            "Die angefragten Daten stimmen NICHT mit den "
                            "offiziellen Daten überein. Prüfen Sie die Angaben."
                        ),
                    },
                    "C": {
                        "code": "C",
                        "meaning": "Nicht angefragt (Not Requested)",
                        "description": ("Dieses Feld wurde nicht zur Prüfung übergeben."),
                    },
                    "D": {
                        "code": "D",
                        "meaning": "Nicht verfügbar (Not Available)",
                        "description": (
                            "Der Mitgliedstaat stellt dieses Feld nicht zur Prüfung bereit."
                        ),
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )

    @mcp.resource("ustidnr://compliance/paragraph-6a-ustg")
    def paragraph_6a_ustg() -> str:
        """§6a UStG / §25d UStG Compliance-Leitfaden.

        Nachweispflichten für steuerfreie innergemeinschaftliche Lieferungen
        und Haftungsrisiken bei fehlender Prüfung.
        """
        return json.dumps(
            {
                "title": "§6a UStG — Innergemeinschaftliche Lieferungen",
                "sections": [
                    {
                        "heading": "Grundsatz",
                        "content": (
                            "Innergemeinschaftliche Lieferungen sind nach §4 Nr. 1b i.V.m. "
                            "§6a UStG von der Umsatzsteuer befreit, wenn bestimmte "
                            "Voraussetzungen erfüllt sind."
                        ),
                    },
                    {
                        "heading": "Voraussetzungen (§6a Abs. 1 UStG)",
                        "content": (
                            "1. Der Gegenstand gelangt in einen anderen EU-Mitgliedstaat.\n"
                            "2. Der Erwerber ist ein Unternehmer mit gültiger USt-IdNr.\n"
                            "3. Der Erwerb unterliegt im Bestimmungsland der Erwerbsbesteuerung."
                        ),
                    },
                    {
                        "heading": "Nachweispflicht (§6a Abs. 3 UStG)",
                        "content": (
                            "Der Unternehmer muss die Voraussetzungen nachweisen durch:\n"
                            "- Buchmäßigen Nachweis (§17a-c UStDV)\n"
                            "- Belegmäßigen Nachweis (Gelangensbestätigung)\n"
                            "- Prüfung der USt-IdNr des Erwerbers beim BZSt"
                        ),
                    },
                    {
                        "heading": "Einfache vs. Qualifizierte Bestätigung",
                        "content": (
                            "EINFACHE BESTÄTIGUNG:\n"
                            "- Prüft nur, ob die USt-IdNr gültig und vergeben ist.\n"
                            "- Reicht für die grundlegende Sorgfaltspflicht.\n\n"
                            "QUALIFIZIERTE BESTÄTIGUNG:\n"
                            "- Prüft zusätzlich Name, Ort, PLZ und Straße.\n"
                            "- Erstellt Vertrauensschutz nach §6a Abs. 4 UStG.\n"
                            "- Empfohlen für alle innergemeinschaftlichen Lieferungen.\n"
                            "- Ergebnis sollte archiviert werden (10 Jahre Aufbewahrungspflicht)."
                        ),
                    },
                    {
                        "heading": "Haftung (§25d UStG)",
                        "content": (
                            "§25d UStG: Der Unternehmer haftet für die entgangene Steuer, "
                            "wenn er wusste oder hätte wissen müssen, dass die Lieferung "
                            "in einen Umsatzsteuerbetrug einbezogen war.\n\n"
                            "Die qualifizierte Bestätigung schützt vor dieser Haftung, "
                            "da sie den Nachweis der Sorgfaltspflicht erbringt."
                        ),
                    },
                    {
                        "heading": "Empfehlung",
                        "content": (
                            "1. Vor JEDER innergemeinschaftlichen Lieferung USt-IdNr prüfen.\n"
                            "2. Qualifizierte Bestätigung für neue Geschäftspartner.\n"
                            "3. Regelmäßige Batch-Prüfung aller aktiven Partner (monatlich).\n"
                            "4. Ergebnisse archivieren (10 Jahre).\n"
                            "5. Bei Nichtübereinstimmung: Lieferung stoppen, Partner kontaktieren."
                        ),
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )

    @mcp.resource("ustidnr://reference/check-digit-algorithm")
    def check_digit_algorithm() -> str:
        """Prüfzifferalgorithmus für deutsche USt-IdNr.

        ISO/IEC 7064 MOD 11,10 — Berechnung der 9. Stelle.
        """
        return json.dumps(
            {
                "title": "Prüfzifferalgorithmus — Deutsche USt-IdNr",
                "standard": "ISO/IEC 7064 MOD 11,10",
                "description": (
                    "Die deutsche USt-IdNr besteht aus dem Präfix 'DE' gefolgt von "
                    "9 Ziffern. Die 9. Ziffer ist eine Prüfziffer, berechnet nach "
                    "dem MOD 11,10-Verfahren."
                ),
                "algorithm": [
                    "1. Startwert: Produkt = 10",
                    "2. Für jede der ersten 8 Ziffern:",
                    "   a. Summe = (Ziffer + Produkt) mod 10",
                    "   b. Falls Summe = 0, setze Summe = 10",
                    "   c. Produkt = (2 x Summe) mod 11",
                    "3. Prüfziffer = 11 - Produkt",
                    "4. Falls Prüfziffer = 10, setze Prüfziffer = 0",
                    "5. Prüfziffer muss gleich der 9. Ziffer sein.",
                ],
                "example": {
                    "vat_id": "DE129273398",
                    "digits": "129273398",
                    "check_digit": 8,
                    "valid": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
