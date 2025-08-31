"""
CLI module for BSE News Scraper
"""

import click

from client.qwen import QwenClient
from tools.web_fetch import ApprovalMode, BSENewsAgent


@click.command()
@click.argument("company_name")
def scrape_bse_news(company_name: str) -> None:
    """Scrape and analyze BSE news for a given company."""
    try:
        # Initialize client
        click.echo("Initializing Qwen client...")
        qwen = QwenClient()
        click.echo("✓ Client initialized")

        # Initialize BSE News Agent
        click.echo(f"Analyzing BSE news for: {company_name}")
        agent = BSENewsAgent(qwen.client, ApprovalMode.AUTO_EDIT)
        analysis = agent.analyze_company_news(company_name)

        if analysis["status"] == "success":
            click.echo("\n" + "=" * 60)
            click.echo(f"ANALYSIS FOR {company_name.upper()}")
            click.echo("=" * 60)
            click.echo(analysis["analysis"])
        else:
            click.echo(f"Error: {analysis['display_message']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
