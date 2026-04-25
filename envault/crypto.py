"""Cryptographic utilities for encrypting and decrypting vault data."""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken


SALT_SIZE = 16
ITERATIONS = 390_000
KEY_LENGTH = 32


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
    )
    raw_key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(raw_key)


def encrypt(plaintext: str, password: str) -> bytes:
    """Encrypt plaintext string with a password. Returns salt + ciphertext."""
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    ciphertext = fernet.encrypt(plaintext.encode())
    return salt + ciphertext


def decrypt(data: bytes, password: str) -> str:
    """Decrypt data (salt + ciphertext) with a password. Returns plaintext."""
    salt = data[:SALT_SIZE]
    ciphertext = data[SALT_SIZE:]
    key = derive_key(password, salt)
    fernet = Fernet(key)
    try:
        return fernet.decrypt(ciphertext).decode()
    except InvalidToken as exc:
        raise ValueError("Invalid password or corrupted vault data.") from exc
