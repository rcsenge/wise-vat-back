"""Build the mock database. It fills the frontend with demo data for every supported country.

Each country gets five hardcoded merchants. The generator picks the amounts and the dates.
A fixed random seed keeps the output identical on every run.
Every invoice runs through the real invoice flow. The receipts and the claims stay realistic.
Some merchants carry a defect on purpose. The frontend then shows a rejected receipt.

Run: DATABASE_URL=sqlite:///./mock.db python -m seed.mock_db
"""
import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, col, select

from app.db import engine as default_engine
from app.domain import vat_rules
from app.models.account import Account
from app.models.invoice_record import InvoiceRecord
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.invoice_flow import InvoiceSubmission
from app.services.invoice_flow import submit_invoice
from seed.seed import paid_on

MOCK_RANDOM_SEED = 2026
MOCK_HISTORY_DAYS = 60
CUSTOMER_NAME = "Példa Tech Kft."
CUSTOMER_VAT_NUMBER = "HU12345678"
CARD_LAST4 = "4821"
ACCOUNT_BALANCE = Decimal("50000.00")
_CENT = Decimal("0.01")

# A defect makes the invoice fail. "no_vat_number" fails validation. "no_transaction" fails the match.
Defect = Literal["no_vat_number", "no_transaction"]


@dataclass(frozen=True)
class MockMerchant:
    name: str
    city: str
    category: str
    description: str
    vat_rate: Decimal
    defect: Defect | None = None


@dataclass(frozen=True)
class MockCountry:
    code: str
    currency: str
    vat_prefix: str
    vat_digits: int
    vat_suffix: str
    # The amount scale converts a EUR-sized net amount into the local currency.
    amount_scale: Decimal
    merchants: tuple[MockMerchant, ...]


def _merchant(name: str, city: str, category: str, description: str, vat_rate: str, defect: Defect | None = None) -> MockMerchant:
    return MockMerchant(name, city, category, description, Decimal(vat_rate), defect)


