"""
CLI module for invoking AWS Lambda function for BSE news analysis
"""
import asyncio
import json
import subprocess
from pathlib import Path
from typing import List

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
    """Invoke AWS Lambda function for BSE news analysis for all companies in stocks_100 file."""
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

        if async_mode:
            # Run asynchronously
            asyncio.run(invoke_lambda_async(company_names, verbose))
        else:
            # Run synchronously
            invoke_lambda_sync(company_names, verbose)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


async def invoke_lambda_async(company_names: List[str], verbose: bool) -> None:
    """Invoke Lambda functions asynchronously."""
    tasks = [invoke_single_lambda_async(company, verbose) for company in company_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for result in results if result is True)
    click.echo(
        f"Completed! Successfully processed {success_count}/{len(company_names)} companies."
    )


async def invoke_single_lambda_async(company_name: str, verbose: bool) -> bool:
    """Invoke Lambda function for a single company asynchronously."""
    try:
        # Print company name being processed unless quiet mode is enabled
        if verbose:
            click.echo(f"Invoking Lambda for: {company_name}")

        # Prepare the payload
        payload = {"company_name": company_name}

        # Run the AWS CLI command
        cmd = [
            "aws",
            "lambda",
            "invoke",
            "--function-name",
            "bse-news-analyzer",
            "--payload",
            json.dumps(payload),
            "--cli-binary-format",
            "raw-in-base64-out",
            "response.json",
        ]

        # Execute the command
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            click.echo(f"✓ Success: {company_name}")
            return True
        else:
            click.echo(f"✗ Failed: {company_name} - {stderr.decode()}")
            return False

    except Exception as e:
        click.echo(f"✗ Error processing {company_name}: {str(e)}")
        return False


def invoke_lambda_sync(company_names: List[str], verbose: bool) -> None:
    """Invoke Lambda functions synchronously."""
    success_count = 0

    for company_name in company_names:
        try:
            # Print company name being processed unless quiet mode is enabled
            if verbose:
                click.echo(f"Invoking Lambda for: {company_name}")

            # Prepare the payload
            payload = {"company_name": company_name}

            # Run the AWS CLI command
            cmd = [
                "aws",
                "lambda",
                "invoke",
                "--function-name",
                "bse-news-analyzer",
                "--payload",
                json.dumps(payload),
                "--cli-binary-format",
                "raw-in-base64-out",
                "response.json",
            ]

            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                click.echo(f"✓ Success: {company_name}")
                success_count += 1
            else:
                click.echo(f"✗ Failed: {company_name} - {result.stderr}")

        except Exception as e:
            click.echo(f"✗ Error processing {company_name}: {str(e)}")

    click.echo(
        f"Completed! Successfully processed {success_count}/{len(company_names)} companies."
    )
