"""
AWS Lambda handler for BSE News Analyzer with S3 mountpoint support.
"""
import json
from typing import Dict, Any

# Import from the main application
from client.qwen import QwenClient


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
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
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "company_name parameter is required"}),
            }

        print(f"Analyzing BSE news for: {company_name}")

        # Initialize Qwen client (will use S3 mountpoint via $HOME/.qwen/)
        qwen = QwenClient()

        # Initialize BSE News Agent
        from tools.web_fetch import BSENewsAgent, ApprovalMode

        agent = BSENewsAgent(qwen.client, ApprovalMode.AUTO_EDIT)

        # Perform analysis
        analysis = agent.analyze_company_news(company_name)

        # Save analysis to mounted outputs directory
        if analysis["status"] == "success":
            filepath = agent.save_analysis_to_file(analysis)
            print(f"Analysis saved to: {filepath}")

        # Return response
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

        return {
            "statusCode": 200,
            "body": json.dumps(response_body, indent=2),
            "headers": {"Content-Type": "application/json"},
        }

    except Exception as e:
        print(f"Error in Lambda function: {str(e)}")

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "status": "error"}),
            "headers": {"Content-Type": "application/json"},
        }
