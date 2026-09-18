from pathlib import Path
from nacl import bindings
KEY_DIR = Path("keys")
PRIVATE_KEY_FILE = KEY_DIR / "signing_key.bin"
PUBLIC_KEY_FILE = KEY_DIR / "verify_key.bin"
def generate_key_pair():
    """
    Generate or load an Ed25519 key pair using
    libsodium-backed low-level bindings.
    """
    KEY_DIR.mkdir(exist_ok=True)
    if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():
        private_key = PRIVATE_KEY_FILE.read_bytes()
        public_key = PUBLIC_KEY_FILE.read_bytes()
        if len(private_key) != bindings.crypto_sign_SECRETKEYBYTES:
            raise ValueError("Invalid Ed25519 private key")
        if len(public_key) != bindings.crypto_sign_PUBLICKEYBYTES:
            raise ValueError("Invalid Ed25519 public key")
        return private_key, public_key
    public_key, private_key = bindings.crypto_sign_keypair()
    PRIVATE_KEY_FILE.write_bytes(private_key)
    PUBLIC_KEY_FILE.write_bytes(public_key)
    return private_key, public_key
def sign_record(record_hash, signing_key):
    """
    Sign a record hash using libsodium-backed Ed25519.
    crypto_sign() returns:
        signature + message
    We store only the signature.
    """
    message = record_hash.encode("utf-8")
    signed_message = bindings.crypto_sign(
        message,
        signing_key
    )
    signature = signed_message[:bindings.crypto_sign_BYTES]
    return signature.hex()
def verify_record(record_hash, signature_hex, verify_key):
    """
    Verify an Ed25519 signature using
    libsodium-backed crypto_sign_open().
    """
    message = record_hash.encode("utf-8")
    signature = bytes.fromhex(signature_hex)
    signed_message = signature + message
    try:
        bindings.crypto_sign_open(
            signed_message,
            verify_key
        )
        return True
    except Exception:
        return False
