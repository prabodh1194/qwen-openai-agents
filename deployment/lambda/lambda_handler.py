"""
AWS Lambda handler for BSE News Analyzer with smart_open integration.
"""
import json
import logging
import traceback
from typing import Any

import cli.bse_news

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler for analyzing BSE news triggered by SQS.

    Expected event format:
    {
        "Records": [
            {
                "body": "{\"company_name\": \"Company Name\", \"force\": false}",
                "messageId": "12345"
            }
        ]
    }
    """

    # Handle SQS event (batch processing) with partial batch failure reporting
    successful_processes = 0
    failed_processes = 0
    failed_message_ids = []

    # Process each record in the SQS event
    for record in event.get("Records", []):
        try:
            # Parse the message body
            event_body = json.loads(record["body"])

            # Extract company name from event
            company_name = event_body.get("company_name")

            if not company_name:
                logger.error(
                    f"company_name parameter is required for message ID: {record['messageId']}"
                )
                failed_processes += 1
                failed_message_ids.append({"itemIdentifier": record["messageId"]})
                continue

            # Get force parameter from event, default to False
            force = event_body.get("force", False)

            # Call the CLI function directly
            analysis = cli.bse_news.scrape_bse_news(company_name, force)

            # Log success
            logger.info(f"Successfully analyzed company: {company_name}")
            logger.info(f"Analysis result: {analysis.get('status', 'unknown')}")
            successful_processes += 1

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SQS message body: {record['body']}")
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            failed_processes += 1
            failed_message_ids.append({"itemIdentifier": record["messageId"]})

        except Exception as e:
            # Log detailed error with stack trace
            logger.error(
                f"Error processing company news analysis for event: {event_body}"
            )
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            failed_processes += 1
            failed_message_ids.append({"itemIdentifier": record["messageId"]})

    # For SQS event sources, return information about which records failed
    # This allows SQS to only retry the failed messages
    logger.info(
        f"SQS processing complete. Successful: {successful_processes}, Failed: {failed_processes}"
    )
    return {"batchItemFailures": failed_message_ids}
