"""
AWS Lambda handler for BSE News Analyzer with smart_open integration.
"""
import os
from typing import Any

# Import from the main application
from services.bse_analysis_service import BSEAnalysisService


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler for analyzing BSE news.

    Expected event format:
    {
        "company_name": "Company Name",
        "output_format": "json"  # Optional: "json" or "text"
    }
    """

    try:
        # Extract company name from event
        company_name = event.get("company_name") or event.get(
            "queryStringParameters", {}
        ).get("company_name")

        if not company_name:
            error_analysis = {
                "status": "error",
                "display_message": "company_name parameter is required",
            }
            return BSEAnalysisService.format_api_response(error_analysis)

        print(f"Analyzing BSE news for: {company_name}")

        # Get S3 bucket from environment
        s3_bucket = os.environ.get("S3_BUCKET_NAME", "bse-news-analyzer-data")

        # Initialize service with S3 credentials URI
        creds_uri = f"s3://{s3_bucket}/.qwen/oauth_creds.json"
        service = BSEAnalysisService(creds_uri=creds_uri)

        # Perform analysis
        analysis = service.analyze_company(company_name)

        # Save analysis to S3
        if analysis["status"] == "success":
            # Generate filename using the shared method
            filename = service.agent._generate_filename(company_name)

            # Save to S3
            s3_output_uri = f"s3://{s3_bucket}/outputs/{filename}"
            service.save_analysis(analysis, s3_output_uri)

            print(f"Analysis saved to: {s3_output_uri}")
            analysis["s3_location"] = s3_output_uri

        # Return formatted API response
        return service.format_api_response(analysis, analysis.get("s3_location"))

    except Exception as e:
        print(f"Error in Lambda function: {str(e)}")

        # Return error response
        # Get S3 bucket from environment
        s3_bucket = os.environ.get("S3_BUCKET_NAME", "bse-news-analyzer-data")
        # Initialize service with S3 credentials URI even for error handling
        creds_uri = f"s3://{s3_bucket}/.qwen/oauth_creds.json"
        service = BSEAnalysisService(creds_uri=creds_uri)
        error_analysis = {"status": "error", "display_message": str(e)}
        return service.format_api_response(error_analysis)
