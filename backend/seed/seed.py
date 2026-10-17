"""Create the database tables and load the mock demo data.

The demo data matches the seed invoices in seed/invoices/. The script drops the
tables first so a schema change never leaves a stale database behind.
The card transactions stay unclaimed. Upload a seed invoice in the frontend to claim one.

The sample invoices in seed/sample_invoices/ fill the demo with many countries.
Each sample gets a matching card transaction. One sample has no transaction on purpose.

Run: python -m seed.seed
"""
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session, SQLModel, select

from app.db import engine, init_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.invoice_flow import InvoiceSubmission
from app.services.invoice_flow import iter_seed_invoices, submit_invoice

SAMPLE_INVOICES_DIR = Path(__file__).resolve().parent / "sample_invoices"
# This sample shows the rejection when no card transaction matches the invoice.
SAMPLE_INVOICE_NUMBERS_WITHOUT_TRANSACTION: frozenset[str] = frozenset({"IT-2026-1444"})


def paid_on(day: date) -> datetime:
    """Return the card payment time on the invoice issue date (UTC noon)."""
    return datetime.combine(day, time(hour=12), tzinfo=timezone.utc)


def sample_transactions(samples: list[InvoiceSubmission], account_ids: dict[str, int]) -> list[Transaction]:
    """Return one card transaction per sample invoice with the same total, currency and country."""
    return [
        Transaction(
            account_id=account_ids[sample.currency],
            amount=sample.totals.gross_amount,
            currency=sample.currency,
            country=sample.supplier.address.country_code,
            merchant=sample.supplier.name,
            kind="card",
            created_at=paid_on(sample.issue_date),
        )
        for sample in samples
        if sample.invoice_number not in SAMPLE_INVOICE_NUMBERS_WITHOUT_TRANSACTION
    ]


def run(submit_invoices: bool = False) -> None:
    import app.models  # noqa: F401  (register tables)

    SQLModel.metadata.drop_all(engine)
    init_db()

    with Session(engine) as session:
        user = User(name="Példa Tech Kft.")
        session.add(user)
        session.flush()

        eur_account = Account(user_id=user.id, currency="EUR", balance=Decimal("5000.00"))
        pln_account = Account(user_id=user.id, currency="PLN", balance=Decimal("15000.00"))
        session.add(eur_account)
        session.add(pln_account)
        for currency in ("CZK", "DKK", "SEK"):
            session.add(Account(user_id=user.id, currency=currency, balance=Decimal("50000.00")))
        session.flush()
        account_ids = {account.currency: account.id for account in session.exec(select(Account)).all()}
        samples = iter_seed_invoices(SAMPLE_INVOICES_DIR)

        transactions = [
            Transaction(account_id=eur_account.id, amount=Decimal("261.00"), currency="EUR", country="AT", merchant="Hotel Ringstrasse GmbH", kind="card", created_at=paid_on(date(2026, 9, 17))),
            Transaction(account_id=eur_account.id, amount=Decimal("32.10"), currency="EUR", country="DE", merchant="Taxi Beispiel", kind="card", created_at=paid_on(date(2026, 10, 8))),
            Transaction(account_id=eur_account.id, amount=Decimal("160.50"), currency="EUR", country="DE", merchant="Hotel München Mitte GmbH", kind="card", created_at=paid_on(date(2026, 9, 28))),
            Transaction(account_id=pln_account.id, amount=Decimal("368.40"), currency="PLN", country="PL", merchant="Restauracja Przykładowa Sp. z o.o.", kind="card", created_at=paid_on(date(2026, 10, 2))),
            # The sample PDFs in seed/documents/ match these two transactions.
            Transaction(account_id=eur_account.id, amount=Decimal("292.50"), currency="EUR", country="DE", merchant="Hotel Spreeufer Berlin GmbH", kind="card", created_at=paid_on(date(2026, 10, 14))),
            Transaction(account_id=eur_account.id, amount=Decimal("47.40"), currency="EUR", country="AT", merchant="Gasthaus Zum Goldenen Hirschen", kind="card", created_at=paid_on(date(2026, 10, 11))),
        ]
        transactions.extend(sample_transactions(samples, account_ids))
        for transaction in transactions:
            session.add(transaction)

        session.commit()

        if submit_invoices:
            for invoice in iter_seed_invoices() + samples:
                submit_invoice(session, invoice)

    print("Database seeded.")


if __name__ == "__main__":
    run()
