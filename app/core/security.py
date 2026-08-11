"""API key generation and hashing.

HMAC-SHA256 (not bcrypt/argon2) is used deliberately: an API key generated
via secrets.token_urlsafe(32) already has 256 bits of entropy, so bcrypt's
deliberate slowness (which defends low-entropy human-chosen passwords)
buys nothing here while taxing every authenticated request. Worse, bcrypt's
per-hash salt makes indexed lookup impossible - the only thing presented on
a request is the key itself, so verifying it would mean an O(n) scan
checking every user's hash. HMAC-SHA256 is deterministic, so lookup is a
plain indexed `WHERE hashed_api_key = :digest`.
"""
import hashlib
import hmac
import secrets

from app.core.config import settings

API_KEY_PREFIX = "rsag_"


def generate_api_key() -> str:
    """Generate a new raw API key. Shown to the caller exactly once."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    """Deterministically hash a raw API key for storage/lookup."""
    return hmac.new(
        settings.api_key_pepper.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
