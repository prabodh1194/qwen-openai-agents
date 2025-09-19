"""
CLI module for BSE News Scraper
"""
import logging

import click
from typing import Any

from services.bse_analysis_service import (
    analyze_company,
    track_scrape_result,
    BSEAnalysisService,
)


def scrape_bse_news(company_name: str, force: bool = False) -> dict[str, Any]:
    """
    Scrape and analyze BSE news for a given company.

    This function can be called directly from CLI or Lambda.

    Args:
        company_name: Name of the company to analyze
        force: Whether to force re-analysis even if data exists in S3
        table_name: Optional DynamoDB table name (for Lambda)

    Returns:
        Analysis results dictionary
    """
    table_name = "bse-news-analyzer-tracker"

    try:
        # Perform analysis using unified function with S3 credentials
        analysis = analyze_company(
            company_name=company_name,
            s3_bucket="s3://bse-news-analyzer-data",
            force=force,
        )

        # Track result in DynamoDB (if table name is available)
        track_scrape_result(company_name, analysis["status"] == "success", table_name)

        return analysis

    except Exception as e:
        # Track failure in DynamoDB (if table name is available)
        track_scrape_result(company_name, False, table_name)
        raise e


@click.command()  # type: ignore[misc]
@click.argument("company_name", type=str)  # type: ignore[misc]
@click.option(
    "--force", is_flag=True, help="Force re-analysis even if data exists in S3"
)  # type: ignore[misc]
def scrape_bse_news_cli(company_name: str, force: bool) -> None:
    """Scrape and analyze BSE news for a given company (CLI version)."""
    try:
        print(f"Analyzing BSE news for: {company_name}")

        # Perform analysis using unified function with S3 credentials
        analysis = scrape_bse_news(company_name, force)

        if analysis["status"] == "success":
            # Display formatted results
            output = BSEAnalysisService.format_console_response(
                analysis, analysis.get("s3_location", "unknown")
            )
            print(f"\n{output}")
        elif analysis["status"] == "skipped":
            print(analysis["display_message"])
        else:
            print(f"Error: {analysis['display_message']}")

    except Exception as e:
        print(f"Error: {str(e)}")
        logging.exception(e)
