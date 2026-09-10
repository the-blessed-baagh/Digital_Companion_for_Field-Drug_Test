Digital Companion for Field Drug Testing

Smart India Hackathon 2026
Problem Statement ID: 26231
Team: Eclipse PROTOCOL

Overview

Digital Companion for Field Drug Testing is a software solution designed to support field drug-testing workflows through digital result processing, secure record management, and mobile integration.

The project combines image-based testing, automated result interpretation, secure local data storage, and digitally verifiable test records.

Data + Intelligence + Security Module

This repository includes the Data, Intelligence, and Security module developed for the project.

Processing Pipeline

Measurement + Quality Status
            ↓
       Reference Data
            ↓
    Intelligence Engine
            ↓
 POSITIVE / NEGATIVE / INCONCLUSIVE
            ↓
       SHA-256 Hash
            ↓
    Ed25519 Signature
            ↓
     SQLCipher Database

Decision Engine

The prototype decision engine follows these rules:

- GOOD quality + measurement ≥ reference threshold → POSITIVE
- GOOD quality + measurement < reference threshold → NEGATIVE
- BAD quality → INCONCLUSIVE
- Invalid or missing measurement → INCONCLUSIVE
- Invalid or missing reference data → INCONCLUSIVE

The current threshold and confidence calculation are prototype values and require validation against the approved drug-testing protocol before production use.

Secure Data Layer

The data layer uses SQLCipher for encrypted local SQLite storage.

Stored record information includes:

- Test ID
- Timestamp
- Result
- Confidence
- Measurement
- Quality status
- Decision reason
- Model version
- Reference-data version
- SHA-256 record hash
- Digital signature

Record Integrity and Authentication

Each generated test record is:

1. Serialized into a deterministic record representation.
2. Hashed using SHA-256.
3. Signed using an Ed25519 digital signature.
4. Stored in the encrypted database.

The signature can later be verified to detect modification of the signed record data.

Demo

"demo.py" demonstrates:

- Positive test
- Negative test
- Inconclusive test
- Original record signature verification
- Tampered-record verification

Expected security behaviour:

Original record signature valid : True
Tampered record signature valid : False

Testing

The module includes automated tests covering:

- Intelligence/decision logic
- Input validation
- Edge cases
- Reference data
- Security/signature verification
- End-to-end integration

The current copied module passes:

20 passed

Project Structure

src/
├── intelligence.py
├── reference_data.py
├── secure_database.py
├── signature.py
└── __init__.py

tests/
├── test_edge_cases.py
├── test_integration.py
├── test_intelligence.py
├── test_reference_data.py
├── test_security.py
└── test_validation.py

demo.py
requirements.txt
sqlcipher_poc.py

Integration Contract

The intelligence module can receive:

{
  "test_id": "KAVACH-DEMO-001",
  "test_type": "prototype_test",
  "measurement": 24.0,
  "quality_status": "GOOD"
}

The processing layer returns information such as:

{
  "result": "POSITIVE",
  "confidence": 0.60,
  "decision_reason": "Measurement 24.0 compared with threshold 20.0",
  "test_type": "prototype_test",
  "threshold": 20.0,
  "reference_version": "reference-1.0",
  "model_version": "prototype-1.0",
  "record_hash": "<SHA-256 hash>",
  "signature": "<Ed25519 signature>"
}

The mobile/Flutter layer can use this contract to integrate with the Data + Intelligence module.

Prototype Security Notice

This implementation is a prototype for the Smart India Hackathon project.

The current database key, reference values, model version, confidence calculation, and signing-key storage approach are intended for demonstration and development only. Production deployment requires appropriate key management, validated scientific reference data, security review, and protocol-level validation.

Disclaimer

This software prototype is not a certified forensic or medical diagnostic system. Final drug-testing decisions must rely on validated testing procedures, approved reference standards, and applicable legal and scientific requirements.