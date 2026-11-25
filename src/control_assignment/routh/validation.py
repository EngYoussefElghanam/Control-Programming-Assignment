from ..common.exceptions import ValidationError
from ..common.numeric import parse_number
from .models import RouthInput


def parse_coefficients(text):
    """'1, 2, 3 4' -> RouthInput([1.0, 2.0, 3.0, 4.0]). Raises ValidationError."""
    parts = text.replace(",", " ").split()
    if len(parts) < 2:
        raise ValidationError("Enter at least 2 coefficients (degree 1 or higher).")
    coeffs = [parse_number(p, "Coefficient") for p in parts]
    if coeffs[0] == 0:
        raise ValidationError("The first (highest power) coefficient cannot be 0.")
    return RouthInput(coeffs)
