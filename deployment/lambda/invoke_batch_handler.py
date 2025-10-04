"""
AWS Lambda handler for invoking batch BSE news analysis.
"""
import json
from typing import Any

# Add the project root to the path so we can import the CLI module
import cli.invoke_lambda


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda function handler for invoking batch BSE news analysis.

    Expected event format:
    {
        "limit": 10  # Optional: Limit the number of companies to process
    }
    """
    try:
        # Parse the limit from the event (optional)
        limit = event.get("limit")

        # Validate limit if provided
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {"error": "limit must be a non-negative integer"}
                    ),
                }

        # Call the CLI function directly
        # Capture any needed parameters from the event
        cli.invoke_lambda.invoke_lambda(limit)

        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Successfully invoked batch processing", "limit": limit}
            ),
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
