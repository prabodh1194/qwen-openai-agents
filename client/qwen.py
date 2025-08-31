# qwen_client.py
from pathlib import Path
import json
import requests
from datetime import datetime, timezone
from openai import OpenAI

MODEL = "qwen3-coder-plus"


class QwenClient:
    def __init__(self) -> None:
        self.creds_path = Path.home() / ".qwen" / "oauth_creds.json"
        self.credentials = self._load_credentials()
        self._display_token_expiration()
        self.client = self._initialize_client()

    def _load_credentials(self) -> dict:
        """Load OAuth credentials from Qwen config file"""
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {self.creds_path}")

        try:
            with open(self.creds_path, "r") as f:
                return dict(json.load(f))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials file: {e}")
        except Exception as e:
            raise Exception(f"Error reading credentials file: {e}")

    def _display_token_expiration(self) -> None:
        """Display token expiration information if available"""
        # Check for expiration timestamp in various possible fields
        exp_key = "expiry_date"
        exp_value = self.credentials.get(exp_key)

        if not exp_value:
            print("[QwenClient] No expiration information found in credentials")
            return

        exp_time = float(exp_value)

        # Convert milliseconds to seconds if needed
        if exp_time > 1e10:
            exp_time = exp_time / 1000

        # Calculate and display time remaining
        now = datetime.now(timezone.utc).timestamp()
        seconds_left = exp_time - now

        if seconds_left <= 0:
            print("[QwenClient] WARNING: Token has expired!")
            return

        # Convert to days, hours, minutes
        days = int(seconds_left // 86400)
        hours = int((seconds_left % 86400) // 3600)
        minutes = int((seconds_left % 3600) // 60)

        print(
            f"[QwenClient] Token expires in {days} days, {hours} hours, {minutes} minutes"
        )

    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client with Qwen credentials"""
        api_key = (
            self.credentials.get("access_token")
            or self.credentials.get("api_key")
            or self.credentials.get("token")
        )

        if not api_key:
            raise ValueError(
                "No API key found in credentials. Available keys: "
                + str(list(self.credentials.keys()))
            )

        return OpenAI(api_key=api_key, base_url="https://portal.qwen.ai/v1")

    def refresh_token(self) -> dict:
        """
        Refresh Qwen API tokens using the refresh token.

        Returns:
            Updated credentials dictionary with new access token and possibly new refresh token
        """
        refresh_token = self.credentials.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh token available for token refresh")

        # Hardcoded client ID as mentioned in the documentation
        client_id = "f0304373b74a44d2b584a3fb70ca9e56"

        # Prepare refresh request
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        }

        # Make POST request to token endpoint
        response = requests.post(
            "https://chat.qwen.ai/api/v1/oauth2/token",
            data=refresh_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Raise exception for bad status codes
        response.raise_for_status()

        # Parse response
        token_data = response.json()

        # Create updated credentials
        new_credentials = self.credentials.copy()

        # Update access token
        if "access_token" in token_data:
            new_credentials["access_token"] = token_data["access_token"]
        elif "token" in token_data:
            new_credentials["access_token"] = token_data["token"]
        elif "api_key" in token_data:
            new_credentials["access_token"] = token_data["api_key"]

        # Update refresh token if provided (token rotation)
        if "refresh_token" in token_data:
            new_credentials["refresh_token"] = token_data["refresh_token"]

        # Update expiration time
        if "expires_in" in token_data:
            # Calculate expiration timestamp
            now = datetime.now(timezone.utc).timestamp()
            expiration_timestamp = now + token_data["expires_in"]
            new_credentials["expiry_date"] = (
                expiration_timestamp * 1000
            )  # Store as milliseconds

        return new_credentials


if __name__ == "__main__":
    qwen_client = QwenClient()
    response = qwen_client.client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "Hello, Qwen! Can you write a Python function to add two numbers?",
            }
        ],
        max_tokens=150,
        temperature=0.5,
    )
    print(response.choices[0].message.content)
