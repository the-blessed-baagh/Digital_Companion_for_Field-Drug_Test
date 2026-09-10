import hashlib
import math

from src.secure_database import save_test_result
from src.signature import generate_key_pair, sign_record
from src.reference_data import get_reference


VALID_QUALITY_STATUSES = {"GOOD", "BAD"}


def analyze_test(measurement, threshold, quality_status):
    """
    KAVACH intelligence / decision engine.

    This is a prototype decision engine.
    The threshold must come from validated reference data
    before production use.
    """

    # 1. Missing measurement
    if measurement is None:
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": "No measurement available"
        }

    # 2. Invalid measurement type
    try:
        measurement = float(measurement)
    except (TypeError, ValueError):
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": "Invalid measurement"
        }

    # 3. NaN or infinite measurement
    if not math.isfinite(measurement):
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": "Measurement is not a finite number"
        }

    # 4. Missing threshold
    if threshold is None:
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": "No reference threshold available"
        }

    # 5. Invalid threshold type
    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": "Invalid reference threshold"
        }

    # 6. Invalid threshold value
    if not math.isfinite(threshold) or threshold <= 0:
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": "Invalid reference threshold"
        }

    # 7. Invalid quality status
    if quality_status not in VALID_QUALITY_STATUSES:
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": f"Invalid test quality status: {quality_status}"
        }

    # 8. Poor test quality
    if quality_status != "GOOD":
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": f"Test quality is {quality_status}"
        }

    # 9. Decision
    if measurement >= threshold:
        result = "POSITIVE"
        difference = measurement - threshold
    else:
        result = "NEGATIVE"
        difference = threshold - measurement

    # Prototype confidence calculation
    confidence = min(
        0.99,
        0.50 + (difference / max(threshold, 1)) * 0.50
    )

    decision_reason = (
        f"Measurement {measurement} compared with "
        f"threshold {threshold}"
    )

    return {
        "result": result,
        "confidence": round(confidence, 2),
        "decision_reason": decision_reason
    }


def generate_record_hash(
    test_id,
    result,
    confidence,
    measurement,
    quality_status,
    decision_reason,
    model_version,
    reference_version
):
    """
    Generate a SHA-256 hash for a KAVACH test record.
    """

    record = (
        f"{test_id}|"
        f"{result}|"
        f"{confidence}|"
        f"{measurement}|"
        f"{quality_status}|"
        f"{decision_reason}|"
        f"{model_version}|"
        f"{reference_version}"
    )

    return hashlib.sha256(
        record.encode("utf-8")
    ).hexdigest()


def analyze_and_save(
    test_id,
    measurement,
    quality_status,
    test_type="prototype_test",
    model_version="prototype-1.0"
):
    """
    Get reference data, analyze the test,
    hash the record, sign it, and save it securely.
    """

    reference = get_reference(test_type)

    if reference is None:
        return {
            "result": "INCONCLUSIVE",
            "confidence": 0.0,
            "decision_reason": f"Unknown test type: {test_type}"
        }

    threshold = reference["threshold"]
    reference_version = reference["version"]

    analysis = analyze_test(
        measurement,
        threshold,
        quality_status
    )

    record_hash = generate_record_hash(
        test_id,
        analysis["result"],
        analysis["confidence"],
        measurement,
        quality_status,
        analysis["decision_reason"],
        model_version,
        reference_version
    )

    signing_key, _verify_key = generate_key_pair()

    signature = sign_record(
        record_hash,
        signing_key
    )

    save_test_result(
        test_id=test_id,
        result=analysis["result"],
        confidence=analysis["confidence"],
        measurement=measurement,
        quality_status=quality_status,
        decision_reason=analysis["decision_reason"],
        model_version=model_version,
        reference_version=reference_version,
        record_hash=record_hash,
        signature=signature
    )

    return {
        **analysis,
        "test_type": test_type,
        "threshold": threshold,
        "reference_version": reference_version,
        "record_hash": record_hash,
        "signature": signature
    }