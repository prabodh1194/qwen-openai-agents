"""
CLI module for analyzing all stock analyses for a given date and categorizing them
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import click
import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm


@click.command()  # type: ignore[misc]
@click.argument("date_str", type=str, required=False)  # type: ignore[misc]
@click.option(
    "--s3-bucket", type=str, default="bse-news-analyzer-data", help="S3 bucket name"
)  # type: ignore[misc]
@click.option("--s3-prefix", type=str, default="outputs", help="S3 prefix for outputs")  # type: ignore[misc]
@click.option(
    "--local-path", type=str, help="Local path to read analyses from instead of S3"
)  # type: ignore[misc]
def analyze_stocks(
    date_str: str, s3_bucket: str, s3_prefix: str, local_path: str
) -> None:
    """Analyze all stock analyses for a given date and categorize as buy/hold/sell."""
    try:
        # If no date provided, use today's date
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        click.echo(f"Analyzing stock analyses for date: {date_str}")

        # Get all analysis files for the date
        if local_path:
            analyses = _get_local_analyses(local_path, date_str)
        else:
            analyses = _get_s3_analyses(s3_bucket, s3_prefix, date_str)

        if not analyses:
            click.echo("No analyses found for the specified date.")
            return

        # Categorize stocks
        buy_stocks, hold_stocks, sell_stocks = _categorize_stocks(analyses)

        # Display results
        _display_results(buy_stocks, hold_stocks, sell_stocks, date_str)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


def _get_s3_analyses(bucket: str, prefix: str, date_str: str) -> List[Dict]:
    """Get all analysis files from S3 for a given date."""
    try:
        s3 = boto3.client("s3")
        s3_path = f"{prefix}/{date_str}/"

        click.echo(f"Fetching analyses from s3://{bucket}/{s3_path}")

        response = s3.list_objects_v2(Bucket=bucket, Prefix=s3_path)

        analyses = []
        if "Contents" in response:
            # Create a progress bar for reading files
            contents = response["Contents"]
            for obj in tqdm(contents, desc="Reading analysis files", unit="file"):
                key = obj["Key"]
                if key.endswith(".json"):
                    try:
                        obj_data = s3.get_object(Bucket=bucket, Key=key)
                        content = obj_data["Body"].read().decode("utf-8")
                        analysis = json.loads(content)
                        analyses.append(analysis)
                    except Exception as e:
                        click.echo(f"Warning: Could not read {key}: {str(e)}")

        click.echo(f"Found {len(analyses)} analyses")
        return analyses

    except ClientError as e:
        click.echo(f"Error accessing S3: {str(e)}", err=True)
        return []
    except Exception as e:
        click.echo(f"Error fetching S3 analyses: {str(e)}", err=True)
        return []


def _get_local_analyses(base_path: str, date_str: str) -> List[Dict]:
    """Get all analysis files from local directory for a given date."""
    try:
        analyses_path = Path(base_path) / "outputs" / date_str

        if not analyses_path.exists():
            click.echo(f"Local path does not exist: {analyses_path}")
            return []

        json_files = list(analyses_path.glob("*.json"))
        analyses = []

        # Create a progress bar for reading files
        for json_file in tqdm(json_files, desc="Reading analysis files", unit="file"):
            try:
                with open(json_file, "r") as f:
                    analysis = json.load(f)
                    analyses.append(analysis)
            except Exception as e:
                click.echo(f"Warning: Could not read {json_file}: {str(e)}")

        click.echo(f"Found {len(analyses)} analyses in local path")
        return analyses

    except Exception as e:
        click.echo(f"Error fetching local analyses: {str(e)}", err=True)
        return []


def _categorize_stocks(
    analyses: List[Dict]
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Categorize stocks based on sentiment scores."""
    buy_stocks = []  # sentiment > 2
    hold_stocks = []  # sentiment between -2 and 2
    sell_stocks = []  # sentiment < -2

    # Create a progress bar for categorizing stocks
    for analysis in tqdm(analyses, desc="Categorizing stocks", unit="analysis"):
        if analysis.get("status") != "success":
            continue

        # Skip stocks with 0 articles analyzed
        if analysis.get("articles_analyzed", 0) == 0:
            continue

        company = analysis.get("company", "Unknown")
        sentiment = analysis.get("overall_sentiment", 0)
        confidence = analysis.get("confidence", 0)

        stock_info = {
            "company": company,
            "sentiment": sentiment,
            "confidence": confidence,
            "articles_analyzed": analysis.get("articles_analyzed", 0),
            "reasoning": analysis.get("analysis_reasoning", ""),
        }

        if sentiment > 2:
            buy_stocks.append(stock_info)
        elif sentiment < -2:
            sell_stocks.append(stock_info)
        else:
            hold_stocks.append(stock_info)

    # Sort by sentiment (highest first for buy, lowest first for sell)
    buy_stocks.sort(key=lambda x: x["sentiment"], reverse=True)
    sell_stocks.sort(key=lambda x: x["sentiment"])

    return buy_stocks, hold_stocks, sell_stocks


def _display_results(
    buy_stocks: List[Dict],
    hold_stocks: List[Dict],
    sell_stocks: List[Dict],
    date_str: str,
) -> None:
    """Display categorized stocks in a formatted way."""
    click.echo("\n" + "=" * 80)
    click.echo(f"STOCK ANALYSIS SUMMARY FOR {date_str}".center(80))
    click.echo("=" * 80)

    # BUY stocks
    click.echo(f"\n📈 BUY STOCKS ({len(buy_stocks)} companies)")
    click.echo("-" * 60)
    if buy_stocks:
        for stock in buy_stocks:
            click.echo(f"  {stock['company']}")
            click.echo(
                f"    Sentiment: {stock['sentiment']}/5 | Confidence: {stock['confidence']}% | Articles: {stock['articles_analyzed']}"
            )
            if stock["reasoning"]:
                click.echo(f"    Reasoning: {stock['reasoning']}")
            click.echo()
    else:
        click.echo("  No strong buy recommendations found.")

    # HOLD stocks
    click.echo(f"\n⏸️ HOLD STOCKS ({len(hold_stocks)} companies)")
    click.echo("-" * 60)
    if hold_stocks:
        for stock in hold_stocks:
            click.echo(f"  {stock['company']}")
            click.echo(
                f"    Sentiment: {stock['sentiment']}/5 | Confidence: {stock['confidence']}% | Articles: {stock['articles_analyzed']}"
            )
            click.echo()
    else:
        click.echo("  No hold recommendations found.")

    # SELL stocks
    click.echo(f"\n📉 SELL STOCKS ({len(sell_stocks)} companies)")
    click.echo("-" * 60)
    if sell_stocks:
        for stock in sell_stocks:
            click.echo(f"  {stock['company']}")
            click.echo(
                f"    Sentiment: {stock['sentiment']}/5 | Confidence: {stock['confidence']}% | Articles: {stock['articles_analyzed']}"
            )
            if stock["reasoning"]:
                click.echo(f"    Reasoning: {stock['reasoning']}")
            click.echo()
    else:
        click.echo("  No strong sell recommendations found.")

    # Summary
    total_stocks = len(buy_stocks) + len(hold_stocks) + len(sell_stocks)
    click.echo("=" * 80)
    click.echo(
        f"SUMMARY: {len(buy_stocks)} Buy | {len(hold_stocks)} Hold | {len(sell_stocks)} Sell (of {total_stocks} total analyzed)"
    )
    click.echo("=" * 80)
