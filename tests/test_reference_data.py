from src.reference_data import (
    get_reference,
    get_threshold,
    get_reference_version
)


def test_valid_reference():
    reference = get_reference("prototype_test")

    assert reference is not None
    assert reference["threshold"] == 20.0
    assert reference["version"] == "reference-1.0"


def test_get_threshold():
    threshold = get_threshold("prototype_test")

    assert threshold == 20.0


def test_get_reference_version():
    version = get_reference_version("prototype_test")

    assert version == "reference-1.0"


def test_unknown_reference():
    reference = get_reference("unknown_test")

    assert reference is None


def test_unknown_threshold():
    threshold = get_threshold("unknown_test")

    assert threshold is None


def test_unknown_reference_version():
    version = get_reference_version("unknown_test")

    assert version is None