"""VAT back rules for the supported countries. Pure. No I/O.

The rules map an expense category to a refundable share per country.
The supported countries are Austria (AT), Germany (DE), France (FR), Italy (IT),
the Netherlands (NL), Poland (PL), Czechia (CZ), Denmark (DK) and Sweden (SE).
Directive 2008/9/EC, Art. 5 refunds VAT only to the extent the country of refund allows deduction.
Each country rule cites the national source of its restriction.
A decision carries a human-readable reason for the UI and the pitch.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.domain.money import Money

Country = Literal["AT", "DE", "FR", "IT", "NL", "PL", "CZ", "DK", "SE"]
SUPPORTED_COUNTRIES: frozenset[str] = frozenset({"AT", "DE", "FR", "IT", "NL", "PL", "CZ", "DK", "SE"})

# The ten expense categories of Directive 2008/9/EC, Art. 9.
CATEGORIES: tuple[str, ...] = (
    "FUEL",
    "VEHICLE_HIRE",
    "VEHICLE_EXPENSES",
    "ROAD_TOLL",
    "TRAVEL",
    "ACCOMMODATION",
    "FOOD_AND_DRINK",
    "FAIR_ADMISSION",
    "ENTERTAINMENT",
    "OTHER",
)

FULL_SHARE = Decimal("1")
NO_SHARE = Decimal("0")

DIRECTIVE_SOURCE = "Directive 2006/112/EC, Art. 168. Directive 2008/9/EC, Art. 5."


@dataclass(frozen=True)
class CategoryRule:
    refundable_share: Decimal
    reason: str
    source: str

    def __post_init__(self) -> None:
        if not isinstance(self.refundable_share, Decimal):
            raise TypeError("The refundable share must be a Decimal.")
        if not NO_SHARE <= self.refundable_share <= FULL_SHARE:
            raise ValueError(f"The refundable share must be between 0 and 1, got {self.refundable_share}.")

    @property
    def eligible(self) -> bool:
        return self.refundable_share > NO_SHARE


@dataclass(frozen=True)
class LineDecision:
    line_index: int
    category: str
    eligible: bool
    refundable_share: Decimal
    refundable_vat: Money
    reason: str


def _country_rules(country_name: str, restrictions: dict[str, CategoryRule]) -> dict[str, CategoryRule]:
    """Return a rule for every category. A category without a restriction is fully refundable."""
    full_rule = CategoryRule(
        FULL_SHARE,
        f"Refundable business expense in {country_name}. No national restriction applies.",
        DIRECTIVE_SOURCE,
    )
    return {category: restrictions.get(category, full_rule) for category in CATEGORIES}


# Source: European Commission, VAT refund vademecum Austria, section 4.
# https://taxation-customs.ec.europa.eu/system/files/2016-09/vademecum-refund-austria_en.pdf
_AT_VEHICLE_SOURCE = "UStG 1994 § 12 (2) Z 2 lit. b. EC VAT refund vademecum Austria, section 4."
_AT_RULES = _country_rules(
    "Austria",
    {
        "FUEL": CategoryRule(NO_SHARE, "Austria allows no VAT deduction for the operation of passenger cars, including fuel.", _AT_VEHICLE_SOURCE),
        "VEHICLE_HIRE": CategoryRule(NO_SHARE, "Austria allows no VAT deduction for the lease or hire of passenger cars.", _AT_VEHICLE_SOURCE),
        "VEHICLE_EXPENSES": CategoryRule(NO_SHARE, "Austria allows no VAT deduction for the operation of passenger cars.", _AT_VEHICLE_SOURCE),
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "Austria allows no VAT deduction for living expenses such as entertainment.",
            "UStG 1994 § 12 (2) Z 2 lit. a. EC VAT refund vademecum Austria, section 4.",
        ),
    },
)

# Source: UStG § 15 (1a). https://www.gesetze-im-internet.de/ustg_1980/__15.html
# Business meals (Bewirtung) stay deductible. Entertainment under EStG § 4 (5) is not.
_DE_RULES = _country_rules(
    "Germany",
    {
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "Germany allows no VAT deduction for entertainment and gifts that income tax does not allow.",
            "UStG § 15 (1a) with EStG § 4 (5) sentence 1 no. 1 to 4 and 7.",
        ),
    },
)

# Sources: BOFiP BOI-TVA-DED-30-30-10 (staff lodging), BOI-TVA-DED-30-30-20 (passenger cars),
# BOI-TVA-DED-30-30-30 (passenger transport), BOI-TVA-DED-30-30-40 (fuel). https://bofip.impots.gouv.fr
_FR_VEHICLE_SOURCE = "CGI annexe II art. 206 IV 2 6°. BOFiP BOI-TVA-DED-30-30-20."
_FR_RULES = _country_rules(
    "France",
    {
        "ACCOMMODATION": CategoryRule(
            NO_SHARE,
            "France allows no VAT deduction for the lodging of directors and staff.",
            "CGI annexe II art. 206 IV 2 2°. BOFiP BOI-TVA-DED-30-30-10.",
        ),
        "TRAVEL": CategoryRule(
            NO_SHARE,
            "France allows no VAT deduction for passenger transport by road, rail, air or water.",
            "CGI annexe II art. 206 IV 2. BOFiP BOI-TVA-DED-30-30-30.",
        ),
        "FUEL": CategoryRule(
            Decimal("0.8"),
            "France refunds 80% of the VAT on petrol and diesel for passenger cars.",
            "CGI art. 298 4 1°. BOFiP BOI-TVA-DED-30-30-40.",
        ),
        "VEHICLE_HIRE": CategoryRule(NO_SHARE, "France allows no VAT deduction for the hire of passenger cars.", _FR_VEHICLE_SOURCE),
        "VEHICLE_EXPENSES": CategoryRule(NO_SHARE, "France allows no VAT deduction for parts and services for passenger cars.", _FR_VEHICLE_SOURCE),
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "France allows no VAT deduction for gifts and entertainment above the small gift limit.",
            "CGI annexe II art. 206 IV 2 3°.",
        ),
    },
)

# Source: DPR 633/1972, art. 19-bis1. https://www.fisco7.it/wp-content/uploads/Art_19bis1.pdf
# Letter d) applies the 40% car share of letter c) to fuel, hire, parking, repairs and road tolls.
_IT_VEHICLE_SOURCE = "DPR 633/1972 art. 19-bis1 (1) c) and d)."
_IT_RULES = _country_rules(
    "Italy",
    {
        "FUEL": CategoryRule(Decimal("0.4"), "Italy refunds 40% of the VAT on fuel for cars not used only for business.", _IT_VEHICLE_SOURCE),
        "VEHICLE_HIRE": CategoryRule(Decimal("0.4"), "Italy refunds 40% of the VAT on car hire for cars not used only for business.", _IT_VEHICLE_SOURCE),
        "VEHICLE_EXPENSES": CategoryRule(Decimal("0.4"), "Italy refunds 40% of the VAT on parking, repairs and upkeep of cars.", _IT_VEHICLE_SOURCE),
        "ROAD_TOLL": CategoryRule(Decimal("0.4"), "Italy refunds 40% of the VAT on road tolls for cars.", _IT_VEHICLE_SOURCE),
        "TRAVEL": CategoryRule(
            NO_SHARE,
            "Italy allows no VAT deduction for passenger transport services.",
            "DPR 633/1972 art. 19-bis1 (1) e).",
        ),
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "Italy allows no VAT deduction for entertainment expenses, except goods up to 50 euro each.",
            "DPR 633/1972 art. 19-bis1 (1) h).",
        ),
    },
)

# Sources: Wet OB 1968 art. 15 lid 5 (food and drink in the hospitality sector, since 2024).
# Besluit uitsluiting aftrek omzetbelasting 1968 (BUA) for business gifts and entertainment.
_NL_RULES = _country_rules(
    "the Netherlands",
    {
        "FOOD_AND_DRINK": CategoryRule(
            NO_SHARE,
            "The Netherlands allows no VAT deduction for food and drink consumed in hotels, cafés or restaurants.",
            "Wet op de omzetbelasting 1968 art. 15 lid 5.",
        ),
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "The Netherlands excludes VAT on business gifts and entertainment from deduction.",
            "Besluit uitsluiting aftrek omzetbelasting 1968 (BUA) art. 1.",
        ),
    },
)

# Sources: Ustawa o podatku od towarów i usług, art. 88 ust. 1 pkt 4 (accommodation and restaurant services)
# and art. 86a ust. 1 and 2 (50% for mixed-use vehicles, incl. fuel, hire and upkeep).
_PL_VEHICLE_SOURCE = "Ustawa o VAT art. 86a ust. 1 i 2."
_PL_RULES = _country_rules(
    "Poland",
    {
        "ACCOMMODATION": CategoryRule(
            NO_SHARE,
            "Poland allows no VAT deduction for purchased accommodation services.",
            "Ustawa o VAT art. 88 ust. 1 pkt 4 lit. b.",
        ),
        "FOOD_AND_DRINK": CategoryRule(
            NO_SHARE,
            "Poland allows no VAT deduction for purchased restaurant services.",
            "Ustawa o VAT art. 88 ust. 1 pkt 4 lit. b.",
        ),
        "FUEL": CategoryRule(Decimal("0.5"), "Poland refunds 50% of the VAT on fuel for mixed-use cars.", _PL_VEHICLE_SOURCE),
        "VEHICLE_HIRE": CategoryRule(Decimal("0.5"), "Poland refunds 50% of the VAT on hire of mixed-use cars.", _PL_VEHICLE_SOURCE),
        "VEHICLE_EXPENSES": CategoryRule(Decimal("0.5"), "Poland refunds 50% of the VAT on the use and upkeep of mixed-use cars.", _PL_VEHICLE_SOURCE),
        "ROAD_TOLL": CategoryRule(Decimal("0.5"), "Poland refunds 50% of the VAT on road tolls for mixed-use cars.", _PL_VEHICLE_SOURCE),
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "Poland allows deduction only for purchases used for taxable sales. Entertainment has no such link.",
            "Ustawa o VAT art. 86 ust. 1.",
        ),
    },
)

# Source: Zákon č. 235/2004 Sb. o dani z přidané hodnoty, § 72 odst. 6 (representation).
_CZ_RULES = _country_rules(
    "Czechia",
    {
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "Czechia allows no VAT deduction for representation and entertainment expenses.",
            "Zákon č. 235/2004 Sb. § 72 odst. 6.",
        ),
    },
)

# Sources: Momsloven § 42. Den juridiske vejledning D.A.11.5.2 (hotel), D.A.11.5.7 (restaurant 25%),
# D.A.22.4.1 (passenger cars). https://tax.dk/jv/da/D_A_11_5_7.htm
_DK_VEHICLE_SOURCE = "Momsloven § 42 stk. 1 nr. 6. Den juridiske vejledning D.A.22.4.1."
_DK_RULES = _country_rules(
    "Denmark",
    {
        "FOOD_AND_DRINK": CategoryRule(
            Decimal("0.25"),
            "Denmark refunds 25% of the VAT on restaurant services for strictly business purposes.",
            "Momsloven § 42 stk. 2. Den juridiske vejledning D.A.11.5.7.",
        ),
        "FUEL": CategoryRule(NO_SHARE, "Denmark allows no VAT deduction for the operation of passenger cars, including fuel.", _DK_VEHICLE_SOURCE),
        "VEHICLE_HIRE": CategoryRule(NO_SHARE, "Denmark allows no VAT deduction for short-term hire of passenger cars.", _DK_VEHICLE_SOURCE),
        "VEHICLE_EXPENSES": CategoryRule(NO_SHARE, "Denmark allows no VAT deduction for the operation of passenger cars.", _DK_VEHICLE_SOURCE),
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "Denmark allows no VAT deduction for entertainment, representation and gifts.",
            "Momsloven § 42 stk. 1 nr. 5. Den juridiske vejledning D.A.11.5.7.",
        ),
    },
)

# Sources: Skatteverket, "Bilar och moms" and "Avdrag för moms vid representation".
# https://skatteverket.se/foretag/moms/sarskildamomsregler/bilarochmoms.4.58d555751259e4d6616800010628.html
# https://www.skatteverket.se/4.15532c7b1442f256baec84b.html
_SE_RULES = _country_rules(
    "Sweden",
    {
        "VEHICLE_HIRE": CategoryRule(
            Decimal("0.5"),
            "Sweden refunds 50% of the VAT on the hire or lease of passenger cars.",
            "Mervärdesskattelag (2023:200) 13 kap. Skatteverket, Bilar och moms.",
        ),
        "ENTERTAINMENT": CategoryRule(
            NO_SHARE,
            "Sweden allows VAT on representation only for meals up to 300 SEK per person. Other entertainment is not refundable.",
            "Mervärdesskattelag (2023:200) 13 kap. Skatteverket, Avdrag för moms vid representation.",
        ),
    },
)

COUNTRY_RULES: dict[str, dict[str, CategoryRule]] = {
    "AT": _AT_RULES,
    "DE": _DE_RULES,
    "FR": _FR_RULES,
    "IT": _IT_RULES,
    "NL": _NL_RULES,
    "PL": _PL_RULES,
    "CZ": _CZ_RULES,
    "DK": _DK_RULES,
    "SE": _SE_RULES,
}


def is_supported(country: str) -> bool:
    return country in SUPPORTED_COUNTRIES


def evaluate_line(country: str, category: str, line_index: int, vat_amount: Decimal, currency: str) -> LineDecision:
    """Return the decision for one invoice line."""
    if country not in COUNTRY_RULES:
        raise ValueError(f"Unsupported country: {country}")
    rule = COUNTRY_RULES[country].get(category)
    if rule is None:
        rule = CategoryRule(NO_SHARE, f"No rule for category {category} in {country}.", DIRECTIVE_SOURCE)
    refundable = Money(vat_amount * rule.refundable_share, currency).rounded()
    return LineDecision(
        line_index=line_index,
        category=category,
        eligible=rule.eligible,
        refundable_share=rule.refundable_share,
        refundable_vat=refundable,
        reason=f"{rule.reason} Source: {rule.source}",
    )
