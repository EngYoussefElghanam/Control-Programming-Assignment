from .exceptions import ValidationError


def parse_number(text, what="value"):
    """Turn text into a float. Accepts '2', '-0.5', '1/2'. Raises ValidationError."""
    text = text.strip()
    if not text:
        raise ValidationError(f"{what} is empty.")
    try:
        if "/" in text:
            top, bottom = text.split("/")
            return float(top) / float(bottom)
        return float(text)
    except (ValueError, ZeroDivisionError):
        raise ValidationError(f"{what} '{text}' is not a valid number.")
