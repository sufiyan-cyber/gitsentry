"""Unit tests for cryptographic HMAC signature verification."""

import pytest
from common.crypto import generate_github_signature, verify_github_signature


def test_generate_and_verify_valid_signature():
    payload = b'{"action":"opened","number":1}'
    secret = "my_super_secret_webhook_key_123"

    signature = generate_github_signature(payload, secret)
    assert signature.startswith("sha256=")
    assert len(signature) == 7 + 64  # 'sha256=' (7) + 64 hex chars

    # Verification should succeed
    assert verify_github_signature(payload, signature, secret) is True


def test_verify_signature_tampered_payload():
    payload = b'{"action":"opened","number":1}'
    tampered_payload = b'{"action":"opened","number":2}'
    secret = "my_super_secret_webhook_key_123"

    signature = generate_github_signature(payload, secret)
    assert verify_github_signature(tampered_payload, signature, secret) is False


def test_verify_signature_wrong_secret():
    payload = b'{"action":"opened","number":1}'
    secret = "correct_secret"
    wrong_secret = "wrong_secret"

    signature = generate_github_signature(payload, secret)
    assert verify_github_signature(payload, signature, wrong_secret) is False


def test_verify_signature_missing_header():
    payload = b'{"action":"opened","number":1}'
    secret = "correct_secret"

    assert verify_github_signature(payload, None, secret) is False
    assert verify_github_signature(payload, "", secret) is False


def test_verify_signature_malformed_header():
    payload = b'{"action":"opened","number":1}'
    secret = "correct_secret"

    # Missing sha256= prefix
    raw_hex = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    assert verify_github_signature(payload, raw_hex, secret) is False

    # Empty hex after prefix
    assert verify_github_signature(payload, "sha256=", secret) is False

    # Wrong prefix format
    assert verify_github_signature(payload, "sha1=abcdef123", secret) is False


def test_verify_signature_empty_secret():
    payload = b'{"action":"opened","number":1}'
    assert verify_github_signature(payload, "sha256=abcdef", "") is False


def test_verify_signature_unicode_payload():
    payload = '{"message": "Hello 🚀 Security Check 🛡️"}'.encode("utf-8")
    secret = "unicode_secret_🔑"

    sig = generate_github_signature(payload, secret)
    assert verify_github_signature(payload, sig, secret) is True
