"""
KAVACH reference data.

IMPORTANT:
The values below are PROTOTYPE values only.
They must be replaced with validated reference values
from the approved drug-testing protocol before production use.
"""

REFERENCE_DATA = {
    "prototype_test": {
        "threshold": 20.0,
        "version": "reference-1.0"
    }
}


def get_reference(test_type):
    """
    Return the reference threshold and version
    for a given test type.
    """

    reference = REFERENCE_DATA.get(test_type)

    if reference is None:
        return None

    return reference


def get_threshold(test_type):
    """
    Return only the threshold for a test type.
    """

    reference = get_reference(test_type)

    if reference is None:
        return None

    return reference["threshold"]


def get_reference_version(test_type):
    """
    Return the reference-data version.
    """

    reference = get_reference(test_type)

    if reference is None:
        return None

    return reference["version"]