"""
AWS Lambda handler for refreshing Qwen credentials and updating S3 mountpoint.
"""
import json
import os
from typing import Dict, Any

# Import from the main application
from client.qwen import QwenClient

# Import S3 upload function
from deployment.scripts.upload_creds import upload_credentials_to_s3


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for refreshing Qwen credentials.

    Expected environment variables:
    - S3_BUCKET_NAME: Name of the S3 bucket for credentials
    - AWS_REGION: AWS region (default: us-east-1)
    """

    try:
        # Get configuration from environment variables
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        region = os.environ.get("AWS_REGION", "us-east-1")

        if not bucket_name:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"error": "S3_BUCKET_NAME environment variable is required"}
                ),
            }

        print(f"Refreshing Qwen credentials for bucket: {bucket_name}")

        # Initialize Qwen client
        qwen = QwenClient()

        # Refresh tokens
        print("Refreshing Qwen API tokens...")
        new_credentials = qwen.refresh_token()

        # Save updated credentials locally (to mounted S3 path)
        with open(qwen.creds_uri, "w") as f:
            json.dump(new_credentials, f, indent=2)

        print(f"✓ Tokens refreshed and saved to {qwen.creds_uri}")

        # Upload to S3 (for redundancy and manual access)
        print("Uploading credentials to S3...")
        upload_credentials_to_s3(bucket_name, region)

        print("✓ Credentials refresh completed successfully")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "status": "success",
                    "message": "Credentials refreshed successfully",
                    "bucket": bucket_name,
                }
            ),
        }

    except Exception as e:
        print(f"Error refreshing credentials: {str(e)}")

        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "error": str(e)}),
        }
