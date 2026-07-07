"""
Simple symmetric encryption for API keys stored in the custom_providers table.
Uses Fernet (AES-128-CBC) from the `cryptography` package if available,
falls back to base64 obfuscation if `cryptography` is not installed.

Set ENCRYPTION_KEY env var for real encryption. Generate one with:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os
import base64
import logging

logger = logging.getLogger(__name__)

_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
_fernet = None

try:
    from cryptography.fernet import Fernet
    if _ENCRYPTION_KEY:
        _fernet = Fernet(_ENCRYPTION_KEY.encode())
        logger.info("✅ API key encryption enabled (Fernet)")
    else:
        logger.warning("⚠️  ENCRYPTION_KEY not set — API keys stored with base64 obfuscation only")
except ImportError:
    logger.warning("⚠️  `cryptography` not installed — API keys stored with base64 obfuscation only")


def encrypt_key(plaintext: str) -> str:
    """Encrypt an API key for storage."""
    if _fernet:
        return _fernet.encrypt(plaintext.encode()).decode()
    # Fallback: base64 encode (NOT secure, just obfuscation)
    return "b64:" + base64.b64encode(plaintext.encode()).decode()


def decrypt_key(ciphertext: str) -> str:
    """Decrypt a stored API key."""
    if not ciphertext:
        return ""
    # Handle legacy plaintext keys (no prefix, not Fernet token)
    if ciphertext.startswith("b64:"):
        return base64.b64decode(ciphertext[4:]).decode()
    if _fernet:
        try:
            return _fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            # Likely a legacy plaintext key — return as-is
            return ciphertext
    # No encryption configured — assume plaintext
    return ciphertext
