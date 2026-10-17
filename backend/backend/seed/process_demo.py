"""Demo script. Seed the database, process every hardcoded invoice, print the claims.

Run: make demo-process
"""
import json

from sqlmodel import Session

from app.db import engine
from app.services import invoice_flow
from seed.seed import run as seed_run


def run() -> None:
    seed_run()
    with Session(engine) as session:
        claims = invoice_flow.compute_claims(session)
        print(json.dumps(claims.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    run()
