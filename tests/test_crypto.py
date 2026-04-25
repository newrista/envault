"""Unit tests for envault.crypto encryption/decryption."""

import pytest
from envault.crypto import encrypt, decrypt, SALT_SIZE


PASSWORD = "correct-horse-battery-staple"
PLAINTEXT = "SECRET_KEY=super_secret_value"


def test_encrypt_returns_bytes():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(result, bytes)


def test_encrypted_data_longer_than_salt():
    result = encrypt(PLAINTEXT, PASSWORD)
    assert len(result) > SALT_SIZE


def test_decrypt_roundtrip():
    encrypted = encrypt(PLAINTEXT, PASSWORD)
    decrypted = decrypt(encrypted, PASSWORD)
    assert decrypted == PLAINTEXT


def test_different_encryptions_produce_different_ciphertext():
    enc1 = encrypt(PLAINTEXT, PASSWORD)
    enc2 = encrypt(PLAINTEXT, PASSWORD)
    assert enc1 != enc2  # different salts each time


def test_wrong_password_raises_value_error():
    encrypted = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(ValueError, match="Invalid password"):
        decrypt(encrypted, "wrong-password")


def test_corrupted_data_raises_value_error():
    encrypted = bytearray(encrypt(PLAINTEXT, PASSWORD))
    encrypted[20] ^= 0xFF  # flip a byte in the ciphertext
    with pytest.raises(ValueError):
        decrypt(bytes(encrypted), PASSWORD)
