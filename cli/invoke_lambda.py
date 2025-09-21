"""
CLI module for sending company names to AWS SQS queue for BSE news analysis
"""
import json
import os
from pathlib import Path

import boto3
import click


@click.command()  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--async/--sync",
    "async_mode",
    default=True,
    help="Run invocations asynchronously or synchronously",
)
@click.option("--limit", type=int, help="Limit the number of companies to process")  # type: ignore[misc]
@click.option("--quiet", "-q", is_flag=True, help="Suppress verbose output")  # type: ignore[misc]
def invoke_lambda(async_mode: bool, limit: int, quiet: bool) -> None:
    """Send company names to AWS SQS queue for BSE news analysis."""
    try:
        # Read company names from stocks file
        stocks_file = Path(__file__).parent.parent / "stocks" / "stocks_100"
        if not stocks_file.exists():
            click.echo(f"Error: Stocks file not found at {stocks_file}", err=True)
            raise click.Abort()

        with open(stocks_file, "r") as f:
            company_names = [line.strip() for line in f.readlines() if line.strip()]

        # Apply limit if specified
        if limit:
            company_names = company_names[:limit]

        # Verbose is the default behavior, only suppress if quiet flag is set
        verbose = not quiet

        click.echo(f"Processing {len(company_names)} companies...")

        # Print company names unless quiet mode is enabled
        if verbose:
            click.echo("Companies to process:")
            for i, company in enumerate(company_names, 1):
                click.echo(f"  {i}. {company}")
            click.echo("")

        # Get SQS queue URL from environment variable
        queue_url = os.environ.get("SQS_QUEUE_URL")
        if not queue_url:
            click.echo("Error: SQS_QUEUE_URL environment variable not set", err=True)
            raise click.Abort()

        # Initialize SQS client
        sqs_client = boto3.client(
            "sqs", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

        # Send company names to SQS queue
        sent_count = 0
        failed_count = 0

        for company_name in company_names:
            try:
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps({"company_name": company_name}),
                )
                sent_count += 1
                if verbose:
                    click.echo(f"  Sent '{company_name}' to SQS queue")
            except Exception as e:
                failed_count += 1
                click.echo(
                    f"  Error sending '{company_name}' to SQS: {str(e)}", err=True
                )

        click.echo(f"\nSummary: {sent_count} sent, {failed_count} failed")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
