"""
Shared service layer for BSE news analysis that eliminates duplication
between CLI and Lambda implementations.
"""
import json
from typing import Dict, Any, Optional
from client.qwen import QwenClient
from tools.web_fetch import BSENewsAgent, ApprovalMode


class BSEAnalysisService:
    """Service layer for BSE news analysis operations"""

    def __init__(self, creds_uri: Optional[str] = None):
        """
        Initialize the service with optional credentials URI.

        Args:
            creds_uri: Optional URI for credentials (for Lambda with S3)
        """
        self.qwen = QwenClient(creds_uri=creds_uri) if creds_uri else QwenClient()
        self.agent = BSENewsAgent(self.qwen.client, ApprovalMode.AUTO_EDIT)

    def analyze_company(self, company_name: str) -> Dict[str, Any]:
        """
        Analyze BSE news for a given company.

        Args:
            company_name: Name of the company to analyze

        Returns:
            Analysis results dictionary
        """
        return self.agent.analyze_company_news(company_name)

    def save_analysis(
        self, analysis: Dict[str, Any], output_uri: Optional[str] = None
    ) -> str:
        """
        Save analysis results to file or URI.

        Args:
            analysis: Analysis results to save
            output_uri: Optional URI for output (for Lambda with S3)

        Returns:
            Path or URI where analysis was saved
        """
        if output_uri:
            return self.agent.save_analysis_to_file(analysis, output_uri)
        else:
            return self.agent.save_analysis_to_file(analysis)

    def format_console_response(self, analysis: Dict[str, Any], filepath: str) -> str:
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

        output.append(f"\nDetailed analysis saved to: {filepath}")

        return "\n".join(output)

    def format_api_response(
        self, analysis: Dict[str, Any], s3_location: Optional[str] = None
    ) -> Dict[str, Any]:
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
