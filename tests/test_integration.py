import uuid

from src.intelligence import analyze_and_save
from src.secure_database import get_test_results
from src.signature import generate_key_pair, verify_record


def test_full_kavach_pipeline():
    test_id = f"INTEGRATION-TEST-{uuid.uuid4().hex[:8]}"

    # 1. Run intelligence + reference lookup + hashing + signing + database save
    result = analyze_and_save(
        test_id=test_id,
        measurement=24.0,
        quality_status="GOOD",
        test_type="prototype_test"
    )

    # 2. Check intelligence result
    assert result["result"] == "POSITIVE"
    assert result["confidence"] > 0
    assert result["threshold"] == 20.0
    assert result["reference_version"] == "reference-1.0"

    # 3. Check security fields
    assert len(result["record_hash"]) == 64
    assert len(result["signature"]) == 128

    # 4. Check database record
    rows = get_test_results()

    matching_rows = [
        row for row in rows
        if row[1] == test_id
    ]

    assert len(matching_rows) == 1

    row = matching_rows[0]

    assert row[3] == "POSITIVE"
    assert row[4] == result["confidence"]
    assert row[5] == 24.0
    assert row[6] == "GOOD"
    assert row[8] == "prototype-1.0"
    assert row[9] == "reference-1.0"
    assert row[10] == result["record_hash"]
    assert row[11] == result["signature"]

    # 5. Verify the stored digital signature
    _, verify_key = generate_key_pair()

    assert verify_record(
        row[10],
        row[11],
        verify_key
    ) is True