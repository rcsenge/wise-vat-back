"""Golden corpus: every invoice case must match its frozen golden outcome.

The corpus reads the invoice JSON files in seed/invoices/ and seed/sample_invoices/.
Every invoice has a sidecar *.golden.json with the expected outcome. Each case runs in
a fresh in-memory database with one matching card transaction. A case passes when the
status, the per-country refundable VAT, and the eligible line count match the sidecar.

Regenerate the sidecars with: uv run python -m seed.generate_golden
Review the sidecars by hand after a rule change.
"""
import json
from contextlib import contextmanager
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.models.account import Account
from app.models.user import User
from app.schemas.invoice_flow import InvoiceSubmission
from seed.seed import sample_transactions
from tests.helpers import compare_expected, golden_cases

CASES = golden_cases()


@contextmanager
def case_client(invoice: dict):
    """Provide an app test client with one fresh database and one matching transaction."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    import app.models as app_models  # noqa: F401  (register tables)

    SQLModel.metadata.create_all(engine)
    submission = InvoiceSubmission.model_validate(invoice)
    with Session(engine) as session:
        user = User(name="Példa Tech Kft.")
        session.add(user)
        session.flush()
        account = Account(user_id=user.id, currency=invoice["currency"], balance=Decimal("50000.00"))
        session.add(account)
        session.flush()
        for transaction in sample_transactions([submission], {invoice["currency"]: account.id}):
            session.add(transaction)
        session.commit()

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_golden_case(case):
    invoice = json.loads(case["invoice"].read_text(encoding="utf-8"))
    expected = json.loads(case["golden"].read_text(encoding="utf-8"))
    with case_client(invoice) as client:
        response = client.post("/invoices", json=invoice)
    assert response.status_code == 200
    problems = compare_expected(response.json(), expected)
    assert not problems, "; ".join(problems)


def test_corpus_has_enough_cases():
    """Keep the corpus near the target size so coverage stays meaningful."""
    assert len(CASES) >= 40, f"The golden corpus has only {len(CASES)} cases."
