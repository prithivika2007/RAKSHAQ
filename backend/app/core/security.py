"""Security and authentication utilities for RAKSHAQ.

Implements Argon2id password/PIN hashing, constant-time verification,
and brute-force protection rate limiting.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

# Maximum consecutive failed PIN attempts allowed before locking
MAX_PIN_ATTEMPTS = 5
PIN_LOCKOUT_DURATION_MINUTES = 15

# Explicitly configure Argon2id with recommended parameters
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def hash_pin(pin: str) -> str:
    """Hash a raw PIN using Argon2id.

    Raw PINs are never logged or persisted in plaintext.
    """
    return _hasher.hash(pin)


def verify_pin(pin: str, hashed_pin: Optional[str]) -> bool:
    """Verify a raw PIN against an Argon2id hash in constant time."""
    if not hashed_pin:
        return False
    try:
        return _hasher.verify(hashed_pin, pin)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def is_pin_locked(pin_locked_until: Optional[datetime]) -> bool:
    """Check if PIN verification is currently locked due to rate limiting."""
    if pin_locked_until is None:
        return False
    now = datetime.now(timezone.utc)
    if pin_locked_until.tzinfo is None:
        pin_locked_until = pin_locked_until.replace(tzinfo=timezone.utc)
    return now < pin_locked_until


def calculate_lockout_expiry() -> datetime:
    """Calculate the expiration timestamp for a new lockout episode."""
    return datetime.now(timezone.utc) + timedelta(minutes=PIN_LOCKOUT_DURATION_MINUTES)
