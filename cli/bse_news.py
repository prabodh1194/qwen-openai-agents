"""
CLI module for BSE News Scraper
"""
from pathlib import Path

import click

from services.bse_analysis_service import BSEAnalysisService


@click.command()  # type: ignore[misc]
@click.argument("company_name", type=str)  # type: ignore[misc]
def scrape_bse_news(company_name: str) -> None:
    """Scrape and analyze BSE news for a given company."""
    try:
        # Initialize service
        click.echo("Initializing BSE analysis service...")
        service = BSEAnalysisService(str(Path.home() / ".qwen" / "oauth_creds.json"))
        click.echo("✓ Service initialized")

        # Perform analysis
        click.echo(f"Analyzing BSE news for: {company_name}")
        analysis = service.analyze_company(company_name)

        if analysis["status"] == "success":
            # Save analysis to file
            filepath = service.save_analysis(analysis)

            # Display formatted results
            output = service.format_console_response(analysis, filepath)
            click.echo(f"\n{output}")

        else:
            click.echo(f"Error: {analysis['display_message']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
