"""
AWS Lambda handler for BSE News Analyzer with smart_open integration.
"""
import json
from typing import Any

import cli.bse_news
from services.bse_analysis_service import BSEAnalysisService


def lambda_handler(
    records: dict[str, list[dict[str, Any]]], context: Any
) -> dict[str, Any]:
    """
    Lambda function handler for analyzing BSE news.

    Expected event format:
    {
        "company_name": "Company Name",
        "force": false  # Optional: true or false
    }
    """

    event = json.loads(records["Records"][0]["body"])

    # Extract company name from event
    company_name = event.get("company_name")

    if not company_name:
        error_analysis = {
            "status": "error",
            "display_message": "company_name parameter is required",
        }
        return BSEAnalysisService.format_api_response(error_analysis)

    # Get force parameter from event, default to True for Lambda
    force = event.get("force", False)

    try:
        # Call the CLI function directly
        analysis = cli.bse_news.scrape_bse_news(company_name, force)

        # Return formatted API response
        return BSEAnalysisService.format_api_response(
            analysis, analysis.get("s3_location")
        )

    except Exception as e:
        # Return error response
        error_analysis = {"status": "error", "display_message": str(e)}
        return BSEAnalysisService.format_api_response(error_analysis)
