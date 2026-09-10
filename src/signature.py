from nacl.signing import SigningKey, VerifyKey
from pathlib import Path


KEY_DIR = Path("keys")
PRIVATE_KEY_FILE = KEY_DIR / "signing_key.bin"
PUBLIC_KEY_FILE = KEY_DIR / "verify_key.bin"


def generate_key_pair():
    """
    Load the existing Ed25519 key pair.
    If it does not exist, generate it once and save it.
    """

    KEY_DIR.mkdir(exist_ok=True)

    # If keys already exist, load them
    if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():

        private_key = PRIVATE_KEY_FILE.read_bytes()
        public_key = PUBLIC_KEY_FILE.read_bytes()

        signing_key = SigningKey(private_key)
        verify_key = VerifyKey(public_key)

        return signing_key, verify_key

    # Otherwise generate a new key pair
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    # Save keys for future use
    PRIVATE_KEY_FILE.write_bytes(signing_key.encode())
    PUBLIC_KEY_FILE.write_bytes(verify_key.encode())

    return signing_key, verify_key


def sign_record(record_hash, signing_key):
    """
    Sign a record hash using an Ed25519 private signing key.
    """

    message = record_hash.encode("utf-8")
    signed_message = signing_key.sign(message)

    return signed_message.signature.hex()


def verify_record(record_hash, signature_hex, verify_key):
    """
    Verify an Ed25519 signature against a record hash.
    """

    message = record_hash.encode("utf-8")
    signature = bytes.fromhex(signature_hex)

    try:
        verify_key.verify(message, signature)
        return True

    except Exception:
        return False