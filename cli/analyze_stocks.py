"""
CLI module for analyzing all stock analyses for a given date and categorizing them
"""
import json
from datetime import datetime
from typing import Dict, List, Any

import click
import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm
from smart_open import open
from client.qwen import QwenClient, MODEL


@click.command()  # type: ignore[misc]
@click.argument("date_str", type=str, required=False)  # type: ignore[misc]
@click.option(
    "--s3-bucket", type=str, default="bse-news-analyzer-data", help="S3 bucket name"
)  # type: ignore[misc]
@click.option("--s3-prefix", type=str, default="outputs", help="S3 prefix for outputs")  # type: ignore[misc]
@click.option(
    "--creds-path",
    type=str,
    default="~/.qwen/oauth_creds.json",
    help="Path to credentials file",
)  # type: ignore[misc]
@click.option(
    "--force-recompute",
    is_flag=True,
    help="Force recompute even if final analysis exists",
)  # type: ignore[misc]
def analyze_stocks(
    date_str: str,
    s3_bucket: str,
    s3_prefix: str,
    creds_path: str,
    force_recompute: bool,
) -> None:
    """Analyze all stock analyses for a given date and categorize as buy/hold/sell using LLM."""
    try:
        # If no date provided, use today's date
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        click.echo(f"Analyzing stock analyses for date: {date_str}")

        # Check if final analysis already exists
        final_analysis = None
        if not force_recompute:
            final_analysis_path = (
                f"s3://{s3_bucket}/{s3_prefix}/{date_str}/final_100_analysis.json"
            )
            final_analysis = _load_existing_analysis(final_analysis_path)

        if final_analysis:
            click.echo("Reusing existing final analysis.")
            _display_results(final_analysis, date_str)
            return

        # Get all analysis files for the date
        analyses = _get_s3_analyses(s3_bucket, s3_prefix, date_str)

        if not analyses:
            click.echo("No analyses found for the specified date.")
            return

        # Filter out stocks with 0 articles analyzed
        filtered_analyses = [
            analysis
            for analysis in analyses
            if analysis.get("status") == "success"
            and analysis.get("articles_analyzed", 0) > 0
        ]

        if not filtered_analyses:
            click.echo("No valid analyses found with articles analyzed.")
            return

        click.echo(
            f"Found {len(filtered_analyses)} valid analyses with articles. Performing LLM-based portfolio analysis..."
        )

        # Perform LLM-based analysis
        portfolio_analysis = _perform_llm_analysis(filtered_analyses, creds_path)

        # Add metadata to the portfolio analysis
        portfolio_analysis["analysis_date"] = date_str
        portfolio_analysis["total_companies_analyzed"] = len(filtered_analyses)

        # Save the final analysis to S3
        _save_s3_analysis(portfolio_analysis, s3_bucket, s3_prefix, date_str)

        # Display results
        _display_results(portfolio_analysis, date_str)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


def _load_existing_analysis(file_path: str) -> Dict[str, Any] | None:
    """Load existing final analysis if it exists."""
    try:
        with open(file_path, "r") as f:
            analysis = json.load(f)
            click.echo(f"Loaded existing analysis from: {file_path}")
            return dict(analysis)
    except Exception:
        # File doesn't exist or couldn't be loaded, which is fine
        return None


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
                if key.endswith(".json") and not key.endswith(
                    "final_100_analysis.json"
                ):
                    try:
                        s3_uri = f"s3://{bucket}/{key}"
                        with open(s3_uri, "r") as f:
                            analysis = json.load(f)
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


def _save_s3_analysis(
    portfolio_analysis: Dict[str, Any], bucket: str, prefix: str, date_str: str
) -> None:
    """Save the portfolio analysis to S3."""
    try:
        s3_uri = f"s3://{bucket}/{prefix}/{date_str}/final_100_analysis.json"

        with open(s3_uri, "w") as f:
            json.dump(portfolio_analysis, f, indent=2, ensure_ascii=False)

        click.echo(f"Final analysis saved to: {s3_uri}")
    except Exception as e:
        click.echo(f"Error saving S3 analysis: {str(e)}", err=True)


def _perform_llm_analysis(analyses: List[Dict], creds_path: str) -> Dict[str, Any]:
    """Perform LLM-based analysis of all stock analyses."""
    try:
        # Initialize Qwen client
        qwen = QwenClient(creds_path)
        client = qwen.client

        # Prepare the data for LLM analysis
        company_data = []
        for analysis in analyses:
            company_data.append(
                {
                    "company": analysis.get("company", "Unknown"),
                    "overall_sentiment": analysis.get("overall_sentiment", 0),
                    "confidence": analysis.get("confidence", 0),
                    "articles_analyzed": analysis.get("articles_analyzed", 0),
                    "analysis_reasoning": analysis.get("analysis_reasoning", ""),
                    "key_positive_drivers": analysis.get("key_positive_drivers", []),
                    "key_risk_factors": analysis.get("key_risk_factors", []),
                }
            )

        # Create prompt for LLM analysis
        prompt = f"""
You are a financial portfolio analyst. Analyze the following list of companies and their recent news sentiment analysis to provide portfolio recommendations.

COMPANIES ANALYZED:
{json.dumps(company_data, indent=2)}

TASK:
1. Categorize each company as BUY, HOLD, or SELL based on their sentiment analysis
2. Provide a brief rationale for each categorization
3. Identify overall market trends or themes from the data
4. Highlight any particularly strong buy or sell opportunities
5. Note any companies with high confidence scores that warrant special attention

CATEGORIZATION CRITERIA:
- BUY: Strong positive sentiment (>2) with high confidence OR moderate sentiment with very high confidence
- SELL: Strong negative sentiment (< -2) OR any sentiment with high risk factors
- HOLD: Moderate sentiment (-2 to 2) OR low confidence in either direction

OUTPUT FORMAT:
Return a JSON object with the following structure:
{{
    "buy_stocks": [
        {{
            "company": "Company Name",
            "rationale": "Brief rationale for buy recommendation"
        }}
    ],
    "hold_stocks": [
        {{
            "company": "Company Name",
            "rationale": "Brief rationale for hold recommendation"
        }}
    ],
    "sell_stocks": [
        {{
            "company": "Company Name",
            "rationale": "Brief rationale for sell recommendation"
        }}
    ],
    "market_trends": "Overall market trends or themes",
    "strong_opportunities": "Any particularly strong buy/sell opportunities",
    "high_confidence_notes": "Notes on companies with high confidence scores"
}}
"""

        click.echo("Performing LLM-based analysis...")
        # Call LLM for analysis
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial portfolio analyst expert.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        # Parse the response
        result = json.loads(response.choices[0].message.content)
        click.echo("LLM analysis completed successfully.")
        return dict(result)

    except Exception as e:
        click.echo(f"Error performing LLM analysis: {str(e)}", err=True)
        click.echo("Falling back to heuristic-based categorization...")
        # Fallback to heuristic-based categorization if LLM fails
        return _fallback_categorization(analyses)


