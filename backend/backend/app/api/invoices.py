"""Invoice intake, receipts list and claim summary endpoints. Keep thin: call the service."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError
from sqlmodel import Session

from app.db import get_session
from app.integrations.extraction import MAX_DOCUMENT_BYTES, DocumentError, extract_invoice
from app.schemas.invoice_flow import (
    MAX_IMAGE_DATA_URL_LENGTH,
    ClaimsSummary,
    InvoiceResult,
    InvoiceSubmission,
    ReceiptView,
)
from app.services import invoice_flow

router = APIRouter(tags=["invoices"])


@router.post("/invoices", response_model=InvoiceResult)
def submit_invoice(submission: InvoiceSubmission, session: Session = Depends(get_session)) -> InvoiceResult:
    return invoice_flow.submit_invoice(session, submission)


@router.post("/invoices/upload", response_model=InvoiceResult)
def upload_invoice(
    document: UploadFile = File(description="The invoice document. The demo accepts an ExtractedInvoice JSON file."),
    image_data_url: str | None = Form(default=None, max_length=MAX_IMAGE_DATA_URL_LENGTH),
    session: Session = Depends(get_session),
) -> InvoiceResult:
    """The frontend entry point. The AI extraction replaces the JSON step later."""
    content = document.file.read(MAX_DOCUMENT_BYTES + 1)
    try:
        invoice = extract_invoice(content, document.content_type, document.filename)
        submission = InvoiceSubmission.model_validate(
            {**invoice.model_dump(mode="json", by_alias=True), "imageDataUrl": image_data_url}
        )
    except DocumentError as error:
        raise HTTPException(status_code=error.status_code, detail={"reasons": error.reasons}) from error
    except ValidationError as error:
        raise HTTPException(status_code=422, detail={"reasons": [item["msg"] for item in error.errors()]}) from error
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
