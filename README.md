# Qwen OpenAI Agents

Implemented an analyser for top 100 NSE + BSE stocks. Scrape the latest news for these stocks daily & use LLM to
generate BUY/HOLD/SELL reccos for these. Accessible on [this page](https://prabodhagarwal.com/se).

## Features

- BSE News Scraper: Analyze Bombay Stock Exchange news for publicly traded companies
- Web Fetch Tool: Generic tool for fetching and analyzing web content
- Easy CLI interface for all tools
- AWS Lambda integration for scalable processing
- SQS-based queuing for batch processing
