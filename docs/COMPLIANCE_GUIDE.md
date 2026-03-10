# USt-IdNr Compliance Guide — §6a UStG

## Überblick

Dieses Dokument beschreibt die steuerrechtlichen Anforderungen an die USt-IdNr-Prüfung
bei innergemeinschaftlichen Lieferungen nach deutschem Recht.

## Rechtsgrundlage

### §6a UStG — Innergemeinschaftliche Lieferungen

Eine Lieferung ist steuerfrei, wenn **alle** Voraussetzungen erfüllt sind:

1. **Gelangensbeweis** (§6a Abs. 1 Nr. 1 UStG): Der Gegenstand gelangt in einen anderen EU-Mitgliedstaat
2. **Unternehmereigenschaft** (§6a Abs. 1 Nr. 2 UStG): Der Erwerber ist Unternehmer mit gültiger USt-IdNr
3. **Erwerbsbesteuerung** (§6a Abs. 1 Nr. 3 UStG): Der Erwerb unterliegt im Bestimmungsland der Erwerbsbesteuerung

### §6a Abs. 3 UStG — Nachweispflichten

Der Unternehmer muss die Voraussetzungen nachweisen durch:
- Buchmäßigen Nachweis (§17a-c UStDV)
- Belegmäßigen Nachweis (Gelangensbestätigung)
- **Prüfung der USt-IdNr des Erwerbers beim BZSt**

### §6a Abs. 4 UStG — Vertrauensschutz

Die **qualifizierte Bestätigung** schafft Vertrauensschutz:
> Wenn der Unternehmer die USt-IdNr beim BZSt qualifiziert bestätigen ließ und die
> Angaben übereinstimmen, haftet er nicht für die entgangene Steuer, selbst wenn
> der Erwerber tatsächlich keine innergemeinschaftliche Lieferung vornimmt.

### §25d UStG — Haftung bei Betrug

Ohne qualifizierte Bestätigung kann der Lieferant für die entgangene Umsatzsteuer haften,
wenn er wusste oder hätte wissen müssen, dass die Lieferung in einen Umsatzsteuerbetrug
einbezogen war.

## Einfache vs. Qualifizierte Bestätigung

### Einfache Bestätigung

- Prüft nur: Ist die USt-IdNr vergeben und gültig?
- Reicht für **grundlegende Sorgfaltspflicht**
- Kein Vertrauensschutz

### Qualifizierte Bestätigung

- Prüft zusätzlich: Stimmen Name, Ort, PLZ und Straße überein?
- Erstellt **Vertrauensschutz** nach §6a Abs. 4 UStG
- **Empfohlen für alle innergemeinschaftlichen Lieferungen**
- Ergebnis muss 10 Jahre archiviert werden (Aufbewahrungspflicht)

### Ergebniscodes der qualifizierten Bestätigung

| Code | Bedeutung | Handlungsempfehlung |
|------|-----------|---------------------|
| **A** | Übereinstimmung | Daten bestätigt — Lieferung möglich |
| **B** | Keine Übereinstimmung | Angaben beim Partner verifizieren, Lieferung stoppen |
| **C** | Nicht angefragt | Feld wurde nicht zur Prüfung übergeben |
| **D** | Nicht verfügbar | Mitgliedstaat stellt dieses Feld nicht bereit |

## Empfohlener Workflow

### Bei neuen Geschäftspartnern

1. USt-IdNr-Format prüfen (`validate_ustidnr`)
2. Qualifizierte Bestätigung durchführen (`qualified_confirmation`)
3. Bei Code "B": Angaben klären, **nicht liefern**
4. Ergebnis archivieren (10 Jahre)

### Bei bestehenden Partnern

1. Monatliche Batch-Validierung (`validate_batch`)
2. Bei Adressänderungen: erneute qualifizierte Bestätigung
3. Ergebnisse dokumentieren

### Entscheidungsbaum

```
Innergemeinschaftliche Lieferung?
├── Ja → Partner hat USt-IdNr?
│   ├── Ja → Format gültig?
│   │   ├── Ja → Qualifizierte Bestätigung durchführen
│   │   │   ├── Alle A → Steuerfrei liefern (§6a UStG)
│   │   │   ├── Code B → Stopp! Angaben prüfen
│   │   │   └── Code D → Alternative Nachweise einholen
│   │   └── Nein → Partner kontaktieren
│   └── Nein → Nicht steuerfrei (19% MwSt)
└── Nein → Normale Besteuerung
```

## BZSt eVatR REST API

Seit Juli 2025 nutzt das BZSt die neue REST API:
- Endpoint: `https://api.evatr.vies.bzst.de/app/v1/abfrage`
- Methode: POST (JSON)
- Alte XML-RPC-Schnittstelle wurde November 2025 abgeschaltet

### Statuscodes (evatr-XXXX)

| Status | HTTP | Bedeutung |
|--------|------|-----------|
| evatr-0000 | 200 | Gültig |
| evatr-2001 | 404 | Nicht vergeben |
| evatr-0004 | 400 | Eigene USt-IdNr syntaktisch ungültig |
| evatr-0005 | 400 | Angefragte USt-IdNr syntaktisch ungültig |
| evatr-0006 | 403 | Nicht berechtigt (DE-DE-Abfrage) |
| evatr-0008 | 403 | Rate Limit erreicht |
| evatr-0011 | 503 | Dienst vorübergehend nicht verfügbar |
| evatr-2003 | 400 | Ungültiger Ländercode |
| evatr-2005 | 404 | Eigene USt-IdNr derzeit ungültig |

## Aufbewahrungspflichten

- **10 Jahre** Aufbewahrungspflicht für Bestätigungsergebnisse (§147 AO)
- Elektronische Archivierung erlaubt
- Bestätigungsergebnis, Datum und angefragte Daten aufbewahren

## Häufige Fehler

1. **Keine Prüfung vor Lieferung** → §25d UStG Haftungsrisiko
2. **Nur einfache statt qualifizierter Bestätigung** → Kein Vertrauensschutz
3. **Ergebnisse nicht archiviert** → Nachweispflicht nicht erfüllt
4. **Prüfung nur bei Erstanlage** → Partner kann USt-IdNr verlieren
5. **Code B ignoriert** → Steuerschaden bei Betriebsprüfung
