import pytest

from control_assignment.common.exceptions import ValidationError
from control_assignment.routh.validation import parse_coefficients


def test_valid():
    assert parse_coefficients("1, 2 3,4").coefficients == [1, 2, 3, 4]


def test_fraction():
    assert parse_coefficients("1 1/2").coefficients == [1, 0.5]


@pytest.mark.parametrize("text", ["", "5", "a b c", "0 1 2", "1 2 x"])
def test_invalid(text):
    with pytest.raises(ValidationError):
        parse_coefficients(text)
