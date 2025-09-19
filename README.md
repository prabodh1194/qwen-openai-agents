# Qwen OpenAI Agents

A collection of tools and agents built using the Qwen API via the OpenAI-compatible interface.

## Features

- BSE News Scraper: Analyze Bombay Stock Exchange news for publicly traded companies
- Web Fetch Tool: Generic tool for fetching and analyzing web content
- Easy CLI interface for all tools
- AWS Lambda integration for scalable processing
- SQS-based queuing for batch processing

## Prerequisites

1. Python 3.13+
2. Qwen API credentials (stored in `~/.qwen/oauth_creds.json`)
3. Required Python packages (see `pyproject.toml`)
4. AWS CLI configured with appropriate permissions (for Lambda/SQS operations)

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

By default, if an analysis already exists for the current date in S3, the command will skip execution. To force re-analysis, use the `--force` flag:

```bash
python main.py scrape-bse-news --force "Company Name"
```

### AWS Lambda Integration

To invoke the AWS Lambda function for processing multiple companies:

```bash
python main.py invoke-lambda [--async/--sync] [--limit N] [--quiet]
```

### SQS Integration

To send company names to an SQS queue for processing by the Lambda function:

```bash
# Send individual companies
python main.py send-to-sqs --queue-url <SQS_QUEUE_URL> "Company A" "Company B"

# Send companies from a file
python main.py send-to-sqs --queue-url <SQS_QUEUE_URL> --file companies.txt

# Force re-analysis
python main.py send-to-sqs --queue-url <SQS_QUEUE_URL> --force "Company A"
```

## Project Structure

- `client/`: Qwen client implementation
- `tools/`: Individual tools (web fetch, etc.)
- `cli/`: Command-line interface modules
- `main.py`: Main entry point
- `deployment/`: Terraform configurations for AWS deployment

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