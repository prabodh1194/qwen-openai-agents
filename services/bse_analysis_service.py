"""
Shared service layer for BSE news analysis that eliminates duplication
between CLI and Lambda implementations.
"""
import json
import os
from typing import Any
from client.qwen import QwenClient
from tools.web_fetch import BSENewsAgent, ApprovalMode


def normalize_company_name(company_name: str) -> str:
    """
    Normalize company name for use as DynamoDB partition key.

    Args:
        company_name: Original company name

    Returns:
        Normalized company name
    """
    # Convert to lowercase and remove extra whitespace
    return " ".join(company_name.lower().split())


def track_scrape_result(company_name: str, success: bool) -> None:
    """
    Track the result of a BSE news scrape in DynamoDB.

    Args:
        company_name: Name of the company that was analyzed
        success: Whether the analysis was successful
    """

    try:
        import boto3
        from datetime import datetime, timedelta

        table_name = "bse-news-analyzer-tracker"

        # Initialize DynamoDB client
        dynamodb = boto3.resource(
            "dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        table = dynamodb.Table(table_name)

        # Normalize company name
        normalized_name = normalize_company_name(company_name)

        # Create ISO timestamp
        created_at = datetime.utcnow().isoformat() + "Z"

        # Calculate TTL (7 days from now)
        ttl = int((datetime.utcnow() + timedelta(days=7)).timestamp())

        # Put item in DynamoDB
        table.put_item(
            Item={
                "pk": datetime.utcnow().date().isoformat(),
                "sk": normalized_name,
                "company_name": normalized_name,
                "created_at": created_at,
                "success": success,
                "ttl": ttl,
            }
        )

    except Exception:
        # We don't want to fail the entire function if DynamoDB tracking fails
        pass


def analyze_company(company_name: str, s3_bucket: str, force: bool = False) -> dict:
    """
    Analyze BSE news for a company.

    This function is used by both CLI and Lambda implementations
    to ensure identical functionality including:
    - Checking if analysis already exists (unless force=True)
    - Performing the analysis
    - Saving results to S3

    Args:
        company_name: Name of the company to analyze
        s3_bucket: Optional S3 bucket name for saving results
        force: Whether to force re-analysis even if data exists

    Returns:
        Analysis results dictionary
    """

    # Check if analysis already exists (unless force flag is used)
    if not force and BSEAnalysisService.check_analysis_exists(company_name, s3_bucket):
        return {
            "status": "skipped",
            "display_message": f"Analysis already exists for {company_name}. Use force to re-run.",
            "company": company_name,
        }

    # Initialize service with S3 credentials (same for both CLI and Lambda)
    service = BSEAnalysisService()

    # Perform analysis
    analysis = service.analyze_company(company_name)

    saved_location = service.save_analysis(analysis, s3_bucket)
    analysis["s3_location"] = saved_location

    return analysis


class BSEAnalysisService:
    """Service layer for BSE news analysis operations"""

    def __init__(self) -> None:
        """
        Initialize the service with optional credentials URI.

        """
        self.qwen = QwenClient()
        self.agent = BSENewsAgent(self.qwen.client, ApprovalMode.AUTO_EDIT)

    def analyze_company(self, company_name: str) -> dict:
        """
        Analyze BSE news for a given company.

        Args:
            company_name: Name of the company to analyze

        Returns:
            Analysis results dictionary
        """
        return self.agent.analyze_company_news(company_name)

    def save_analysis(self, analysis: dict, s3_bucket: str) -> str:
        """
        Save analysis results to S3 URI.

        Args:
            analysis: Analysis results to save
            s3_bucket: S3 bucket name

        Returns:
            S3 URI where analysis was saved
        """
        return self.agent.save_analysis_to_file(analysis, s3_bucket)

    @staticmethod
    def check_analysis_exists(company_name: str, s3_bucket: str) -> bool:
        """
        Check if analysis already exists for the given company in S3.

        Args:
            company_name: Name of the company to check
            s3_bucket: S3 bucket name

        Returns:
            True if analysis exists, False otherwise
        """
        from datetime import datetime
        from smart_open import open
        import json

        # Generate the expected file path
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = BSENewsAgent._generate_filename(company_name)
        file_path = f"{s3_bucket}/outputs/{date_str}/{filename}"

        # Try to open the file to check if it exists
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Try to parse JSON to ensure it's a valid analysis file
                json.load(f)
            return True
        except Exception as e:
            # File doesn't exist or is invalid
            print(e)
            return False

    @staticmethod
    def format_console_response(analysis: dict[str, Any], filepath: str) -> str:
        """
        Format analysis results for console output.

        Args:
            analysis: Analysis results
            filepath: Path where analysis was saved

        Returns:
            Formatted console output string
        """
        if analysis["status"] != "success":
            return f"Error: {analysis['display_message']}"

        output = []
        output.append("=" * 60)
        output.append(f"ANALYSIS FOR {analysis['company'].upper()}")
        output.append("=" * 60)
        output.append(f"Overall Sentiment: {analysis['overall_sentiment']}/5")
        output.append(f"Confidence: {analysis['confidence']}%")
        output.append(f"Articles Analyzed: {analysis['articles_analyzed']}")

        if analysis.get("analysis_reasoning"):
            output.append(f"\nReasoning: {analysis['analysis_reasoning']}")

        if analysis["key_positive_drivers"]:
            output.append("\nKey Positive Drivers:")
            for driver in analysis["key_positive_drivers"]:
                output.append(f"  • {driver}")

        if analysis["key_risk_factors"]:
            output.append("\nKey Risk Factors:")
            for risk in analysis["key_risk_factors"]:
                output.append(f"  • {risk}")

        output.append(f"\nDetailed analysis saved to S3: {filepath}")

        return "\n".join(output)

    @staticmethod
    def format_api_response(
        analysis: dict[str, Any], s3_location: str | None = None
    ) -> dict[str, Any]:
        """
        Format analysis results for API response.

        Args:
            analysis: Analysis results
            s3_location: Optional S3 location where analysis was saved

        Returns:
            Formatted API response dictionary
        """
        if analysis["status"] != "success":
            return {
                "statusCode": 400
                if "parameter is required" in analysis.get("display_message", "")
                else 500,
                "body": json.dumps(
                    {"error": analysis["display_message"], "status": "error"}
                ),
                "headers": {"Content-Type": "application/json"},
            }

        response_body = {
            "company": analysis["company"],
            "analysis_date": analysis["analysis_date"],
            "overall_sentiment": analysis["overall_sentiment"],
            "confidence": analysis["confidence"],
            "articles_analyzed": analysis["articles_analyzed"],
            "key_positive_drivers": analysis["key_positive_drivers"],
            "key_risk_factors": analysis["key_risk_factors"],
            "status": "success",
        }

        if analysis.get("analysis_reasoning"):
            response_body["analysis_reasoning"] = analysis["analysis_reasoning"]

        if s3_location:
            response_body["s3_location"] = s3_location

        return {
            "statusCode": 200,
            "body": json.dumps(response_body, indent=2),
            "headers": {"Content-Type": "application/json"},
        }
