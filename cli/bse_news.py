"""
CLI module for BSE News Scraper
"""
from pathlib import Path

import click

from services.bse_analysis_service import BSEAnalysisService


@click.command()
@click.argument("company_name", type=str)
@click.option(
    "--force", is_flag=True, help="Force re-analysis even if data exists in S3"
)
def scrape_bse_news(company_name: str, force: bool) -> None:
    """Scrape and analyze BSE news for a given company."""
    try:
        # Initialize service
        click.echo("Initializing BSE analysis service...")
        service = BSEAnalysisService(str(Path.home() / ".qwen" / "oauth_creds.json"))
        click.echo("✓ Service initialized")

        # Check if analysis already exists (unless force flag is used)
        if not force:
            click.echo(f"Checking if analysis already exists for: {company_name}")
            if service.check_analysis_exists(company_name):
                click.echo(
                    f"✓ Analysis already exists for {company_name}. Skipping execution."
                )
                click.echo("Use --force to re-run analysis even if data exists.")
                return

        # Perform analysis
        click.echo(f"Analyzing BSE news for: {company_name}")
        analysis = service.analyze_company(company_name)

        # Save analysis to S3 (save all analyses, including placeholders for companies with no news)
        filepath = service.save_analysis(analysis, "s3://bse-news-analyzer-data")

        if analysis["status"] == "success":
            # Display formatted results
            output = service.format_console_response(analysis, filepath)
            click.echo(f"\n{output}")

        else:
            click.echo(f"Error: {analysis['display_message']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
