"""EU VAT number validation against VIES. Mocked for the demo.

The real VIES service is an external dependency. It stays out of scope until
after the demo. The mock passes every VAT number except one known-bad value.
"""
MOCK_INVALID_VAT = "XX12345678"


def validate_vat_number(vat_number: str | None) -> bool:
    """Return True when the VAT number belongs to a legitimate company."""
    if vat_number is None:
        return False
    return vat_number != MOCK_INVALID_VAT
