from typing import Any

from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import get_settings


def verify_google_id_token(credential: str) -> dict[str, Any]:
    """Verify a Google Identity Services credential for this application."""
    client_id = get_settings().google_client_id
    if not client_id:
        raise ValueError("Google sign-in is not configured")
    claims = id_token.verify_oauth2_token(credential, requests.Request(), client_id)
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValueError("Invalid Google token issuer")
    if claims.get("email_verified") is not True:
        raise ValueError("Google email is not verified")
    if not claims.get("sub") or not claims.get("email"):
        raise ValueError("Google token is missing required claims")
    return claims
