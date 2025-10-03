# qwen_client.py
import os

from openai import OpenAI

MODEL = os.getenv("MODEL", "qwen3-coder-plus")


class QwenClient:
    def __init__(self) -> None:
        self.client = self._initialize_client()

    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client with Qwen credentials"""
        return OpenAI()
