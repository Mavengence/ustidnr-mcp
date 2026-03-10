"""German MCP prompts for USt-IdNr validation workflows."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts on the MCP server."""

    @mcp.prompt()
    def geschaeftspartner_pruefen(partner_ustidnr: str) -> str:
        """Prüfe die USt-IdNr meines Geschäftspartners."""
        return (
            f"Bitte prüfe die USt-IdNr '{partner_ustidnr}' meines Geschäftspartners.\n\n"
            "1. Validiere zunächst das Format der USt-IdNr.\n"
            "2. Führe dann eine einfache Bestätigung über die BZSt eVatR-Schnittstelle durch.\n"
            "3. Gib mir eine klare Aussage, ob die USt-IdNr gültig ist.\n"
            "4. Falls Firmenname oder Adresse zurückgeliefert werden, zeige diese an.\n\n"
            "Nutze dafür das Tool 'validate_ustidnr'."
        )

    @mcp.prompt()
    def batch_validierung(ustidnr_liste: str) -> str:
        """Validiere alle USt-IdNr in meiner Kundenliste."""
        return (
            f"Bitte validiere folgende USt-IdNr aus meiner Kundenliste:\n\n{ustidnr_liste}\n\n"
            "1. Prüfe jede einzelne USt-IdNr auf Gültigkeit.\n"
            "2. Erstelle eine Übersicht mit Ergebnis pro USt-IdNr.\n"
            "3. Markiere ungültige oder fehlerhafte Einträge deutlich.\n"
            "4. Gib eine Zusammenfassung (x von y gültig).\n\n"
            "Nutze dafür das Tool 'validate_batch'."
        )

    @mcp.prompt()
    def qualifizierte_bestaetigung(
        eigene_ustidnr: str,
        partner_ustidnr: str,
        firmenname: str,
        ort: str,
        plz: str,
        strasse: str,
    ) -> str:
        """Qualifizierte Bestätigung für innergemeinschaftliche Lieferung."""
        return (
            "Bitte führe eine qualifizierte Bestätigung (§6a UStG) durch:\n\n"
            f"- Eigene USt-IdNr: {eigene_ustidnr}\n"
            f"- Partner USt-IdNr: {partner_ustidnr}\n"
            f"- Firmenname: {firmenname}\n"
            f"- Ort: {ort}\n"
            f"- PLZ: {plz}\n"
            f"- Straße: {strasse}\n\n"
            "1. Prüfe, ob Name, Adresse und USt-IdNr mit den offiziellen Daten "
            "des Mitgliedstaats übereinstimmen.\n"
            "2. Erkläre die Ergebniscodes (A=Übereinstimmung, B=keine Übereinstimmung, "
            "C=nicht angefragt, D=nicht verfügbar).\n"
            "3. Beurteile, ob die Voraussetzungen für eine steuerfreie "
            "innergemeinschaftliche Lieferung nach §6a UStG erfüllt sind.\n"
            "4. Weise auf Risiken hin, falls Felder nicht übereinstimmen.\n\n"
            "Nutze dafür das Tool 'qualified_confirmation'."
        )

    @mcp.prompt()
    def nachweispflicht_erklaerung() -> str:
        """Erkläre §6a UStG Nachweispflicht für innergemeinschaftliche Lieferungen."""
        return (
            "Erkläre mir die Nachweispflicht nach §6a UStG für "
            "innergemeinschaftliche Lieferungen:\n\n"
            "1. Was muss ich als Lieferant nachweisen?\n"
            "2. Welche Rolle spielt die USt-IdNr-Prüfung?\n"
            "3. Was ist der Unterschied zwischen einfacher und "
            "qualifizierter Bestätigung?\n"
            "4. Welche Konsequenzen drohen bei fehlender Prüfung (§25d UStG)?\n"
            "5. Wie oft sollte ich die USt-IdNr meiner Geschäftspartner prüfen?\n\n"
            "Nutze die Ressource 'ustidnr://compliance/paragraph-6a-ustg' als Grundlage."
        )

    @mcp.prompt()
    def eu_rechnungen_batch() -> str:
        """Batch-Validierung für EU-Rechnungen — monatlicher Workflow."""
        return (
            "Ich möchte einen monatlichen Validierungs-Workflow für "
            "alle EU-Geschäftspartner einrichten:\n\n"
            "1. Welche Daten brauche ich pro Partner?\n"
            "2. Wie führe ich eine Batch-Validierung durch?\n"
            "3. Was mache ich bei ungültigen Ergebnissen?\n"
            "4. Wie dokumentiere ich die Ergebnisse für die Steuerprüfung?\n"
            "5. Empfehlung: Einfache oder qualifizierte Bestätigung?\n\n"
            "Nutze die Tools 'validate_batch' und 'qualified_confirmation'."
        )

    @mcp.prompt()
    def reverse_charge_pruefung(partner_ustidnr: str) -> str:
        """Prüfe Voraussetzungen für Reverse-Charge-Verfahren."""
        return (
            f"Prüfe die Voraussetzungen für das Reverse-Charge-Verfahren "
            f"mit dem Partner {partner_ustidnr}:\n\n"
            "1. Ist die USt-IdNr des Partners gültig?\n"
            "2. Stammt die USt-IdNr aus einem anderen EU-Mitgliedstaat?\n"
            "3. Erkläre die Reverse-Charge-Regelung (§13b UStG).\n"
            "4. Welche Angaben müssen auf der Rechnung stehen?\n\n"
            "Nutze das Tool 'validate_ustidnr'."
        )

    @mcp.prompt()
    def einvoice_workflow(partner_ustidnr: str) -> str:
        """Kompletter Workflow: USt-IdNr prüfen → Rechnung erstellen."""
        return (
            f"Führe den kompletten EU-Rechnungs-Workflow durch:\n\n"
            f"Partner USt-IdNr: {partner_ustidnr}\n\n"
            "Schritt 1: Validiere die USt-IdNr des Partners (validate_ustidnr).\n"
            "Schritt 2: Falls gültig, führe eine qualifizierte Bestätigung durch "
            "(qualified_confirmation).\n"
            "Schritt 3: Empfehle basierend auf dem Ergebnis, ob eine steuerfreie "
            "innergemeinschaftliche Lieferung möglich ist.\n"
            "Schritt 4: Falls einvoice-mcp verfügbar ist, erstelle die Rechnung "
            "mit dem Bestätigungsergebnis als Anlage.\n\n"
            "Dies ist der empfohlene Workflow für §6a UStG-konforme EU-Rechnungen."
        )

    @mcp.prompt()
    def format_erklaerung(laendercode: str = "") -> str:
        """Erkläre das USt-IdNr-Format für ein EU-Land."""
        if laendercode:
            return (
                f"Erkläre das Format der USt-IdNr für den Ländercode '{laendercode}':\n\n"
                "1. Wie ist die USt-IdNr aufgebaut (Präfix, Länge, Prüfziffer)?\n"
                "2. Zeige ein Beispiel.\n"
                "3. Gibt es Besonderheiten bei diesem Land?\n\n"
                "Nutze die Ressource 'ustidnr://reference/eu-formats'."
            )
        return (
            "Zeige eine Übersicht aller EU USt-IdNr-Formate:\n\n"
            "1. Liste alle 27 EU-Mitgliedstaaten mit Präfix und Format.\n"
            "2. Zeige jeweils ein Beispiel.\n"
            "3. Hebe Besonderheiten hervor (z.B. variable Länge, Buchstaben).\n\n"
            "Nutze die Ressource 'ustidnr://reference/eu-formats'."
        )
