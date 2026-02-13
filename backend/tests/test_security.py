"""Security module tests."""

from __future__ import annotations

from app.core.security import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "my_secure_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_different_each_time(self):
        password = "same_password"
        h1 = hash_password(password)
        h2 = hash_password(password)
        assert h1 != h2  # bcrypt uses random salt
        assert verify_password(password, h1)
        assert verify_password(password, h2)
