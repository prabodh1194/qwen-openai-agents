#!/usr/bin/env python3
"""
Script to read Qwen OAuth credentials and initialize an OpenAI client
"""

import json
from pathlib import Path
from openai import OpenAI


def load_qwen_creds():
    """Load OAuth credentials from Qwen config file"""
    creds_path = Path.home() / ".qwen" / "oauth_creds.json"

    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")

    try:
        with open(creds_path, "r") as f:
            creds = json.load(f)
        return creds
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in credentials file: {e}")
    except Exception as e:
        raise Exception(f"Error reading credentials file: {e}")


def create_openai_client(creds):
    """Create OpenAI client from Qwen credentials"""

    # Extract relevant fields from creds
    # Note: You may need to adjust these field names based on actual structure
    api_key = creds.get("access_token") or creds.get("api_key") or creds.get("token")

    if not api_key:
        raise ValueError(
            "No API key found in credentials. Available keys: "
            + str(list(creds.keys()))
        )

    # Initialize OpenAI client
    client_kwargs = {
        "api_key": api_key,
        "base_url": "https://portal.qwen.ai/v1"
    }

    client = OpenAI(**client_kwargs)
    return client


def main():
    # Load credentials
    print("Loading Qwen OAuth credentials...")
    creds = load_qwen_creds()
    print("✓ Credentials loaded successfully")

    # Debug: print available credential keys (without values)
    print(f"Available credential fields: {list(creds.keys())}")

    # Create OpenAI client
    print("Initializing OpenAI client...")
    client = create_openai_client(creds)
    print("✓ OpenAI client created")

    return client


if __name__ == "__main__":
    client = main()

    # Example usage if client was created successfully
    if client:
        print("\n" + "=" * 50)
        print("Client ready for use! Example:")
        print("=" * 50)

        # Uncomment to test with actual API call
        response = client.chat.completions.create(
            model="qwen3-coder-plus",  # Adjust model name as needed
            messages=[{"role": "user", "content": "Hello, world!"}],
            max_tokens=50,
        )
        print("Test response:", response.choices[0].message.content)