MOCK_COUNTRIES: tuple[MockCountry, ...] = (
    MockCountry("AT", "EUR", "ATU", 8, "", Decimal("1"), (
        _merchant("Hotel Stephansplatz GmbH", "Wien", "ACCOMMODATION", "Doppelzimmer, 2 Nächte", "10"),
        _merchant("OMV Tankstelle Innsbruck", "Innsbruck", "FUEL", "Diesel", "20"),
        _merchant("ÖBB-Personenverkehr AG", "Wien", "TRAVEL", "Railjet Wien - Salzburg", "10"),
        _merchant("Messe Wien Exhibition GmbH", "Wien", "FAIR_ADMISSION", "Fachbesucher Ticket", "20"),
        _merchant("Café Mozart Salzburg", "Salzburg", "FOOD_AND_DRINK", "Geschäftsessen", "10", "no_vat_number"),
    )),
    MockCountry("DE", "EUR", "DE", 9, "", Decimal("1"), (
        _merchant("Hotel Alexanderplatz Berlin GmbH", "Berlin", "ACCOMMODATION", "Einzelzimmer, 3 Nächte", "7"),
        _merchant("Deutsche Bahn Fernverkehr AG", "Frankfurt am Main", "TRAVEL", "ICE Frankfurt - Hamburg", "7"),
        _merchant("Sixt GmbH & Co. Autovermietung KG", "München", "VEHICLE_HIRE", "Mietwagen, 2 Tage", "19"),
        _merchant("Shell Tankstelle Köln", "Köln", "FUEL", "Super E10", "19"),
        _merchant("Brauhaus Sion Köln", "Köln", "FOOD_AND_DRINK", "Abendessen", "19"),
    )),
    MockCountry("FR", "EUR", "FR", 11, "", Decimal("1"), (
        _merchant("Hôtel Le Marais SAS", "Paris", "ACCOMMODATION", "Chambre double, 2 nuits", "10"),
        _merchant("SNCF Voyageurs", "Lyon", "TRAVEL", "TGV Lyon - Paris", "10"),
        _merchant("Sanef Autoroute A1", "Lille", "ROAD_TOLL", "Péage A1", "20"),
        _merchant("TotalEnergies Marseille", "Marseille", "FUEL", "Gazole", "20"),
        _merchant("Brasserie Bellecour", "Lyon", "FOOD_AND_DRINK", "Déjeuner d'affaires", "10"),
    )),
    MockCountry("IT", "EUR", "IT", 11, "", Decimal("1"), (
        _merchant("Hotel Duomo Milano S.r.l.", "Milano", "ACCOMMODATION", "Camera singola, 2 notti", "10"),
        _merchant("Trenitalia S.p.A.", "Roma", "TRAVEL", "Frecciarossa Roma - Milano", "10"),
        _merchant("Autostrade per l'Italia", "Bologna", "ROAD_TOLL", "Pedaggio A1", "22"),
        _merchant("Fiera Milano S.p.A.", "Milano", "FAIR_ADMISSION", "Biglietto fiera", "22"),
        _merchant("Trattoria da Enzo", "Roma", "FOOD_AND_DRINK", "Cena di lavoro", "10", "no_transaction"),
    )),
    MockCountry("NL", "EUR", "NL", 9, "B01", Decimal("1"), (
        _merchant("Hotel Damrak Amsterdam B.V.", "Amsterdam", "ACCOMMODATION", "Tweepersoonskamer, 2 nachten", "9"),
        _merchant("NS Reizigers B.V.", "Utrecht", "TRAVEL", "Intercity Utrecht - Rotterdam", "9"),
        _merchant("RAI Amsterdam B.V.", "Amsterdam", "FAIR_ADMISSION", "Beursticket", "21"),
        _merchant("Shell Station Den Haag", "Den Haag", "FUEL", "Euro 95", "21"),
        _merchant("Restaurant De Haven", "Rotterdam", "FOOD_AND_DRINK", "Zakelijk diner", "9"),
    )),
    MockCountry("PL", "PLN", "PL", 10, "", Decimal("4.3"), (
        _merchant("Hotel Stare Miasto Sp. z o.o.", "Kraków", "ACCOMMODATION", "Pokój jednoosobowy, 2 noce", "8"),
        _merchant("PKP Intercity S.A.", "Warszawa", "TRAVEL", "Pendolino Warszawa - Gdańsk", "8"),
        _merchant("ORLEN Stacja Gdańsk", "Gdańsk", "FUEL", "Olej napędowy", "23"),
        _merchant("Autostrada Wielkopolska S.A.", "Poznań", "ROAD_TOLL", "Opłata za przejazd A2", "23"),
        _merchant("Restauracja Pod Wawelem", "Kraków", "FOOD_AND_DRINK", "Obiad służbowy", "8"),
    )),
    MockCountry("CZ", "CZK", "CZ", 8, "", Decimal("25"), (
        _merchant("Hotel Václavské náměstí s.r.o.", "Praha", "ACCOMMODATION", "Dvoulůžkový pokoj, 2 noci", "12"),
        _merchant("České dráhy, a.s.", "Brno", "TRAVEL", "Jízdenka Brno - Praha", "12"),
        _merchant("Benzina Ostrava", "Ostrava", "FUEL", "Natural 95", "21"),
        _merchant("Veletrhy Brno, a.s.", "Brno", "FAIR_ADMISSION", "Vstupenka na veletrh", "21"),
        _merchant("Restaurace U Fleků", "Praha", "FOOD_AND_DRINK", "Pracovní večeře", "12"),
    )),
    MockCountry("DK", "DKK", "DK", 8, "", Decimal("7.46"), (
        _merchant("Hotel Nyhavn ApS", "København", "ACCOMMODATION", "Dobbeltværelse, 2 nætter", "25"),
        _merchant("DSB", "Aarhus", "TRAVEL", "Togbillet Aarhus - København", "25"),
        _merchant("Circle K Odense", "Odense", "FUEL", "Diesel", "25"),
        _merchant("Bella Center Copenhagen A/S", "København", "FAIR_ADMISSION", "Messebillet", "25"),
        _merchant("Restaurant Havnen", "Aarhus", "FOOD_AND_DRINK", "Forretningsmiddag", "25", "no_vat_number"),
    )),
    MockCountry("SE", "SEK", "SE", 10, "01", Decimal("11"), (
        _merchant("Hotel Gamla Stan AB", "Stockholm", "ACCOMMODATION", "Enkelrum, 2 nätter", "12"),
        _merchant("SJ AB", "Göteborg", "TRAVEL", "Tågbiljett Göteborg - Stockholm", "6"),
        _merchant("Preem Malmö", "Malmö", "FUEL", "Diesel", "25"),
        _merchant("Stockholmsmässan AB", "Stockholm", "FAIR_ADMISSION", "Mässbiljett", "25"),
        _merchant("Restaurang Kajen", "Göteborg", "FOOD_AND_DRINK", "Affärsmiddag", "12"),
    )),
)


@dataclass(frozen=True)
class MockReceipt:
    country: MockCountry
    merchant: MockMerchant
    invoice: InvoiceSubmission