def _fallback_categorization(analyses: List[Dict]) -> Dict[str, Any]:
    """Fallback heuristic-based categorization if LLM analysis fails."""
    click.echo("Using fallback heuristic-based analysis due to LLM error.")

    buy_stocks = []
    hold_stocks = []
    sell_stocks = []

    for analysis in analyses:
        company = analysis.get("company", "Unknown")
        sentiment = analysis.get("overall_sentiment", 0)
        confidence = analysis.get("confidence", 0)

        if sentiment > 2:
            buy_stocks.append(
                {
                    "company": company,
                    "rationale": f"Positive sentiment ({sentiment}/5) with {confidence}% confidence",
                }
            )
        elif sentiment < -2:
            sell_stocks.append(
                {
                    "company": company,
                    "rationale": f"Negative sentiment ({sentiment}/5) with {confidence}% confidence",
                }
            )
        else:
            hold_stocks.append(
                {
                    "company": company,
                    "rationale": f"Neutral sentiment ({sentiment}/5) with {confidence}% confidence",
                }
            )

    # Sort by sentiment (highest first for buy, lowest first for sell)
    buy_stocks.sort(key=lambda x: x["rationale"], reverse=True)
    sell_stocks.sort(key=lambda x: x["rationale"])

    return {
        "buy_stocks": buy_stocks,
        "hold_stocks": hold_stocks,
        "sell_stocks": sell_stocks,
        "market_trends": "Using fallback heuristic-based analysis due to LLM error",
        "strong_opportunities": "None identified with fallback method",
        "high_confidence_notes": "None identified with fallback method",
    }


def _display_results(portfolio_analysis: Dict[str, Any], date_str: str) -> None:
    """Display portfolio analysis results in a formatted way."""
    click.echo("\n" + "=" * 80)
    click.echo(f"PORTFOLIO ANALYSIS FOR {date_str}".center(80))
    click.echo("=" * 80)

    # BUY stocks
    buy_stocks = portfolio_analysis.get("buy_stocks", [])
    click.echo(f"\n📈 BUY RECOMMENDATIONS ({len(buy_stocks)} companies)")
    click.echo("-" * 60)
    if buy_stocks:
        for stock in buy_stocks:
            click.echo(f"  {stock['company']}")
            click.echo(f"    Rationale: {stock['rationale']}")
            click.echo()
    else:
        click.echo("  No strong buy recommendations found.")

    # HOLD stocks
    hold_stocks = portfolio_analysis.get("hold_stocks", [])
    click.echo(f"\n⏸️ HOLD RECOMMENDATIONS ({len(hold_stocks)} companies)")
    click.echo("-" * 60)
    if hold_stocks:
        for stock in hold_stocks:
            click.echo(f"  {stock['company']}")
            click.echo(f"    Rationale: {stock['rationale']}")
            click.echo()
    else:
        click.echo("  No hold recommendations found.")

    # SELL stocks
    sell_stocks = portfolio_analysis.get("sell_stocks", [])
    click.echo(f"\n📉 SELL RECOMMENDATIONS ({len(sell_stocks)} companies)")
    click.echo("-" * 60)
    if sell_stocks:
        for stock in sell_stocks:
            click.echo(f"  {stock['company']}")
            click.echo(f"    Rationale: {stock['rationale']}")
            click.echo()
    else:
        click.echo("  No sell recommendations found.")

    # Market trends and insights
    click.echo("\n📊 MARKET INSIGHTS")
    click.echo("-" * 60)
    click.echo(f"Market Trends: {portfolio_analysis.get('market_trends', 'N/A')}")
    click.echo(
        f"Strong Opportunities: {portfolio_analysis.get('strong_opportunities', 'N/A')}"
    )
    click.echo(
        f"High Confidence Notes: {portfolio_analysis.get('high_confidence_notes', 'N/A')}"
    )

    # Summary
    total_stocks = len(buy_stocks) + len(hold_stocks) + len(sell_stocks)
    click.echo("=" * 80)
    click.echo(
        f"SUMMARY: {len(buy_stocks)} Buy | {len(hold_stocks)} Hold | {len(sell_stocks)} Sell (of {total_stocks} total analyzed)"
    )
    click.echo("=" * 80)
