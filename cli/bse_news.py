"""
CLI module for BSE News Scraper
"""

import click

from client.qwen import QwenClient
from tools.web_fetch import ApprovalMode, BSENewsAgent


@click.command()  # type: ignore[misc]
@click.argument("company_name", type=str)  # type: ignore[misc]
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
            # Save analysis to file
            filepath = agent.save_analysis_to_file(analysis)

            click.echo("\n" + "=" * 60)
            click.echo(f"ANALYSIS FOR {company_name.upper()}")
            click.echo("=" * 60)
            click.echo(f"Overall Sentiment: {analysis['overall_sentiment']}/5")
            click.echo(f"Confidence: {analysis['confidence']}%")
            click.echo(f"Articles Analyzed: {analysis['articles_analyzed']}")

            if analysis.get("analysis_reasoning"):
                click.echo(f"\nReasoning: {analysis['analysis_reasoning']}")

            if analysis["key_positive_drivers"]:
                click.echo("\nKey Positive Drivers:")
                for driver in analysis["key_positive_drivers"]:
                    click.echo(f"  • {driver}")

            if analysis["key_risk_factors"]:
                click.echo("\nKey Risk Factors:")
                for risk in analysis["key_risk_factors"]:
                    click.echo(f"  • {risk}")

            click.echo(f"\nDetailed analysis saved to: {filepath}")

        else:
            click.echo(f"Error: {analysis['display_message']}")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
