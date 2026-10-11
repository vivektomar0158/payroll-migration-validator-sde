"""API-key auth for the backend-service layer. The DA version has no auth (single-user
analyst tool); as a standalone service this needs a caller identity check."""
import os
from fastapi import Header, HTTPException

API_KEY_ENV = "MIGRATION_VALIDATOR_API_KEY"


def require_api_key(x_api_key: str = Header(default=None)):
    expected = os.environ.get(API_KEY_ENV)
    if not expected:
        # No key configured (local/dev default) — auth is a no-op so the service still runs out of the box.
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")
