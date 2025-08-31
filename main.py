#!/usr/bin/env python3
"""
Main entry point for BSE News Scraper CLI
"""
import click

from cli.bse_news import scrape_bse_news


@click.group()
def cli() -> None:
    """BSE News Scraper CLI"""
    pass


cli.add_command(scrape_bse_news)

if __name__ == "__main__":
    cli()