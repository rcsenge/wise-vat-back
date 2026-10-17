"""One-off generator for extra approved sample invoices. Run from seed/ with uv.

Writes JSON files into sample_invoices/. Every case is an approved invoice.
The sidecar expected files are written by generate_golden.py in step two.
"""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

HERE = Path(__file__).resolve().parent
OUT = HERE / "sample_invoices"

# (filename, currency, supplier, vat, postal, city, country, card, document_type,
#  [(description, category, net, vat_rate), ...])
SPECS = [
    ("at_restaurant_graz", "EUR", "Gasthof Goldener Hirsch GmbH", "ATU74091653", "8010", "Graz", "AT", "4821", "FULL_INVOICE",
     [("Steirisches Backhendl", "FOOD_AND_DRINK", "34.18", 10), ("Veltliner Wein", "FOOD_AND_DRINK", "12.73", 20)]),
    ("at_taxi_wien", "EUR", "Wiener Taxi Zentrale", "ATU11304368", "1030", "Wien", "AT", "4821", "SIMPLIFIED_INVOICE",
     [("Fahrt zum Flughafen", "TRAVEL", "23.00", 13)]),
    ("de_parking_munich", "EUR", "Parkhaus am Hauptbahnhof GmbH", "DE812345678", "80335", "München", "DE", "4821", "SIMPLIFIED_INVOICE",
     [("Parken Tagesticket", "OTHER", "30.00", 19)]),
    ("fr_bistro_nice", "EUR", "Le Petit Bouchon SARL", "FR09876543210", "06000", "Nice", "FR", "4821", "SIMPLIFIED_INVOICE",
     [("Déjeuner affaires", "FOOD_AND_DRINK", "41.60", 10), ("Café", "FOOD_AND_DRINK", "3.20", 10)]),
    ("fr_highway_toulouse", "EUR", "Vinci Autoroutes", "FR92345678901", "31000", "Toulouse", "FR", "4821", "SIMPLIFIED_INVOICE",
     [("Péage A61", "ROAD_TOLL", "18.40", 20)]),
    ("it_restaurant_roma", "EUR", "Trattoria da Mario", "IT09876543210", "00184", "Roma", "IT", "4821", "FULL_INVOICE",
     [("Pasta e Vino", "FOOD_AND_DRINK", "38.00", 10), ("Coperto", "FOOD_AND_DRINK", "4.00", 10)]),
    ("it_garage_milano", "EUR", "Autorimessa Centrale", "IT12345678901", "20123", "Milano", "IT", "4821", "SIMPLIFIED_INVOICE",
     [("Sosta auto 24 ore", "VEHICLE_EXPENSES", "28.50", 22)]),
    ("nl_tram_amsterdam", "EUR", "GVB Amsterdam", "NL818181818B01", "1012", "Amsterdam", "NL", "4821", "SIMPLIFIED_INVOICE",
     [("Reizenkaart", "TRAVEL", "7.50", 9)]),
    ("nl_restaurant_rotterdam", "EUR", "Eetcafé de Haven", "NL823456789B01", "3011", "Rotterdam", "NL", "4821", "FULL_INVOICE",
     [("Kost en drank", "FOOD_AND_DRINK", "52.00", 9)]),
    ("pl_restaurant_wroclaw", "PLN", "Restauracja Karczma", "PL8980001234", "50-041", "Wrocław", "PL", "4821", "FULL_INVOICE",
     [("Obiad firmowy", "FOOD_AND_DRINK", "210.00", 8)]),
    ("pl_train_warsaw_krakow", "PLN", "PKP Intercity", "PL5260007890", "00-928", "Warszawa", "PL", "4821", "SIMPLIFIED_INVOICE",
     [("Bilet EIC Express", "TRAVEL", "189.00", 23)]),
    ("cz_fuel_prague", "CZK", "Čepro a.s.", "CZ26177005", "150 00", "Praha", "CZ", "4821", "SIMPLIFIED_INVOICE",
     [("Natural 95", "FUEL", "1450.00", 21)]),
    ("dk_fuel_aarhus", "DKK", "Circle K Danmark", "DK25621554", "8000", "Aarhus", "DK", "4821", "SIMPLIFIED_INVOICE",
     [("Diesel", "FUEL", "512.00", 25)]),
    ("dk_taxi_copenhagen", "DKK", "Taxa 4x35", "DK32850401", "2100", "København", "DK", "4821", "SIMPLIFIED_INVOICE",
     [("Tur til møde", "TRAVEL", "445.00", 25)]),
    ("se_restaurant_gothenburg", "SEK", "Sjömagasinet AB", "SE556074308901", "411 18", "Göteborg", "SE", "4821", "FULL_INVOICE",
     [("Middag", "FOOD_AND_DRINK", "980.00", 12)]),
    ("se_fair_stockholm", "SEK", "Stockholmsmässan AB", "SE556014455601", "125 80", "Stockholm", "SE", "4821", "FULL_INVOICE",
     [("Mässbiljett", "FAIR_ADMISSION", "1250.00", 25)]),
    ("at_fair_linz", "EUR", "Messezentrum Linz GmbH", "ATU61234567", "4021", "Linz", "AT", "4821", "FULL_INVOICE",
     [("Fachmesse Eintritt", "FAIR_ADMISSION", "46.00", 20)]),
    ("de_fuel_stuttgart", "EUR", "ARAL Tankstelle", "DE301876543", "70173", "Stuttgart", "DE", "4821", "SIMPLIFIED_INVOICE",
     [("Super E10", "FUEL", "68.32", 19)]),
]


def _two(value: str) -> str:
    return str(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build(line_specs: list[tuple[str, str, str, str]], invoice_number: str, **header) -> dict:
    lines = []
    net_total = Decimal("0")
    vat_total = Decimal("0")
    for description, category, net, rate in line_specs:
        float_net = Decimal(net)
        float_rate = Decimal(rate)
        vat = (float_net * float_rate / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gross = float_net + vat
        net_total += float_net
        vat_total += vat
        lines.append({
            "description": description,
            "category": category,
            "netAmount": _two(str(float_net)),
            "vatRate": float(rate),
            "vatAmount": _two(str(vat)),
            "grossAmount": _two(str(gross)),
        })
    return {
        "schemaVersion": "1.0",
        "documentType": header["document_type"],
        "invoiceNumber": invoice_number,
        "issueDate": "2026-09-10",
        "currency": header["currency"],
        "supplier": {
            "name": header["supplier"],
            "vatNumber": header["vat"],
            "address": {
                "street": "Beispielstrasse 1",
                "postalCode": header["postal"],
                "city": header["city"],
                "countryCode": header["country"],
            },
        },
        "customer": {"name": "Példa Tech Kft.", "vatNumber": "HU12345678"},
        "lines": lines,
        "totals": {
            "netAmount": _two(str(net_total)),
            "vatAmount": _two(str(vat_total)),
            "grossAmount": _two(str(net_total + vat_total)),
        },
        "cardLast4": header["card"],
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    written = 0
    for index, (filename, *rest) in enumerate(SPECS, start=1):
        invoice = build(rest[8], f"CC-2026-{1000 + index:04d}", currency=rest[0], supplier=rest[1],
                        vat=rest[2], postal=rest[3], city=rest[4], country=rest[5],
                        card=rest[6], document_type=rest[7])
        path = OUT / f"{filename}.json"
        path.write_text(json.dumps(invoice, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1
    print(f"Wrote {written} sample invoices to {OUT}")


if __name__ == "__main__":
    main()
