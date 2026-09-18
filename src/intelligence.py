import hashlib
import json
import math
from datetime import datetime, timezone

from src.secure_database import save_test_result
from src.signature import generate_key_pair, sign_record, verify_record
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
    reference_version,
    operator_id=None,
    latitude=None,
    longitude=None,
    image_sha256=None,
    timestamp_utc=None
):
    """
    Generate a deterministic SHA-256 hash for the complete
    digital test record.

    Canonical JSON is used so that another implementation,
    such as Flutter/Dart, can reproduce the same hash using
    the same field values and canonicalization rules.
    """

    record = {
        "test_id": test_id,
        "timestamp_utc": timestamp_utc,
        "operator_id": operator_id,
        "gps": {
            "latitude": latitude,
            "longitude": longitude
        },
        "result": result,
        "confidence": confidence,
        "measurement": measurement,
        "quality_status": quality_status,
        "decision_reason": decision_reason,
        "model_version": model_version,
        "reference_version": reference_version,
        "image_sha256": image_sha256
    }

    canonical_record = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )

    return hashlib.sha256(
        canonical_record.encode("utf-8")
    ).hexdigest()


def analyze_and_save(
    test_id,
    measurement,
    quality_status,
    test_type="prototype_test",
    model_version="prototype-1.0",
    operator_id=None,
    latitude=None,
    longitude=None,
    image_sha256=None
):
    """
    Get reference data, analyze the test,
    generate a timestamp, hash the complete record,
    sign it, and save it securely.
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

    # Generate the timestamp BEFORE hashing.
    # This exact timestamp becomes part of the signed record.
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    record_hash = generate_record_hash(
        test_id,
        analysis["result"],
        analysis["confidence"],
        measurement,
        quality_status,
        analysis["decision_reason"],
        model_version,
        reference_version,
        operator_id,
        latitude,
        longitude,
        image_sha256,
        timestamp_utc
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
        image_sha256=image_sha256,
        record_hash=record_hash,
        signature=signature,
        operator_id=operator_id,
        latitude=latitude,
        longitude=longitude,
        timestamp_utc=timestamp_utc
    )

    return {
        **analysis,
        "test_type": test_type,
        "threshold": threshold,
        "reference_version": reference_version,
        "timestamp_utc": timestamp_utc,
        "operator_id": operator_id,
        "latitude": latitude,
        "longitude": longitude,
        "image_sha256": image_sha256,
        "record_hash": record_hash,
        "signature": signature
    }
def verify_record_integrity(
    test_id,
    result,
    confidence,
    measurement,
    quality_status,
    decision_reason,
    model_version,
    reference_version,
    operator_id,
    latitude,
    longitude,
    image_sha256,
    timestamp_utc,
    record_hash,
    signature
):
    """
    Verify the integrity and authenticity of a digital test record.

    Verification has two stages:

    1. Recalculate the canonical SHA-256 record hash and compare it
       with the stored record_hash.
    2. Verify the stored Ed25519 signature against the stored hash.

    Returns True only when both checks succeed.
    """

    # Recalculate the hash from the record fields
    recalculated_hash = generate_record_hash(
        test_id,
        result,
        confidence,
        measurement,
        quality_status,
        decision_reason,
        model_version,
        reference_version,
        operator_id,
        latitude,
        longitude,
        image_sha256,
        timestamp_utc
    )

    # First check: record data must match the stored hash
    if recalculated_hash != record_hash:
        return False

    # Second check: signature must match the verified record hash
    _signing_key, verify_key = generate_key_pair()

    return verify_record(
        record_hash,
        signature,
        verify_key
    )
def calculate_image_sha256(image_bytes):
    """
    Calculate the SHA-256 hash of captured image bytes.

    The resulting hash can be stored as image_sha256 and included
    in the canonical test record before hashing and signing.
    """

    if not isinstance(image_bytes, bytes):
        raise TypeError("image_bytes must be bytes")

    return hashlib.sha256(image_bytes).hexdigest()