"""PKCE helpers for MCP agent OAuth (RFC 7636)."""

import base64
import hashlib
import secrets


class PKCEError(Exception):
    """Raised when PKCE verification fails."""


class PKCEService:
    """Generate and verify PKCE code verifiers and challenges."""

    VERIFIER_BYTES = 32

    @staticmethod
    def generate_code_verifier() -> str:
        """Return a high-entropy URL-safe code verifier."""
        return secrets.token_urlsafe(PKCEService.VERIFIER_BYTES)

    @staticmethod
    def generate_code_challenge(verifier: str, *, method: str = "S256") -> str:
        """Derive the code challenge from a verifier."""
        if method != "S256":
            msg = f"Unsupported code challenge method: {method}"
            raise PKCEError(msg)
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    @staticmethod
    def verify_code_challenge(
        *,
        verifier: str,
        challenge: str,
        method: str = "S256",
    ) -> None:
        """Raise ``PKCEError`` when the verifier does not match the challenge."""
        expected = PKCEService.generate_code_challenge(verifier, method=method)
        if not secrets.compare_digest(expected, challenge):
            raise PKCEError("PKCE code_verifier does not match code_challenge")
