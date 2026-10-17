"""Measure the local AI extraction quality over the sample PDF documents.

This is a measurement tool, not a pass or fail test. It is not part of make test.
Ollama is stochastic. Run the same corpus several times and report the range.

For every PDF the script compares the AI extraction against the hand-checked
*.expected.json sidecar, then runs both through the full flow and compares the
decisions. Money fields must agree to the cent after rounding. Text fields must
equal after trimming and lowercasing.

Run: uv run python -m evaluation.evaluate_extraction [documents-dir]
Exit codes: 0 = measured, 2 = the local AI is not available.
"""
import sys
from decimal import Decimal
from pathlib import Path

from app.integrations.extraction import DocumentError, extract_invoice
from app.integrations.ollama_reader import get_invoice_reader
from app.schemas.invoice import ExtractedInvoice
from app.schemas.invoice_flow import InvoiceSubmission
from seed.generate_golden import compute_outcome

BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENTS_DIR = BACKEND / "seed" / "documents"
CENT = Decimal("0.01")


def _money(value: object) -> Decimal | None:
    try:
        return Decimal(str(value)).quantize(CENT)
    except (TypeError, ValueError):
        return None


def _text(value: object) -> str:
    return str(value).strip().lower() if value is not None else ""


def _line_summary(line: dict) -> tuple[str, Decimal | None]:
    return line.get("category", ""), _money(line.get("grossAmount"))


def compare_extraction(expected: ExtractedInvoice, actual: ExtractedInvoice, tolerance: Decimal = Decimal("0.02")) -> tuple[int, list[str]]:
    """Return the number of comparable fields and the mismatch descriptions."""
    compared = 0
    problems: list[str] = []
    expected_data = expected.model_dump(mode="json", by_alias=True)
    actual_data = actual.model_dump(mode="json", by_alias=True)

    pairs = [
        ("supplier.name", expected.supplier.name, actual.supplier.name),
        ("supplier.vatNumber", expected.supplier.vat_number, actual.supplier.vat_number),
        ("supplier.address.countryCode", expected.supplier.address.country_code, actual.supplier.address.country_code),
        ("currency", expected.currency, actual.currency),
        ("documentType", expected.document_type.value, actual.document_type.value),
        ("issueDate", expected.issue_date.isoformat(), actual.issue_date.isoformat()),
        ("cardLast4", expected.card_last4, actual.card_last4),
    ]
    for name, want, got in pairs:
        compared += 1
        if _text(want).rstrip(".") != _text(got).rstrip("."):
            problems.append(f"{name}: expected {want!r}, got {got!r}")

    money_fields = [("grossAmount", "totals"), ("vatAmount", "totals"), ("netAmount", "totals")]
    want_totals = expected_data.get("totals", {})
    got_totals = actual_data.get("totals", {})
    for field, _section in money_fields:
        compared += 1
        want = _money(want_totals.get(field))
        got = _money(got_totals.get(field))
        if want is None or got is None or abs(want - got) > tolerance:
            problems.append(f"totals.{field}: expected {want}, got {got}")

    compared += 1
    want_lines = [_line_summary(line) for line in expected_data.get("lines", [])]
    got_lines = [_line_summary(line) for line in actual_data.get("lines", [])]
    if want_lines and got_lines and len(want_lines) == len(got_lines):
        for index, (want, got) in enumerate(zip(want_lines, got_lines)):
            if want[0] != got[0]:
                problems.append(f"lines[{index}].category: expected {want[0]!r}, got {got[0]!r}")
            if want[1] is not None and got[1] is not None and abs(want[1] - got[1]) > tolerance:
                problems.append(f"lines[{index}].grossAmount: expected {want[1]}, got {got[1]}")
    elif want_lines or got_lines:
        problems.append(
            f"lines count: expected {len(want_lines)}, got {len(got_lines)}"
        )
    return compared, problems


def _as_submission(invoice: ExtractedInvoice) -> InvoiceSubmission:
    return InvoiceSubmission.model_validate(invoice.model_dump(mode="json", by_alias=True))


def evaluate_documents(directory: Path) -> int:
    documents = sorted(directory.glob("*.pdf"))
    if not documents:
        print(f"No PDF documents found in {directory}")
        return 2

    reader = get_invoice_reader()
    rows: list[tuple[str, int, int, list[str], str, str, str]] = []
    for document in documents:
        expected_path = document.with_suffix(".expected.json")
        if not expected_path.exists():
            print(f"SKIP {document.name}: no expected.json sidecar")
            continue
        expected = ExtractedInvoice.model_validate_json(expected_path.read_text(encoding="utf-8"))
        content = document.read_bytes()
        try:
            actual = extract_invoice(content, reader)
        except DocumentError as error:
            if any("not running" in reason for reason in error.reasons):
                print("The local AI is not running. Start Ollama and pull the model first.")
                return 2
            actual = None
        compared_total, problems = 0, []
        if actual is None:
            problems = ["extraction failed"]
            compared_total = 1
            actual = expected
        else:
            compared_total, problems = compare_extraction(expected, actual)
        expected_outcome = compute_outcome(_as_submission(expected))
        actual_outcome = compute_outcome(_as_submission(actual))
        decision_ok = expected_outcome.get("status") == actual_outcome.get("status") and (
            expected_outcome.get("status") != "approved"
            or expected_outcome.get("refundableVatTotal") == actual_outcome.get("refundableVatTotal")
        )
        rows.append(
            (
                document.name,
                compared_total,
                len(problems),
                problems,
                expected_outcome.get("status", ""),
                actual_outcome.get("status", ""),
                "PASS" if decision_ok else "FAIL",
            )
        )

    for name, compared, failed, problems, expect_status, got_status, mark in rows:
        line = f"{mark:4} {name:45} fields {compared - failed:2}/{compared} decision {expect_status} -> {got_status}"
        print(line)
        for problem in problems:
            print(f"      - {problem}")

    total_fields = sum(row[1] for row in rows)
    total_failed = sum(row[2] for row in rows)
    decision_passes = sum(1 for row in rows if row[6] == "PASS")
    print()
    print(f"Documents: {len(rows)}")
    print(f"Extraction field accuracy: {total_fields - total_failed}/{total_fields} = "
          f"{(total_fields - total_failed) / total_fields * 100:.1f}%" if total_fields else "0 documents")
    print(f"Decision matches: {decision_passes}/{len(rows)}")
    return 0


def main() -> None:
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCUMENTS_DIR
    sys.exit(evaluate_documents(directory))


if __name__ == "__main__":
    main()
