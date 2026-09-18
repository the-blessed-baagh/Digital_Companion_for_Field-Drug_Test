from sqlcipher3 import dbapi2 as sqlite


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
            operator_id TEXT,
            latitude REAL,
            longitude REAL,
            result TEXT NOT NULL,
            confidence REAL,
            measurement REAL,
            quality_status TEXT,
            decision_reason TEXT,
            model_version TEXT,
            reference_version TEXT,
            image_sha256 TEXT,
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
    image_sha256=None,
    record_hash=None,
    signature=None,
    operator_id=None,
    latitude=None,
    longitude=None,
    timestamp_utc=None
):
    """
    Save a digitally signed test result into the encrypted SQLCipher database.

    timestamp_utc must be the same timestamp that was included
    in the canonical record before hashing and signing.
    """

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    if timestamp_utc is None:
        raise ValueError(
            "timestamp_utc is required for a signed test record"
        )

    cursor.execute("""
        INSERT INTO test_results (
            test_id,
            timestamp,
            operator_id,
            latitude,
            longitude,
            result,
            confidence,
            measurement,
            quality_status,
            decision_reason,
            model_version,
            reference_version,
            image_sha256,
            record_hash,
            signature
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        timestamp_utc,
        operator_id,
        latitude,
        longitude,
        result,
        confidence,
        measurement,
        quality_status,
        decision_reason,
        model_version,
        reference_version,
        image_sha256,
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
            operator_id,
            latitude,
            longitude,
            result,
            confidence,
            measurement,
            quality_status,
            decision_reason,
            model_version,
            reference_version,
            image_sha256,
            record_hash,
            signature
        FROM test_results
        ORDER BY id
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


def get_test_history():
    """
    Return stored test records in a structured format
    for the application History screen.
    """

    rows = get_test_results()

    history = []

    for row in rows:
        history.append({
            "id": row[0],
            "test_id": row[1],
            "timestamp_utc": row[2],
            "operator_id": row[3],
            "latitude": row[4],
            "longitude": row[5],
            "result": row[6],
            "confidence": row[7],
            "measurement": row[8],
            "quality_status": row[9],
            "decision_reason": row[10],
            "model_version": row[11],
            "reference_version": row[12],
            "image_sha256": row[13],
            "record_hash": row[14],
            "signature": row[15]
        })

    return history
def get_test_by_id(test_id):
    """
    Return all stored records matching a test ID.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            test_id,
            timestamp,
            operator_id,
            latitude,
            longitude,
            result,
            confidence,
            measurement,
            quality_status,
            decision_reason,
            model_version,
            reference_version,
            image_sha256,
            record_hash,
            signature
        FROM test_results
        WHERE test_id = ?
        ORDER BY id
    """, (test_id,))

    rows = cursor.fetchall()

    connection.close()

    return rows


def get_tests_by_operator(operator_id):
    """
    Return all stored records for a specific operator.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            test_id,
            timestamp,
            operator_id,
            latitude,
            longitude,
            result,
            confidence,
            measurement,
            quality_status,
            decision_reason,
            model_version,
            reference_version,
            image_sha256,
            record_hash,
            signature
        FROM test_results
        WHERE operator_id = ?
        ORDER BY id
    """, (operator_id,))

    rows = cursor.fetchall()

    connection.close()

    return rows


def get_tests_by_result(result):
    """
    Return all stored records matching a test result.

    Expected values include:
    POSITIVE
    NEGATIVE
    INCONCLUSIVE
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            test_id,
            timestamp,
            operator_id,
            latitude,
            longitude,
            result,
            confidence,
            measurement,
            quality_status,
            decision_reason,
            model_version,
            reference_version,
            image_sha256,
            record_hash,
            signature
        FROM test_results
        WHERE result = ?
        ORDER BY id
    """, (result,))

    rows = cursor.fetchall()

    connection.close()

    return rows