# Qwen OpenAI Agents

Implemented an analyser for top 100 NSE + BSE stocks. Scrape the latest news for these stocks daily & use LLM to generate BUY/HOLD/SELL reccos for these. Accessible on [this page](https://prabodhagarwal.com/se).

## Features

- BSE News Scraper: Analyze Bombay Stock Exchange news for publicly traded companies
- Web Fetch Tool: Generic tool for fetching and analyzing web content
- Easy CLI interface for all tools
- AWS Lambda integration for scalable processing
- SQS-based queuing for batch processing
- Multi-agent system architecture for distributed analysis
- Portfolio-level analysis with BUY/HOLD/SELL recommendations
- S3 mountpoint integration for persistent storage
- DynamoDB tracking for analysis results

## Technical Architecture

- **Python** with modern async/await patterns and type hints
- **DeepSeek API** integration (production)
- **FastAPI** for RESTful API endpoints
- **AWS Lambda** with S3 mountpoint for serverless processing
- **SQS queues** for batch job processing
- **DynamoDB** for tracking analysis results
- **S3 storage** for analysis outputs and data persistence
- **Smart-open** for S3 file operations
- **Docker containerization** for deployment

## Key Components

- **BSE News Agent**: Uses RSS feeds to gather news articles for each company
- **Web Fetch Tool**: Fetches and analyzes web content using AI
- **Lambda Functions**: Serverless functions for batch and individual processing
- **Analysis Service**: Core service layer for news analysis
- **CLI Interface**: Command-line tools for various operations

## AI Integration

- Uses DeepSeek in production for financial analysis
- 5-point scoring system for sentiment analysis (-5 to +5)
- Automated categorization of news as positive/negative factors
- Portfolio-level recommendations based on comprehensive analysis
