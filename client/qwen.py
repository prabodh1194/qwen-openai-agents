# qwen_client.py
from pathlib import Path
import json
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
        exp_key = None
        for key in ["expires_at", "expiration", "expires_in", "expire_time"]:
            if key in self.credentials:
                exp_key = key
                break
        
        if not exp_key:
            print("[QwenClient] No expiration info found in credentials")
            return
            
        try:
            exp_value = self.credentials[exp_key]
            
            # Parse the expiration time
            if isinstance(exp_value, str):
                # Try parsing as timestamp string first
                if exp_value.isdigit():
                    exp_time = float(exp_value)
                else:
                    # Try parsing as ISO format
                    exp_time = datetime.fromisoformat(exp_value.replace("Z", "+00:00")).timestamp()
            elif isinstance(exp_value, (int, float)):
                exp_time = float(exp_value)
            else:
                print(f"[QwenClient] Unknown expiration format: {exp_value}")
                return
                
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
            
            print(f"[QwenClient] Token expires in {days} days, {hours} hours, {minutes} minutes")
            
        except Exception as e:
            print(f"[QwenClient] Could not parse expiration info: {e}")

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
