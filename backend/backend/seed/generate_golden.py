"""Generate the golden outcome sidecars for every invoice JSON case.

For each invoice in seed/invoices/ and seed/sample_invoices/ the script runs the full
flow in a fresh in-memory database with one matching card transaction. It writes the
outcome to a *.golden.json sidecar next to the invoice. The golden corpus test compares
every future run against these frozen outcomes.

The sidecars are the ground truth of the demo. Review them by hand after a rule change.

Run: uv run python -m seed.generate_golden
"""
import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (register tables)
from app.models.account import Account
from app.models.transaction import Transaction  # noqa: F401  (registered model)
from app.models.user import User
from app.schemas.invoice_flow import InvoiceSubmission
from app.services.invoice_flow import submit_invoice
from seed.seed import SAMPLE_INVOICES_DIR, sample_transactions

BACKEND = Path(__file__).resolve().parents[1]
INVOICES_DIR = BACKEND / "seed" / "invoices"
GOLDEN_ROOT = BACKEND / "seed" / "golden"
CENT = Decimal("0.01")


def _fresh_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _seed_case(session: Session, invoice: InvoiceSubmission) -> None:
    user = User(name="Példa Tech Kft.")
    session.add(user)
    session.flush()
    account = Account(user_id=user.id, currency=invoice.currency, balance=Decimal("50000.00"))
    session.add(account)
    session.flush()
    for transaction in sample_transactions([invoice], {invoice.currency: account.id}):
        session.add(transaction)
    session.commit()


def compute_outcome(invoice: InvoiceSubmission) -> dict:
    with _fresh_session() as session:
        _seed_case(session, invoice)
        result = submit_invoice(session, invoice)
    total_sum = sum((total.refundable_vat_total for total in result.country_totals), Decimal("0"))
    return {
        "status": result.status,
        "refundableVatTotal": str(total_sum.quantize(CENT)),
        "eligibleLineCount": sum(total.eligible_line_count for total in result.country_totals),
        "perCountry": [
            {
                "country": total.country,
                "currency": total.currency,
                "refundableVatTotal": str(total.refundable_vat_total.quantize(CENT)),
                "eligibleLineCount": total.eligible_line_count,
            }
            for total in result.country_totals
        ],
    }


def generate(directory: Path) -> int:
    """Write one golden sidecar per invoice in the directory to the mirrored golden folder."""
    golden_dir = GOLDEN_ROOT / directory.name
    golden_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for path in sorted(directory.glob("*.json")):
        submission = InvoiceSubmission.model_validate_json(path.read_text(encoding="utf-8"))
        outcome = compute_outcome(submission)
        sidecar = golden_dir / f"{path.stem}.golden.json"
        sidecar.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        written += 1
    return written


def run() -> None:
    count = generate(INVOICES_DIR) + generate(SAMPLE_INVOICES_DIR)
    print(f"Wrote {count} golden sidecars.")


if __name__ == "__main__":
    run()
