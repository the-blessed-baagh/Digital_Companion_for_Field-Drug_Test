from src.intelligence import generate_record_hash
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