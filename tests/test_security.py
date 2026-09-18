from src.intelligence import (
    generate_record_hash,
    verify_record_integrity,
    analyze_and_save,
    calculate_image_sha256
)

from src.signature import generate_key_pair, sign_record, verify_record


def test_record_hash_is_consistent():
    hash1 = generate_record_hash(
        "TEST-001",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement above threshold",
        "prototype-1.0",
        "reference-1.0"
    )

    hash2 = generate_record_hash(
        "TEST-001",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement above threshold",
        "prototype-1.0",
        "reference-1.0"
    )

    assert hash1 == hash2
    assert len(hash1) == 64


def test_signature_verification():
    signing_key, verify_key = generate_key_pair()

    record_hash = "test-record-hash"

    signature = sign_record(
        record_hash,
        signing_key
    )

    assert verify_record(
        record_hash,
        signature,
        verify_key
    ) is True


def test_tampered_record_is_rejected():
    signing_key, verify_key = generate_key_pair()

    record_hash = "original-record-hash"

    signature = sign_record(
        record_hash,
        signing_key
    )

    assert verify_record(
        "tampered-record-hash",
        signature,
        verify_key
    ) is False
def test_security_fields_change_record_hash():
    base_hash = generate_record_hash(
        "TEST-002",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement above threshold",
        "prototype-1.0",
        "reference-1.0",
        "OP-001",
        22.5726,
        88.3639,
        "image-hash-001"
    )

    changed_gps_hash = generate_record_hash(
        "TEST-002",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement above threshold",
        "prototype-1.0",
        "reference-1.0",
        "OP-001",
        22.5727,
        88.3639,
        "image-hash-001"
    )

    changed_image_hash = generate_record_hash(
        "TEST-002",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement above threshold",
        "prototype-1.0",
        "reference-1.0",
        "OP-001",
        22.5726,
        88.3639,
        "image-hash-002"
    )

    changed_operator_hash = generate_record_hash(
        "TEST-002",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement above threshold",
        "prototype-1.0",
        "reference-1.0",
        "OP-002",
        22.5726,
        88.3639,
        "image-hash-001"
    )

    assert base_hash != changed_gps_hash
    assert base_hash != changed_image_hash
    assert base_hash != changed_operator_hash
def test_timestamp_change_changes_record_hash():
    base_hash = generate_record_hash(
        "TEST-TIMESTAMP-001",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement 24.0 compared with threshold 20.0",
        "prototype-1.0",
        "reference-1.0",
        "OP-001",
        22.5726,
        88.3639,
        "image-hash-001",
        "2026-09-10T10:00:00+00:00"
    )

    changed_timestamp_hash = generate_record_hash(
        "TEST-TIMESTAMP-001",
        "POSITIVE",
        0.90,
        24.0,
        "GOOD",
        "Measurement 24.0 compared with threshold 20.0",
        "prototype-1.0",
        "reference-1.0",
        "OP-001",
        22.5726,
        88.3639,
        "image-hash-001",
        "2026-09-10T10:01:00+00:00"
    )

    assert base_hash != changed_timestamp_hash
from src.intelligence import generate_record_hash

def test_record_integrity_verification():
    result = analyze_and_save(
        test_id="VERIFY-001",
        measurement=24.0,
        quality_status="GOOD",
        operator_id="OP-001",
        latitude=22.5726,
        longitude=88.3639,
        image_sha256="image-hash-001"
    )

    is_valid = verify_record_integrity(
        test_id="VERIFY-001",
        result=result["result"],
        confidence=result["confidence"],
        measurement=24.0,
        quality_status="GOOD",
        decision_reason=result["decision_reason"],
        model_version="prototype-1.0",
        reference_version="reference-1.0",
        operator_id="OP-001",
        latitude=22.5726,
        longitude=88.3639,
        image_sha256="image-hash-001",
        timestamp_utc=result["timestamp_utc"],
        record_hash=result["record_hash"],
        signature=result["signature"]
    )

    assert is_valid is True
