from sqlcipher3 import dbapi2 as sqlite


DB_PATH = "secure_results.db"
DB_KEY = "kavach-demo-key"


# Connect to database
connection = sqlite.connect(DB_PATH)
cursor = connection.cursor()

# Set encryption key
cursor.execute(f"PRAGMA key = '{DB_KEY}';")

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result TEXT NOT NULL,
    delta_e REAL NOT NULL
)
""")

# Insert one test result
cursor.execute("""
INSERT INTO test_results (result, delta_e)
VALUES (?, ?)
""", ("NEGATIVE", 19.11))

connection.commit()

# Retrieve the result
cursor.execute("""
SELECT id, result, delta_e
FROM test_results
""")

rows = cursor.fetchall()

print("================================")
print("      SQLCIPHER POC")
print("================================")
print("Database created : YES")
print("Encryption key   : SET")
print("Stored result    : YES")
print("Retrieved data   :")
print(rows)

connection.close()