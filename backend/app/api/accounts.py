"""UNWIRED. The live flow never calls this module. See REPO-FINDINGS.md item 2.

Accounts / balances / transactions. Keep thin: call services, return schemas.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
def list_accounts() -> list[dict]:
    # TODO: load accounts + multi-currency balances from DB
    return []


@router.get("/{account_id}/transactions")
def list_transactions(account_id: int) -> list[dict]:
    # TODO: load transactions for account
    return []
