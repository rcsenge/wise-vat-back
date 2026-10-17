"""Shared fixtures. Provide an app test client with an in-memory database."""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from seed.seed import paid_on

BACKEND = Path(__file__).resolve().parents[1]
INVOICES_DIR = BACKEND / "seed" / "invoices"


def load_invoice(name: str) -> dict:
    return json.loads((INVOICES_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    import app.models as app_models  # noqa: F401  (register tables)

    SQLModel.metadata.create_all(engine)

    from app.models.account import Account
    from app.models.transaction import Transaction
    from app.models.user import User

    with Session(engine) as session:
        user = User(name="Példa Tech Kft.")
        session.add(user)
        session.flush()
        eur = Account(user_id=user.id, currency="EUR", balance=Decimal("5000.00"))
        pln = Account(user_id=user.id, currency="PLN", balance=Decimal("15000.00"))
        session.add(eur)
        session.add(pln)
        session.flush()
        transactions = [
            Transaction(account_id=eur.id, amount=Decimal("261.00"), currency="EUR", country="AT", merchant="Hotel Ringstrasse GmbH", kind="card", created_at=paid_on(date(2026, 9, 17))),
            Transaction(account_id=eur.id, amount=Decimal("32.10"), currency="EUR", country="DE", merchant="Taxi Beispiel", kind="card", created_at=paid_on(date(2026, 10, 8))),
            Transaction(account_id=eur.id, amount=Decimal("160.50"), currency="EUR", country="DE", merchant="Hotel München Mitte GmbH", kind="card", created_at=paid_on(date(2026, 9, 28))),
            Transaction(account_id=pln.id, amount=Decimal("368.40"), currency="PLN", country="PL", merchant="Restauracja Przykładowa Sp. z o.o.", kind="card", created_at=paid_on(date(2026, 10, 2))),
            Transaction(account_id=eur.id, amount=Decimal("292.50"), currency="EUR", country="DE", merchant="Hotel Spreeufer Berlin GmbH", kind="card", created_at=paid_on(date(2026, 10, 14))),
            Transaction(account_id=eur.id, amount=Decimal("47.40"), currency="EUR", country="AT", merchant="Gasthaus Zum Goldenen Hirschen", kind="card", created_at=paid_on(date(2026, 10, 11))),
            # VAT back is not supported in the United Kingdom.
            Transaction(account_id=eur.id, amount=Decimal("120.00"), currency="GBP", country="GB", merchant="London Hotel Ltd", kind="card", created_at=paid_on(date(2026, 10, 2))),
        ]
        for transaction in transactions:
            session.add(transaction)
        session.commit()
    return engine


@pytest.fixture
def client(engine):
    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def stored_seed_invoices(engine):
    """Store every seed invoice through the service, like the seed script."""
    from app.services.invoice_flow import iter_seed_invoices, submit_invoice

    with Session(engine) as session:
        for invoice in iter_seed_invoices():
            submit_invoice(session, invoice)
