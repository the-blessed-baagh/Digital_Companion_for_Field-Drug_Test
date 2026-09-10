from sqlcipher3 import dbapi2 as sqlite
from datetime import datetime


DB_PATH = "secure_results.db"
DB_KEY = "kavach-demo-key"  # Prototype only


def get_connection():
    connection = sqlite.connect(DB_PATH)
    cursor = connection.cursor()

    # Unlock SQLCipher database
    cursor.execute(f"PRAGMA key = '{DB_KEY}';")

    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            result TEXT NOT NULL,
            confidence REAL,
            measurement REAL,
            quality_status TEXT,
            decision_reason TEXT,
            model_version TEXT,
            reference_version TEXT,
            record_hash TEXT,
            signature TEXT
        )
    """)

    connection.commit()
    connection.close()


def save_test_result(
    test_id,
    result,
    confidence=None,
    measurement=None,
    quality_status=None,
    decision_reason=None,
    model_version=None,
    reference_version=None,
    record_hash=None,
    signature=None
):
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()

    timestamp = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO test_results (
            test_id,
            timestamp,
            result,
            confidence,
            measurement,
            quality_status,
            decision_reason,
            model_version,
            reference_version,
            record_hash,
            signature
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        timestamp,
        result,
        confidence,
        measurement,
        quality_status,
        decision_reason,
        model_version,
        reference_version,
        record_hash,
        signature
    ))

    connection.commit()
    connection.close()


def get_test_results():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            test_id,
            timestamp,
            result,
            confidence,
            measurement,
            quality_status,
            decision_reason,
            model_version,
            reference_version,
            record_hash,
            signature
        FROM test_results
        ORDER BY id
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows