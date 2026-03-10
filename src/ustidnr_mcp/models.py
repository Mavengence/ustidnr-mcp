"""Pydantic models for VAT ID validation."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MatchCode(Enum):
    """BZSt qualified confirmation match codes."""

    MATCH = "A"
    NO_MATCH = "B"
    NOT_REQUESTED = "C"
    NOT_AVAILABLE = "D"


class ErrorCode(Enum):
    """Internal error codes (based on legacy BZSt eVatR codes)."""

    VALID = "200"
    INVALID_FORMAT = "201"
    NOT_REGISTERED = "202"
    SERVICE_UNAVAILABLE = "203"
    OWN_VAT_INVALID = "204"
    OWN_VAT_NOT_GERMAN = "205"
    NOT_EU_MEMBER = "206"
    RATE_LIMITED = "207"
    INTERNAL_ERROR = "208"
    DATE_INVALID = "209"
    BATCH_LIMIT = "210"
    INDIVIDUAL_ONLY = "211"
    QUALIFIED_NOT_POSSIBLE = "212"
    PRINT_REQUESTED = "213"
    PRINT_NOT_REQUESTED = "214"
    PRINT_RESULT_FOLLOWS = "215"
    GENERAL_ERROR = "216"
    SERVICE_TEMP_UNAVAILABLE = "217"
    DUPLICATE_REQUEST = "218"
    VALID_QUALIFIED = "219"
    INVALID_OWN_FORMAT = "220"
    XML_PARSE_ERROR = "221"

    @property
    def description_de(self) -> str:
        descriptions: dict[str, str] = {
            "200": "Die angefragte USt-IdNr. ist gültig.",
            "201": "Die angefragte USt-IdNr. ist ungültig (Format).",
            "202": "Die angefragte USt-IdNr. ist ungültig (nicht vergeben).",
            "203": "Der Mitgliedstaat kann die Anfrage derzeit nicht beantworten.",
            "204": "Die eigene USt-IdNr. ist ungültig.",
            "205": "Die eigene USt-IdNr. ist keine deutsche USt-IdNr.",
            "206": "Die angefragte USt-IdNr. stammt nicht aus einem EU-Mitgliedstaat.",
            "207": "Serverkapazität überschritten. Bitte später erneut versuchen.",
            "208": "Interner Fehler beim BZSt.",
            "209": "Das angegebene Datum ist ungültig.",
            "210": "Die Anfrage überschreitet das Batch-Limit.",
            "211": "Eine Einzelanfrage ist nicht möglich.",
            "212": "Qualifizierte Bestätigung ist für diesen Mitgliedstaat nicht möglich.",
            "213": "Amtliche Bestätigungsmitteilung wurde angefordert.",
            "214": "Amtliche Bestätigungsmitteilung wurde nicht angefordert.",
            "215": "Das Ergebnis der Anfrage folgt als amtliche Bestätigungsmitteilung.",
            "216": "Allgemeiner Fehler.",
            "217": "Dienst vorübergehend nicht verfügbar.",
            "218": "Doppelte Anfrage — bitte warten.",
            "219": "Gültig mit qualifizierter Bestätigung.",
            "220": "Format der eigenen USt-IdNr. ist ungültig.",
            "221": "XML-Parsefehler.",
        }
        return descriptions.get(self.value, "Unbekannter Fehlercode.")


# Mapping from new BZSt REST API status codes to internal error codes.
# The new API (July 2025) uses "evatr-XXXX" format instead of numeric codes.
BZST_STATUS_MAP: dict[str, tuple[str, bool]] = {
    # (internal_error_code, is_valid)
    "evatr-0000": ("200", True),  # Valid
    "evatr-0002": ("201", False),  # Missing required fields
    "evatr-0003": ("212", False),  # Valid but missing qualified data
    "evatr-0004": ("220", False),  # Own VAT syntax invalid
    "evatr-0005": ("201", False),  # Queried VAT syntax invalid
    "evatr-0006": ("205", False),  # Not authorized (DE-DE query)
    "evatr-0007": ("208", False),  # Malformed API call
    "evatr-0008": ("207", False),  # Rate limited (session max reached)
    "evatr-0011": ("203", False),  # Service temporarily unavailable
    "evatr-0012": ("201", False),  # VAT ID doesn't match schema
    "evatr-0013": ("203", False),  # Service temporarily unavailable
    "evatr-1001": ("217", False),  # Service temporarily unavailable
    "evatr-1002": ("208", False),  # Processing error
    "evatr-1003": ("208", False),  # Processing error
    "evatr-1004": ("208", False),  # Processing error
    "evatr-2001": ("202", False),  # Not assigned at query time
    "evatr-2002": ("209", False),  # Valid from future date
    "evatr-2003": ("206", False),  # Invalid country code
    "evatr-2004": ("208", False),  # Processing error
    "evatr-2005": ("204", False),  # Own DE VAT currently invalid
    "evatr-2006": ("202", False),  # Was valid during past period
    "evatr-2007": ("208", False),  # Processing error
    "evatr-2008": ("200", True),  # Valid with special circumstances
    "evatr-2011": ("208", False),  # Processing error
    "evatr-3011": ("208", False),  # Processing error
}


class ValidationResult(BaseModel):
    """Result of a single VAT ID validation."""

    vat_id: str
    valid: bool
    error_code: str
    error_description: str
    country_code: str = ""
    company_name: str = ""
    company_address: str = ""
    request_date: str = ""
    raw_response: dict[str, Any] = Field(default_factory=dict)


class QualifiedConfirmationResult(BaseModel):
    """Result of a qualified confirmation (qualifizierte Bestätigung)."""

    own_vat_id: str
    partner_vat_id: str
    valid: bool
    error_code: str
    error_description: str
    company_name_match: str = ""
    city_match: str = ""
    zip_match: str = ""
    street_match: str = ""
    request_date: str = ""
    print_confirmation: str = ""
    raw_response: dict[str, Any] = Field(default_factory=dict)

    @property
    def all_fields_match(self) -> bool:
        return all(
            code == MatchCode.MATCH.value
            for code in [
                self.company_name_match,
                self.city_match,
                self.zip_match,
                self.street_match,
            ]
            if code and code != MatchCode.NOT_REQUESTED.value
        )


class BatchValidationResult(BaseModel):
    """Result of batch VAT ID validation."""

    results: list[ValidationResult]
    total: int
    valid_count: int
    invalid_count: int
    error_count: int


# EU country VAT ID format patterns (regex)
EU_VAT_FORMATS: dict[str, str] = {
    "AT": r"^ATU\d{8}$",
    "BE": r"^BE[01]\d{9}$",
    "BG": r"^BG\d{9,10}$",
    "CY": r"^CY\d{8}[A-Z]$",
    "CZ": r"^CZ\d{8,10}$",
    "DE": r"^DE\d{9}$",
    "DK": r"^DK\d{8}$",
    "EE": r"^EE\d{9}$",
    "EL": r"^EL\d{9}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
    "FI": r"^FI\d{8}$",
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",
    "HR": r"^HR\d{11}$",
    "HU": r"^HU\d{8}$",
    "IE": r"^IE\d{7}[A-Z]{1,2}$|^IE\d[A-Z]\d{5}[A-Z]$",
    "IT": r"^IT\d{11}$",
    "LT": r"^LT\d{9}$|^LT\d{12}$",
    "LU": r"^LU\d{8}$",
    "LV": r"^LV\d{11}$",
    "MT": r"^MT\d{8}$",
    "NL": r"^NL\d{9}B\d{2}$",
    "PL": r"^PL\d{10}$",
    "PT": r"^PT\d{9}$",
    "RO": r"^RO\d{2,10}$",
    "SE": r"^SE\d{12}$",
    "SI": r"^SI\d{8}$",
    "SK": r"^SK\d{10}$",
}

EU_COUNTRY_NAMES: dict[str, str] = {
    "AT": "Österreich",
    "BE": "Belgien",
    "BG": "Bulgarien",
    "CY": "Zypern",
    "CZ": "Tschechien",
    "DE": "Deutschland",
    "DK": "Dänemark",
    "EE": "Estland",
    "EL": "Griechenland",
    "ES": "Spanien",
    "FI": "Finnland",
    "FR": "Frankreich",
    "HR": "Kroatien",
    "HU": "Ungarn",
    "IE": "Irland",
    "IT": "Italien",
    "LT": "Litauen",
    "LU": "Luxemburg",
    "LV": "Lettland",
    "MT": "Malta",
    "NL": "Niederlande",
    "PL": "Polen",
    "PT": "Portugal",
    "RO": "Rumänien",
    "SE": "Schweden",
    "SI": "Slowenien",
    "SK": "Slowakei",
}
