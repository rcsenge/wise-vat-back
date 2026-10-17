"""SQLModel tables. Import every model here so init_db() registers them."""
from app.models.account import Account
from app.models.invoice_record import InvoiceRecord
from app.models.transaction import Transaction
from app.models.user import User

__all__ = ["Account", "InvoiceRecord", "Transaction", "User"]
