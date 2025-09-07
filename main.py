#!/usr/bin/env python3
"""
Main entry point for BSE News Scraper CLI
"""
import click

from cli.bse_news import scrape_bse_news
from cli.invoke_lambda import invoke_lambda
from cli.refresh_token import refresh_qwen_token


@click.group()  # type: ignore[misc]
def cli() -> None:
    """BSE News Scraper CLI"""
    pass


cli.add_command(scrape_bse_news)
cli.add_command(invoke_lambda)
cli.add_command(refresh_qwen_token)

if __name__ == "__main__":
    cli()
