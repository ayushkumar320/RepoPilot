"""BYOK keys are stored as ciphertext, and only the same secret reads them back."""

from __future__ import annotations

from cryptography.fernet import InvalidToken

from repopilot_api.access import credential_cipher


def test_round_trips_under_the_same_secret() -> None:
    cipher = credential_cipher("a-session-secret")
    token = cipher.encrypt(b"gsk_live_key")
    assert token != b"gsk_live_key"
    assert credential_cipher("a-session-secret").decrypt(token) == b"gsk_live_key"


def test_a_rotated_secret_cannot_read_old_ciphertext() -> None:
    token = credential_cipher("a-session-secret").encrypt(b"gsk_live_key")
    try:
        credential_cipher("a-different-secret").decrypt(token)
    except InvalidToken:
        return
    raise AssertionError("ciphertext decrypted under the wrong secret")