def _vat_number(country: MockCountry, generator: random.Random) -> str:
    digits = "".join(str(generator.randint(0, 9)) for _ in range(country.vat_digits))
    return f"{country.vat_prefix}{digits}{country.vat_suffix}"


def _money(value: Decimal) -> str:
    return str(value.quantize(_CENT, rounding=ROUND_HALF_UP))


def build_invoice(country: MockCountry, merchant: MockMerchant, index: int, issue_date: date, generator: random.Random) -> InvoiceSubmission:
    """Return one invoice with consistent net, VAT and gross amounts."""
    net = (Decimal(generator.randint(2000, 40000)) / 100 * country.amount_scale).quantize(_CENT, rounding=ROUND_HALF_UP)
    vat = (net * merchant.vat_rate / 100).quantize(_CENT, rounding=ROUND_HALF_UP)
    gross = net + vat
    vat_number = None if merchant.defect == "no_vat_number" else _vat_number(country, generator)
    return InvoiceSubmission.model_validate(
        {
            "schemaVersion": "1.0",
            "documentType": "FULL_INVOICE",
            "invoiceNumber": f"{country.code}-MOCK-{index:04d}",
            "issueDate": issue_date.isoformat(),
            "currency": country.currency,
            "supplier": {
                "name": merchant.name,
                "vatNumber": vat_number,
                "address": {"street": None, "postalCode": None, "city": merchant.city, "countryCode": country.code},
            },
            "customer": {"name": CUSTOMER_NAME, "vatNumber": CUSTOMER_VAT_NUMBER},
            "lines": [
                {
                    "description": merchant.description,
                    "category": merchant.category,
                    "netAmount": _money(net),
                    "vatRate": float(merchant.vat_rate),
                    "vatAmount": _money(vat),
                    "grossAmount": _money(gross),
                }
            ],
            "totals": {"netAmount": _money(net), "vatAmount": _money(vat), "grossAmount": _money(gross)},
            "cardLast4": CARD_LAST4,
        }
    )


def generate_receipts(today: date) -> list[MockReceipt]:
    """Return the mock receipts of every country, oldest first."""
    generator = random.Random(MOCK_RANDOM_SEED)
    receipts: list[MockReceipt] = []
    for country in MOCK_COUNTRIES:
        for merchant in country.merchants:
            issue_date = today - timedelta(days=generator.randint(1, MOCK_HISTORY_DAYS))
            invoice = build_invoice(country, merchant, len(receipts) + 1, issue_date, generator)
            receipts.append(MockReceipt(country, merchant, invoice))
    return sorted(receipts, key=lambda receipt: receipt.invoice.issue_date)


def build_mock_database(target_engine: Engine, today: date) -> None:
    """Drop the tables. Fill them with the mock user, accounts, transactions and receipts."""
    import app.models  # noqa: F401  (register tables)

    SQLModel.metadata.drop_all(target_engine)
    SQLModel.metadata.create_all(target_engine)
    receipts = generate_receipts(today)

    with Session(target_engine) as session:
        user = User(name=CUSTOMER_NAME)
        session.add(user)
        session.flush()
        for currency in sorted({country.currency for country in MOCK_COUNTRIES}):
            session.add(Account(user_id=user.id, currency=currency, balance=ACCOUNT_BALANCE))
        session.flush()
        account_ids = {account.currency: account.id for account in session.exec(select(Account)).all()}

        for receipt in receipts:
            if receipt.merchant.defect == "no_transaction":
                continue
            session.add(
                Transaction(
                    account_id=account_ids[receipt.invoice.currency],
                    amount=receipt.invoice.totals.gross_amount,
                    currency=receipt.invoice.currency,
                    country=receipt.country.code,
                    merchant=receipt.merchant.name,
                    kind="card",
                    created_at=paid_on(receipt.invoice.issue_date),
                )
            )
        session.commit()

        for receipt in receipts:
            submit_invoice(session, receipt.invoice)
            # The employee scans the receipt on the evening of the payment day.
            record = session.exec(select(InvoiceRecord).order_by(col(InvoiceRecord.id).desc()).limit(1)).one()
            record.created_at = datetime.combine(receipt.invoice.issue_date, time(hour=18), tzinfo=timezone.utc)
            session.add(record)
        session.commit()


def run() -> None:
    build_mock_database(default_engine, date.today())
    print(f"Mock database built for {len(vat_rules.SUPPORTED_COUNTRIES)} countries.")


if __name__ == "__main__":
    run()