def test_tampered_record_fails_integrity_verification():
    result = analyze_and_save(
        test_id="TAMPER-001",
        measurement=24.0,
        quality_status="GOOD",
        operator_id="OP-001",
        latitude=22.5726,
        longitude=88.3639,
        image_sha256="image-hash-001"
    )

    # Change the GPS coordinate after the record was signed.
    # The original hash/signature should no longer validate.
    is_valid = verify_record_integrity(
        test_id="TAMPER-001",
        result=result["result"],
        confidence=result["confidence"],
        measurement=24.0,
        quality_status="GOOD",
        decision_reason=result["decision_reason"],
        model_version="prototype-1.0",
        reference_version="reference-1.0",
        operator_id="OP-001",
        latitude=22.5727,  # TAMPERED VALUE
        longitude=88.3639,
        image_sha256="image-hash-001",
        timestamp_utc=result["timestamp_utc"],
        record_hash=result["record_hash"],
        signature=result["signature"]
    )

    assert is_valid is False
def test_image_sha256_is_deterministic():
    image_bytes = b"sample image data"

    hash_1 = calculate_image_sha256(image_bytes)
    hash_2 = calculate_image_sha256(image_bytes)

    assert hash_1 == hash_2
    assert len(hash_1) == 64


def test_different_images_have_different_sha256():
    image_1 = b"sample image data 1"
    image_2 = b"sample image data 2"

    hash_1 = calculate_image_sha256(image_1)
    hash_2 = calculate_image_sha256(image_2)

    assert hash_1 != hash_2


def test_image_sha256_rejects_invalid_input():
    try:
        calculate_image_sha256("not bytes")
        assert False
    except TypeError:
        assert True
def test_get_test_by_id():
    from src.secure_database import get_test_by_id

    result = analyze_and_save(
        test_id="HISTORY-ID-001",
        measurement=25.0,
        quality_status="GOOD",
        operator_id="OP-HISTORY"
    )

    rows = get_test_by_id("HISTORY-ID-001")

    assert len(rows) >= 1

    row = rows[-1]

    assert row[1] == "HISTORY-ID-001"
    assert row[3] == "OP-HISTORY"
    assert row[6] == "POSITIVE"
    assert row[14] == result["record_hash"]
    assert row[15] == result["signature"]


def test_get_tests_by_operator():
    from src.secure_database import get_tests_by_operator

    analyze_and_save(
        test_id="OPERATOR-001",
        measurement=25.0,
        quality_status="GOOD",
        operator_id="OP-TEST"
    )

    analyze_and_save(
        test_id="OPERATOR-002",
        measurement=15.0,
        quality_status="GOOD",
        operator_id="OP-TEST"
    )

    rows = get_tests_by_operator("OP-TEST")

    test_ids = [row[1] for row in rows]

    assert "OPERATOR-001" in test_ids
    assert "OPERATOR-002" in test_ids

    for row in rows:
        assert row[3] == "OP-TEST"


def test_get_tests_by_result():
    from src.secure_database import get_tests_by_result

    analyze_and_save(
        test_id="RESULT-POSITIVE-001",
        measurement=30.0,
        quality_status="GOOD",
        operator_id="OP-RESULT"
    )

    analyze_and_save(
        test_id="RESULT-NEGATIVE-001",
        measurement=10.0,
        quality_status="GOOD",
        operator_id="OP-RESULT"
    )

    positive_rows = get_tests_by_result("POSITIVE")
    negative_rows = get_tests_by_result("NEGATIVE")

    positive_ids = [row[1] for row in positive_rows]
    negative_ids = [row[1] for row in negative_rows]

    assert "RESULT-POSITIVE-001" in positive_ids
    assert "RESULT-NEGATIVE-001" not in positive_ids

    assert "RESULT-NEGATIVE-001" in negative_ids
    assert "RESULT-POSITIVE-001" not in negative_ids