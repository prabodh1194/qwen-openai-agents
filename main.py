# main.py
#!/usr/bin/env python3
"""
Script to initialize and test Qwen client
"""
from openai import OpenAI

from client.qwen import QwenClient

def main() -> OpenAI:
    # Initialize client
    print("Initializing Qwen client...")
    qwen = QwenClient()
    print("✓ Client initialized")

    return qwen.client

def test_client(oa_client: OpenAI) -> None:
    """Test the client with a simple completion"""
    print("\n" + "=" * 50)
    print("Testing client with a simple completion:")
    print("=" * 50)

    response = oa_client.chat.completions.create(
        model="qwen3-coder-plus",
        messages=[{"role": "user", "content": "Hello, world!"}],
        max_tokens=50,
    )
    print("Response:", response.choices[0].message.content)

if __name__ == "__main__":
    client = main()
    test_client(client)