"""
AWS Lambda handler for scheduled invocation of BSE news analysis for all companies.
"""
import json
import os
import boto3
from typing import Dict, Any
from pathlib import Path
from smart_open import open


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for scheduled invocation of BSE news analysis.

    Expected environment variables:
    - S3_BUCKET_NAME: Name of the S3 bucket for mountpoint
    """

    try:
        # Get configuration from environment variables
        bucket_name = os.environ.get("S3_BUCKET_NAME", "bse-news-analyzer-data")

        print(f"Starting scheduled BSE news analysis for bucket: {bucket_name}")

        # Read company names from stocks file (mounted from S3)
        stocks_file = Path("/home/sbx_user1050/stocks/stocks_100")
        if not stocks_file.exists():
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"error": f"Stocks file not found at {stocks_file}"}
                ),
            }

        with open(stocks_file, "r") as f:
            company_names = [line.strip() for line in f.readlines() if line.strip()]

        print(f"Processing {len(company_names)} companies...")

        # Initialize Lambda client
        lambda_client = boto3.client("lambda")

        # Process all companies synchronously
        success_count = 0
        for company_name in company_names:
            try:
                print(f"Invoking Lambda for: {company_name}")

                # Prepare the payload
                payload = json.dumps({"company_name": company_name})

                # Invoke the Lambda function
                response = lambda_client.invoke(
                    FunctionName="bse-news-analyzer",
                    InvocationType="RequestResponse",  # Synchronous invocation
                    Payload=payload,
                )

                if response["StatusCode"] == 200:
                    print(f"✓ Success: {company_name}")
                    success_count += 1
                else:
                    print(f"✗ Failed: {company_name} - Status {response['StatusCode']}")

            except Exception as e:
                print(f"✗ Error processing {company_name}: {str(e)}")

        print(
            f"Completed! Successfully processed {success_count}/{len(company_names)} companies."
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "status": "success",
                    "message": f"Processed {success_count}/{len(company_names)} companies",
                    "companies_processed": len(company_names),
                    "success_count": success_count,
                    "bucket": bucket_name,
                }
            ),
        }

    except Exception as e:
        print(f"Error in scheduled invoke: {str(e)}")

        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "error": str(e)}),
        }
