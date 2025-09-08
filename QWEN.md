# CODING STANDARDS

1. USE smart_open.open for all file operations. It is s3 compatible.
2. Avoid safe code. Fail very very fast.
3. Use `abc | None` instead of Optional[abc]


# Qwen Code Agent

This project is a CLI tool that provides access to the Qwen API through an OpenAI-compatible interface, with specialized features for financial news analysis.

## Features

### BSE News Analysis
- **Company News Scraping**: Automatically scrape recent news for BSE-listed companies using Google News RSS feeds
- **Sentiment Analysis**: Analyze news articles to determine potential stock price impact with sentiment scores from -5 to +5
- **Key Factor Extraction**: Identify key positive drivers and risk factors affecting companies
- **Confidence Scoring**: Provides confidence levels based on the number of articles analyzed

### Stock Analysis Summary
- **Portfolio Analysis**: Analyze all stock analyses for a specific date and categorize stocks as Buy, Hold, or Sell
- **Automated Categorization**: Classify stocks based on sentiment scores (Buy: >2, Hold: -2 to 2, Sell: <-2)
- **S3 Integration**: Read analysis files directly from S3 or local directories
- **Comprehensive Reporting**: Display detailed results with sentiment scores, confidence levels, and reasoning

### Token Management
- **Automatic Token Refresh**: Refresh Qwen API tokens using refresh tokens to maintain continuous access
- **Token Expiration Monitoring**: Display token expiration information to help manage credentials

### AWS Lambda Integration
- **Batch Processing**: Process multiple companies' news analysis through AWS Lambda functions
- **Async/Sync Execution**: Support for both asynchronous and synchronous Lambda invocations
- **Processing Limits**: Option to limit the number of companies processed in a batch

## Credentials Setup

To use this tool, you need to set up your Qwen API credentials in a specific location:

1. Create a directory: `~/.qwen/`
2. Create a file called `oauth_creds.json` in that directory
3. Add your credentials in one of these formats:

### Option 1: API Key
```json
{
  "api_key": "your-qwen-api-key-here"
}
```

### Option 2: Access Token
```json
{
  "access_token": "your-qwen-access-token-here"
}
```

### Option 3: Token
```json
{
  "token": "your-qwen-token-here"
}
```

## Model Information

The project currently uses the `qwen3-coder-plus` model.

## Usage

Once you've set up your credentials, the tool will automatically load them from `~/.qwen/oauth_creds.json` and use them to authenticate with the Qwen API.

### CLI Commands

1. **Analyze BSE News for a Company**:
   ```bash
   python main.py scrape-bse-news "Company Name"
   ```

2. **Refresh Qwen API Tokens**:
   ```bash
   python main.py refresh-qwen-token
   ```

3. **Invoke AWS Lambda for Batch Processing**:
   ```bash
   python main.py invoke-lambda [--async/--sync] [--limit N] [--quiet]
   ```

4. **Analyze All Stocks for a Date**:
   ```bash
   python main.py analyze-stocks [DATE] [--s3-bucket BUCKET] [--s3-prefix PREFIX] [--local-path PATH]
   ```
   - DATE: Date in YYYY-MM-DD format (defaults to today if not provided)
   - --s3-bucket: S3 bucket name (defaults to "bse-news-analyzer-data")
   - --s3-prefix: S3 prefix for outputs (defaults to "outputs")
   - --local-path: Local path to read analyses from instead of S3