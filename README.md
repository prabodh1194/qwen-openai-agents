# Qwen OpenAI Agents

A collection of tools and agents built using the Qwen API via the OpenAI-compatible interface.

## Features

- BSE News Scraper: Analyze Bombay Stock Exchange news for publicly traded companies
- Web Fetch Tool: Generic tool for fetching and analyzing web content
- Easy CLI interface for all tools

## Prerequisites

1. Python 3.13+
2. Qwen API credentials (stored in `~/.qwen/oauth_creds.json`)
3. Required Python packages (see `pyproject.toml`)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd qwen-openai-agents
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```
   or if using uv:
   ```bash
   uv pip install -e .
   ```

## Usage

### BSE News Scraper

To analyze recent news for a BSE-listed company:

```bash
python main.py scrape-bse-news "Company Name"
```

Example:
```bash
python main.py scrape-bse-news "Tata Consultancy Services"
```

You can also specify the maximum number of articles to analyze:
```bash
python main.py scrape-bse-news "Reliance Industries" --max-articles 10
```

## Project Structure

- `client/`: Qwen client implementation
- `tools/`: Individual tools (web fetch, etc.)
- `cli/`: Command-line interface modules
- `main.py`: Main entry point

## Development

To install development dependencies:
```bash
pip install -e ".[dev]"
```

To run type checking:
```bash
mypy .
```

To run code formatting:
```bash
ruff check .
```