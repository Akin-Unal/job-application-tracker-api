from datetime import timedelta

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_works() -> None:
    hashed = hash_password("StrongPassword123")

    assert hashed != "StrongPassword123"
    assert len(hashed) > 20


def test_correct_password_verification_succeeds() -> None:
    hashed = hash_password("StrongPassword123")

    assert verify_password("StrongPassword123", hashed)


def test_incorrect_password_verification_fails() -> None:
    hashed = hash_password("StrongPassword123")

    assert not verify_password("WrongPassword123", hashed)


def test_jwt_token_creation_works() -> None:
    token = create_access_token("user-id")
    payload = decode_access_token(token)

    assert payload["sub"] == "user-id"


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(AuthenticationError):
        decode_access_token("not-a-valid-token")


def test_expired_token_is_rejected() -> None:
    token = create_access_token("user-id", expires_delta=timedelta(seconds=-1))

    with pytest.raises(AuthenticationError):
        decode_access_token(token)
