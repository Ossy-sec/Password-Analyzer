"""
Argon2id password hashing.

Never store or compare plaintext passwords — always go through hash_password()
at registration time and verify_password() at login time.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Default parameters (time_cost, memory_cost, parallelism) follow argon2-cffi's
# own recommended defaults, which already target OWASP's current guidance.
_hasher = PasswordHasher()


def hash_password(plaintext_password: str) -> str:
    return _hasher.hash(plaintext_password)


def verify_password(password_hash: str, plaintext_password: str) -> bool:
    try:
        _hasher.verify(password_hash, plaintext_password)
        return True
    except VerifyMismatchError:
        return False
