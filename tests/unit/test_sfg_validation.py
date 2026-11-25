import pytest

from control_assignment.common.exceptions import ValidationError
from control_assignment.sfg.models import Branch, SFGInput
from control_assignment.sfg.validation import validate_sfg


def good():
    return SFGInput(["R", "C"], [Branch("R", "C", 2.0, "G1")], "R", "C")


def test_valid():
    validate_sfg(good())


def test_errors():
    s = good(); s.output_node = "R"
    with pytest.raises(ValidationError): validate_sfg(s)
    s = good(); s.branches = []
    with pytest.raises(ValidationError): validate_sfg(s)
    s = good(); s.branches[0].gain = 0
    with pytest.raises(ValidationError): validate_sfg(s)
    s = good(); s.branches.append(Branch("R", "C", 1, "G1"))
    with pytest.raises(ValidationError): validate_sfg(s)
    s = good(); s.branches[0].target = "Z"
    with pytest.raises(ValidationError): validate_sfg(s)
