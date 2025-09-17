"""
Shared service layer for BSE news analysis that eliminates duplication
between CLI and Lambda implementations.
"""
import json
from typing import Any
from client.qwen import QwenClient
from tools.web_fetch import BSENewsAgent, ApprovalMode


class BSEAnalysisService:
    """Service layer for BSE news analysis operations"""

    def __init__(self, creds_uri: str):
        """
        Initialize the service with optional credentials URI.

        Args:
            creds_uri: Optional URI for credentials (for Lambda with S3)
        """
        self.qwen = QwenClient(creds_uri=creds_uri)
        self.agent = BSENewsAgent(self.qwen.client, ApprovalMode.AUTO_EDIT)

    def analyze_company(self, company_name: str) -> dict[str, Any]:
        """
        Analyze BSE news for a given company.

        Args:
            company_name: Name of the company to analyze

        Returns:
            Analysis results dictionary
        """
        return self.agent.analyze_company_news(company_name)

    def save_analysis(
        self, analysis: dict[str, Any], s3_bucket: str = "bse-news-analyzer-data"
    ) -> str:
        """
        Save analysis results to S3 URI.

        Args:
            analysis: Analysis results to save
            s3_bucket: S3 bucket name

        Returns:
            S3 URI where analysis was saved
        """
        s3_uri = f"s3://{s3_bucket}"
        return self.agent.save_analysis_to_file(analysis, s3_uri)

    def check_analysis_exists(
        self, company_name: str, s3_bucket: str = "bse-news-analyzer-data"
    ) -> bool:
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
        s3_uri = f"s3://{s3_bucket}"
        filename = self.agent._generate_filename(company_name)
        file_path = f"{s3_uri}/outputs/{date_str}/{filename}"

        # Try to open the file to check if it exists
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # Try to parse JSON to ensure it's a valid analysis file
                json.load(f)
            return True
        except Exception:
            # File doesn't exist or is invalid
            return False

    def format_console_response(self, analysis: dict[str, Any], filepath: str) -> str:
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
