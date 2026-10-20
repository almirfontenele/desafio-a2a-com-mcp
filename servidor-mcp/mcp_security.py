"""
Security and HMAC-SHA256 Token Service for MRTR requestState.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from mcp_config import get_request_state_secret, TOKEN_EXPIRATION_SECONDS


class HMACStateTokenService:
    """
    Manages generation and cryptographic verification of opaque MRTR requestState tokens.
    """

    def __init__(self, secret: str | None = None) -> None:
        self._secret = secret or get_request_state_secret()

    def _get_secret(self) -> str:
        return self._secret

    def generate_token(self, args: dict[str, Any], ttl_seconds: int = TOKEN_EXPIRATION_SECONDS) -> str:
        secret = self._get_secret()
        payload = {
            "sala": args.get("sala"),
            "inicio": args.get("inicio"),
            "fim": args.get("fim"),
            "responsavel": args.get("responsavel"),
            "exp": time.time() + ttl_seconds,
            "nonce": secrets.token_hex(16),
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(payload_json).decode("ascii").rstrip("=")
        sig = hmac.new(secret.encode("utf-8"), b64_payload.encode("ascii"), hashlib.sha256).hexdigest()
        return f"{b64_payload}.{sig}"

    def verify_token(self, token: str) -> dict[str, Any] | None:
        if not token or "." not in token:
            return None
        secret = self._get_secret()
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None
        b64_payload, sig = parts[0], parts[1]
        expected_sig = hmac.new(secret.encode("utf-8"), b64_payload.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        padding = "=" * (-len(b64_payload) % 4)
        try:
            payload_json = base64.urlsafe_b64decode((b64_payload + padding).encode("ascii")).decode("utf-8")
            payload = json.loads(payload_json)
        except Exception:
            return None

        if time.time() > payload.get("exp", 0):
            return None

        return payload
