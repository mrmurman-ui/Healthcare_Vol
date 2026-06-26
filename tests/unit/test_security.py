"""Unit tests — security utilities."""
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    plain = "MySecret123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_wrong_password_fails():
    hashed = hash_password("correct")
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    token = create_refresh_token("user-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"


def test_tampered_token_raises():
    token = create_access_token("abc") + "garbage"
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token(token)


def test_access_token_carries_extra():
    token = create_access_token("u1", extra={"role": "admin"})
    payload = decode_token(token)
    assert payload["role"] == "admin"
