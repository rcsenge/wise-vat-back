"""Create the database tables and load the mock demo data.

The demo data matches the seed invoices in seed/invoices/. The script drops the
tables first so a schema change never leaves a stale database behind.
The card transactions stay unclaimed. Upload a seed invoice in the frontend to claim one.

Run: python -m seed.seed
"""
from decimal import Decimal

from sqlmodel import Session, SQLModel

from app.db import engine, init_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.services.invoice_flow import iter_seed_invoices, submit_invoice


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
        session.flush()

        transactions = [
            Transaction(account_id=eur_account.id, amount=Decimal("261.00"), currency="EUR", country="AT", merchant="Hotel Ringstrasse GmbH", kind="card"),
            Transaction(account_id=eur_account.id, amount=Decimal("32.10"), currency="EUR", country="DE", merchant="Taxi Beispiel", kind="card"),
            Transaction(account_id=eur_account.id, amount=Decimal("160.50"), currency="EUR", country="DE", merchant="Hotel München Mitte GmbH", kind="card"),
            Transaction(account_id=pln_account.id, amount=Decimal("368.40"), currency="PLN", country="PL", merchant="Restauracja Przykładowa Sp. z o.o.", kind="card"),
        ]
        for transaction in transactions:
            session.add(transaction)

        session.commit()

        if submit_invoices:
            for invoice in iter_seed_invoices():
                submit_invoice(session, invoice)

    print("Database seeded.")


if __name__ == "__main__":
    run()
