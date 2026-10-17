"""Invoice intake, receipts list and claim summary endpoints. Keep thin: call the service."""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.schemas.invoice_flow import ClaimsSummary, InvoiceResult, InvoiceSubmission, ReceiptView
from app.services import invoice_flow

router = APIRouter(tags=["invoices"])


@router.post("/invoices", response_model=InvoiceResult)
def submit_invoice(submission: InvoiceSubmission, session: Session = Depends(get_session)) -> InvoiceResult:
    return invoice_flow.submit_invoice(session, submission)


@router.get("/receipts", response_model=list[ReceiptView])
def list_receipts(
    limit: int = Query(default=invoice_flow.DEFAULT_RECEIPT_LIMIT, ge=1, le=invoice_flow.DEFAULT_RECEIPT_LIMIT),
    session: Session = Depends(get_session),
) -> list[ReceiptView]:
    return invoice_flow.list_receipts(session, limit)


@router.get("/claims", response_model=ClaimsSummary)
def get_claims(session: Session = Depends(get_session)) -> ClaimsSummary:
    return invoice_flow.compute_claims(session)
