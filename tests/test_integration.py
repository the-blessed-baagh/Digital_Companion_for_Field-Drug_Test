import uuid

from src.intelligence import analyze_and_save
from src.secure_database import get_test_results
from src.signature import generate_key_pair, verify_record


def test_full_kavach_pipeline():
    test_id = f"INTEGRATION-TEST-{uuid.uuid4().hex[:8]}"

    # 1. Run intelligence + reference lookup +
    # timestamp + hashing + signing + database save
    result = analyze_and_save(
        test_id=test_id,
        measurement=24.0,
        quality_status="GOOD",
        operator_id="OP-001",
        latitude=22.5726,
        longitude=88.3639,
        image_sha256="image-hash-001",
    )

    # 2. Check intelligence result
    assert result["result"] == "POSITIVE"
    assert result["confidence"] > 0
    assert result["threshold"] == 20.0
    assert result["reference_version"] == "reference-1.0"

    # 3. Check timestamp
    assert result["timestamp_utc"] is not None
    assert result["timestamp_utc"].endswith("+00:00")

    # 4. Check security fields
    assert len(result["record_hash"]) == 64
    assert len(result["signature"]) == 128

    # 5. Check database record
    rows = get_test_results()

    matching_rows = [
        row for row in rows
        if row[1] == test_id
    ]

    assert len(matching_rows) == 1

    row = matching_rows[0]

    # Database field checks
    assert row[2] == result["timestamp_utc"]
    assert row[3] == "OP-001"
    assert row[4] == 22.5726
    assert row[5] == 88.3639
    assert row[6] == "POSITIVE"
    assert row[7] == result["confidence"]
    assert row[8] == 24.0
    assert row[9] == "GOOD"
    assert row[11] == "prototype-1.0"
    assert row[12] == "reference-1.0"
    assert row[13] == "image-hash-001"
    assert row[14] == result["record_hash"]
    assert row[15] == result["signature"]

    # 6. Verify Ed25519 signature
    _, verify_key = generate_key_pair()

    assert verify_record(
        row[14],
        row[15],
        verify_key
    ) is True


def test_security_fields_flow_through_pipeline():

    result = analyze_and_save(
        test_id="SECURITY-001",
        measurement=24.0,
        quality_status="GOOD",
        operator_id="OP-001",
        latitude=22.5726,
        longitude=88.3639,
        image_sha256="image-hash-001"
    )

    # Check returned security fields
    assert result["timestamp_utc"] is not None
    assert result["operator_id"] == "OP-001"
    assert result["latitude"] == 22.5726
    assert result["longitude"] == 88.3639
    assert result["image_sha256"] == "image-hash-001"

    # Check database
    history = get_test_results()

    matching_rows = [
        row for row in history
        if row[1] == "SECURITY-001"
    ]

    assert len(matching_rows) >= 1

    row = matching_rows[-1]

    assert row[2] == result["timestamp_utc"]
    assert row[3] == "OP-001"
    assert row[4] == 22.5726
    assert row[5] == 88.3639
    assert row[13] == "image-hash-001"
    assert row[14] == result["record_hash"]
    assert row[15] == result["signature"]