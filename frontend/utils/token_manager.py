import jwt
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict


class TokenManager:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def is_token_expired(self, token: str) -> bool:
        """Check if the JWT token is expired"""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = datetime.fromtimestamp(payload['exp'])
            return datetime.utcnow() >= exp
        except (jwt.InvalidTokenError, KeyError):
            return True

    def refresh_token_if_needed(self, current_token: str) -> Optional[str]:
        """Refresh the token if it's about to expire"""
        if not self.is_token_expired(current_token):
            return current_token

        try:
            response = requests.post(
                f"{self.api_url}/auth/refresh",
                headers={"Authorization": f"Bearer {current_token}"},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()["access_token"]
        except:
            pass
        return None

    def get_user_info(self, token: str) -> Optional[Dict]:
        """Get user information from the token"""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return {
                "user_id": payload.get("sub"),
                "exp": datetime.fromtimestamp(payload['exp']),
                "iat": datetime.fromtimestamp(payload['iat'])
            }
        except:
            return None
