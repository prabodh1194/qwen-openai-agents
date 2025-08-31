# Qwen Configuration

This project requires access to the Qwen API through an OpenAI-compatible interface.

## Credentials Setup

To use this tool, you need to set up your Qwen API credentials in a specific location:

1. Create a directory: `~/.qwen/`
2. Create a file called `oauth_creds.json` in that directory
3. Add your credentials in one of these formats:

### Option 1: API Key
```json
{
  "api_key": "your-qwen-api-key-here"
}
```

### Option 2: Access Token
```json
{
  "access_token": "your-qwen-access-token-here"
}
```

### Option 3: Token
```json
{
  "token": "your-qwen-token-here"
}
```

## Model Information

The project currently uses the `qwen3-coder-plus` model.

## Usage

Once you've set up your credentials, the tool will automatically load them from `~/.qwen/oauth_creds.json` and use them to authenticate with the Qwen API.