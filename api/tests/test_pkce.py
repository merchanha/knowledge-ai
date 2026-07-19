"""Tests for PKCE code verifier and challenge helpers."""

import pytest

from knowledge_ai.services.pkce import PKCEError, PKCEService


def test_generate_code_challenge_is_deterministic() -> None:
    verifier = PKCEService.generate_code_verifier()
    challenge = PKCEService.generate_code_challenge(verifier)
    assert challenge == PKCEService.generate_code_challenge(verifier)


def test_verify_code_challenge_accepts_matching_verifier() -> None:
    verifier = PKCEService.generate_code_verifier()
    challenge = PKCEService.generate_code_challenge(verifier)
    PKCEService.verify_code_challenge(verifier=verifier, challenge=challenge)


def test_verify_code_challenge_rejects_mismatch() -> None:
    verifier = PKCEService.generate_code_verifier()
    challenge = PKCEService.generate_code_challenge(verifier)
    with pytest.raises(PKCEError):
        PKCEService.verify_code_challenge(
            verifier=PKCEService.generate_code_verifier(),
            challenge=challenge,
        )
