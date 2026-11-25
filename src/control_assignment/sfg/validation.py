from ..common.exceptions import ValidationError


def validate_sfg(sfg):
    """Check an SFGInput. Raises ValidationError with a clear message."""
    if len(sfg.nodes) < 2:
        raise ValidationError("Add at least 2 nodes.")
    if len(set(sfg.nodes)) != len(sfg.nodes):
        raise ValidationError("Node names must be unique.")
    if not sfg.input_node or not sfg.output_node:
        raise ValidationError("Choose an input node and an output node.")
    if sfg.input_node == sfg.output_node:
        raise ValidationError("Input and output nodes must be different.")
    if not sfg.branches:
        raise ValidationError("Add at least one branch.")

    labels = set()
    for b in sfg.branches:
        if b.source not in sfg.nodes or b.target not in sfg.nodes:
            raise ValidationError(f"Branch {b.label}: unknown node.")
        if b.label in labels:
            raise ValidationError(f"Duplicate branch label '{b.label}'.")
        labels.add(b.label)
        if b.gain == 0:
            raise ValidationError(f"Branch {b.label}: gain cannot be 0.")
