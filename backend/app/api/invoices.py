"""Invoice intake, receipts list and claim summary endpoints. Keep thin: call the service."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from pydantic import ValidationError
from sqlmodel import Session

from app.db import get_session
from app.integrations.extraction import MAX_DOCUMENT_BYTES, DocumentError, detect_media_type, extract_invoice
from app.integrations.ollama_reader import InvoiceReader, get_invoice_reader
from app.schemas.invoice_flow import (
    MAX_IMAGE_DATA_URL_LENGTH,
    ClaimsSummary,
    InvoiceResult,
    InvoiceSubmission,
    ReceiptView,
)
from app.services import claim_package, invoice_flow

router = APIRouter(tags=["invoices"])


@router.post("/invoices", response_model=InvoiceResult)
def submit_invoice(submission: InvoiceSubmission, session: Session = Depends(get_session)) -> InvoiceResult:
    return invoice_flow.submit_invoice(session, submission)


@router.post("/invoices/upload", response_model=InvoiceResult)
def upload_invoice(
    document: UploadFile = File(description="The invoice as a PDF or a photo."),
    image_data_url: str | None = Form(default=None, max_length=MAX_IMAGE_DATA_URL_LENGTH),
    session: Session = Depends(get_session),
    read_with_ai: InvoiceReader = Depends(get_invoice_reader),
) -> InvoiceResult:
    """The frontend entry point. The local AI reads the PDF or the photo."""
    content = document.file.read(MAX_DOCUMENT_BYTES + 1)
    try:
        invoice = extract_invoice(content, read_with_ai)
        submission = InvoiceSubmission.model_validate(
            {**invoice.model_dump(mode="json", by_alias=True), "imageDataUrl": image_data_url}
        )
    except DocumentError as error:
        raise HTTPException(status_code=error.status_code, detail={"reasons": error.reasons}) from error
    except ValidationError as error:
        raise HTTPException(status_code=422, detail={"reasons": [item["msg"] for item in error.errors()]}) from error
    original = invoice_flow.OriginalDocument(
        filename=document.filename or "invoice",
        media_type=detect_media_type(content) or "application/octet-stream",
        content=content,
    )
    return invoice_flow.submit_invoice(session, submission, original)


@router.get("/receipts", response_model=list[ReceiptView])
def list_receipts(
    limit: int = Query(default=invoice_flow.DEFAULT_RECEIPT_LIMIT, ge=1, le=invoice_flow.DEFAULT_RECEIPT_LIMIT),
    session: Session = Depends(get_session),
) -> list[ReceiptView]:
    return invoice_flow.list_receipts(session, limit)


@router.get("/claims", response_model=ClaimsSummary)
def get_claims(session: Session = Depends(get_session)) -> ClaimsSummary:
    return invoice_flow.compute_claims(session)


@router.get(
    "/claims/package",
    response_class=Response,
    responses={200: {"content": {"application/zip": {}}, "description": "The claim package as a ZIP file."}},
)
def download_claim_package(
    country: str = Query(pattern=r"^[A-Z]{2}$", description="The Member State of refund, for example AT."),
    year: int = Query(ge=2000, le=2100, description="The refund period: the calendar year of the invoices."),
    session: Session = Depends(get_session),
) -> Response:
    """Return the package that the accountant needs for the refund application of one country and year."""
    try:
        package = claim_package.build_claim_package(session, country, year)
    except claim_package.PackageError as error:
        raise HTTPException(status_code=error.status_code, detail={"reasons": error.reasons}) from error
    return Response(
        content=package.content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{package.filename}"'},
    )
