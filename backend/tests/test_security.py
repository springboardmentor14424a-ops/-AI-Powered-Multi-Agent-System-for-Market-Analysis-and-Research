from datetime import datetime, timedelta, timezone

import jwt

from app import security


def test_hash_and_verify_password():
    h = security.hash_password("test12345")
    assert h.startswith("$2b$")
    assert h != "test12345"
    assert security.verify_password("test12345", h)
    assert not security.verify_password("wrong-password", h)


def test_same_password_gives_different_hashes():
    assert security.hash_password("abc12345") != security.hash_password("abc12345")


def test_token_round_trip():
    token = security.create_access_token(42)
    assert security.decode_access_token(token) == 42


def test_tampered_token_rejected():
    token = security.create_access_token(42)
    assert security.decode_access_token(token + "x") is None


def test_expired_token_rejected():
    payload = {"sub": "42", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
    token = jwt.encode(payload, security.SECRET_KEY, algorithm=security.ALGORITHM)
    assert security.decode_access_token(token) is None


def test_token_signed_with_other_key_rejected():
    payload = {"sub": "42", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    token = jwt.encode(payload, "some-other-secret-key-of-32-bytes-long!!", algorithm="HS256")
    assert security.decode_access_token(token) is None