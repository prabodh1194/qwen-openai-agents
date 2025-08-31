# qwen_client.py
from pathlib import Path
import json
from openai import OpenAI

MODEL = "qwen3-coder-plus"


class QwenClient:
    def __init__(self) -> None:
        self.creds_path = Path.home() / ".qwen" / "oauth_creds.json"
        self.credentials = self._load_credentials()
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
