"""
AWS Lambda handler for BSE News Analyzer with smart_open integration.
"""
import json
import os
from typing import Dict, Any

# Import from the main application
from client.qwen import QwenClient
from smart_open import open


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

        # Get S3 bucket from environment
        s3_bucket = os.environ.get("S3_BUCKET_NAME", "bse-news-analyzer-data")

        # Initialize Qwen client with S3 credentials URI
        creds_uri = f"s3://{s3_bucket}/.qwen/oauth_creds.json"
        qwen = QwenClient(creds_uri=creds_uri)

        # Initialize BSE News Agent
        from tools.web_fetch import BSENewsAgent, ApprovalMode

        agent = BSENewsAgent(qwen.client, ApprovalMode.AUTO_EDIT)

        # Perform analysis
        analysis = agent.analyze_company_news(company_name)

        # Save analysis to S3 using smart_open
        if analysis["status"] == "success":
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company_name.lower().replace(' ', '_')}_{timestamp}.json"
            output_uri = f"s3://{s3_bucket}/outputs/{filename}"

            with open(output_uri, "w") as f:
                json.dump(analysis, f, indent=2)

            print(f"Analysis saved to: {output_uri}")
            analysis["s3_location"] = output_uri

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
