"""
CLI module for refreshing Qwen API tokens
"""

import click
import json

from client.qwen import QwenClient


@click.command()
def refresh_qwen_token() -> None:
    """Refresh Qwen API tokens using the refresh token."""
    try:
        click.echo("Refreshing Qwen API tokens...")
        qwen = QwenClient()

        # Check if we have a refresh token
        refresh_token = qwen.credentials.get("refresh_token")
        if not refresh_token:
            click.echo("No refresh token found in credentials.", err=True)
            raise click.Abort()

        # Perform token refresh
        new_credentials = qwen.refresh_token()

        # Save updated credentials
        with open(qwen.creds_path, "w") as f:
            json.dump(new_credentials, f, indent=2)

        click.echo("✓ Tokens refreshed successfully")
        click.echo(f"Updated credentials saved to {qwen.creds_path}")

    except Exception as e:
        click.echo(f"Error refreshing tokens: {str(e)}", err=True)
        raise click.Abort()
