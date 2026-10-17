"""The original uploaded invoice document. The claim package attaches it as the invoice copy."""
from sqlalchemy import Column, LargeBinary
from sqlmodel import Field, SQLModel


class InvoiceDocument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="invoicerecord.id", index=True)
    filename: str = Field(max_length=255)
    media_type: str = Field(max_length=64)
    content: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
