"""Test helpers. Load invoices and compare outcomes against golden sidecars."""
import json
from decimal import Decimal
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SEED_ROOT = BACKEND / "seed"
INVOICES_DIR = SEED_ROOT / "invoices"
SAMPLE_INVOICES_DIR = SEED_ROOT / "sample_invoices"
GOLDEN_ROOT = SEED_ROOT / "golden"
CENT = Decimal("0.01")


def load_invoice(name: str) -> dict:
    return json.loads((INVOICES_DIR / name).read_text(encoding="utf-8"))


def golden_cases() -> list[dict]:
    """Return every golden case as name, invoice path, and golden path."""
    cases: list[dict] = []
    for sidecar in sorted(GOLDEN_ROOT.glob("*/*.golden.json")):
        invoice = SEED_ROOT / sidecar.parent.name / sidecar.name.replace(".golden.json", ".json")
        cases.append({"name": sidecar.stem, "invoice": invoice, "golden": sidecar})
    return cases


def compare_expected(result: dict, expected: dict) -> list[str]:
    """Return the mismatch reasons between a flow result and a golden sidecar."""
    problems: list[str] = []
    if result.get("status") != expected.get("status"):
        problems.append(f"status {result.get('status')!r} != expected {expected.get('status')!r}")

    got_by_country = {total["country"]: total for total in result.get("country_totals", [])}
    expected_by_country = {total["country"]: total for total in expected.get("perCountry", [])}
    for country in sorted(set(got_by_country) | set(expected_by_country)):
        got = got_by_country.get(country)
        want = expected_by_country.get(country)
        if got is None or want is None:
            source = "result" if got else "expected"
            problems.append(f"country {country} present in {source} only")
            continue
        got_amount = Decimal(str(got["refundable_vat_total"])).quantize(CENT)
        want_amount = Decimal(str(want["refundableVatTotal"])).quantize(CENT)
        if got_amount != want_amount:
            problems.append(
                f"country {country} refundable_vat_total {got_amount} != expected {want_amount}"
            )
        if got["currency"] != want["currency"]:
            problems.append(f"country {country} currency {got['currency']} != expected {want['currency']}")
        if got["eligible_line_count"] != want["eligibleLineCount"]:
            problems.append(
                f"country {country} eligible_line_count {got['eligible_line_count']} != expected {want['eligibleLineCount']}"
            )
    return problems
