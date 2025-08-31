import requests
import html2text
import urllib.parse
import re
import xml.etree.ElementTree as ET
from typing import Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from openai import OpenAI

import client.qwen


class ApprovalMode(Enum):
    MANUAL = "manual"
    AUTO_EDIT = "auto_edit"


@dataclass
class ToolResult:
    llm_content: str
    return_display: str


@dataclass
class ToolCallConfirmationDetails:
    type: str
    title: str
    prompt: str
    urls: list
    on_confirm: Callable | None = None


class WebFetchToolParams:
    def __init__(self, url: str, prompt: str):
        self.url = url
        self.prompt = prompt


class WebFetchTool:
    """
    Python implementation of WebFetch tool that fetches content from URLs
    and processes it using OpenAI instead of Gemini
    """

    NAME = "web_fetch"
    URL_FETCH_TIMEOUT_MS = 10000
    MAX_CONTENT_LENGTH = 100000

    def __init__(
        self, openai_client: OpenAI, approval_mode: ApprovalMode = ApprovalMode.MANUAL
    ) -> None:
        """
        Initialize the WebFetch tool

        Args:
            openai_client: Your OpenAI client instance
            approval_mode: Whether to auto-approve or require manual confirmation
        """
        self.openai_client = openai_client
        self.approval_mode = approval_mode
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Initialize html2text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # No line wrapping

    @staticmethod
    def validate_params(params: WebFetchToolParams) -> str | None:
        """
        Validate tool parameters

        Args:
            params: WebFetchToolParams object

        Returns:
            Error message if validation fails, None if valid
        """
        if not params.url or params.url.strip() == "":
            return "The 'url' parameter cannot be empty."

        if not params.url.startswith(("http://", "https://")):
            return "The 'url' must be a valid URL starting with http:// or https://."

        if not params.prompt or params.prompt.strip() == "":
            return "The 'prompt' parameter cannot be empty."

        return None

    @staticmethod
    def is_private_ip(url: str) -> bool:
        """
        Check if URL points to a private/localhost IP

        Args:
            url: URL to check

        Returns:
            True if private IP, False otherwise
        """
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False

        # Check for localhost variants
        if hostname.lower() in ["localhost", "127.0.0.1", "::1"]:
            return True

        # Check for private IP ranges (basic check)
        if hostname.startswith(("192.168.", "10.", "172.")):
            return True

        return False

    def should_confirm_execute(
        self, params: WebFetchToolParams
    ) -> ToolCallConfirmationDetails | None:
        """
        Check if execution should be confirmed

        Args:
            params: Tool parameters

        Returns:
            Confirmation details if confirmation needed, None otherwise
        """
        if self.approval_mode == ApprovalMode.AUTO_EDIT:
            return None

        display_prompt = (
            params.prompt[:97] + "..." if len(params.prompt) > 100 else params.prompt
        )

        return ToolCallConfirmationDetails(
            type="info",
            title="Confirm Web Fetch",
            prompt=f"Fetch content from {params.url} and process with: {display_prompt}",
            urls=[params.url],
        )

    @staticmethod
    def convert_github_url(url: str) -> str:
        """
        Convert GitHub blob URL to raw URL for direct access

        Args:
            url: Original GitHub URL

        Returns:
            Raw GitHub URL if applicable, original URL otherwise
        """
        if "github.com" in url and "/blob/" in url:
            raw_url = url.replace("github.com", "raw.githubusercontent.com").replace(
                "/blob/", "/"
            )
            print(f"[WebFetchTool] Converted GitHub blob URL to raw URL: {raw_url}")
            return raw_url
        return url

    def fetch_content(self, url: str) -> str:
        """
        Fetch and convert web content to text

        Args:
            url: URL to fetch

        Returns:
            Text content from the URL
        """
        try:
            print(f"[WebFetchTool] Fetching content from: {url}")

            response = requests.get(
                url, headers=self.headers, timeout=self.URL_FETCH_TIMEOUT_MS / 1000
            )
            response.raise_for_status()

            print(f"[WebFetchTool] Successfully fetched content from {url}")

            # Convert HTML to text
            text_content = self.html_converter.handle(response.text)

            # Truncate if too long
            if len(text_content) > self.MAX_CONTENT_LENGTH:
                text_content = text_content[: self.MAX_CONTENT_LENGTH]
                print(
                    f"[WebFetchTool] Content truncated to {self.MAX_CONTENT_LENGTH} characters"
                )

            print(
                f"[WebFetchTool] Converted HTML to text ({len(text_content)} characters)"
            )
            return str(text_content)

        except requests.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"[WebFetchTool] {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[WebFetchTool] {error_msg}")
            raise Exception(error_msg)

    def process_with_openai(self, content: str, prompt: str, url: str) -> str:
        """
        Process fetched content using OpenAI

        Args:
            content: Fetched web content
            prompt: User's processing prompt
            url: Original URL (for context)

        Returns:
            AI-generated response
        """
        try:
            system_prompt = "You are a helpful assistant that analyzes web content and provides accurate, relevant information based on user requests."

            user_prompt = f"""The user requested the following: "{prompt}".

I have fetched the content from {url}. Please use the following content to answer the user's request.

---
{content}
---"""

            print(
                f'[WebFetchTool] Processing content with OpenAI using prompt: "{prompt}"'
            )

            response = self.openai_client.chat.completions.create(
                model=client.qwen.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1500,
                temperature=0.3,
            )

            result = response.choices[0].message.content
            print(f"[WebFetchTool] Successfully processed content from {url}")
            return str(result)

        except Exception as e:
            error_msg = f"Error processing with OpenAI: {str(e)}"
            print(f"[WebFetchTool] {error_msg}")
            raise Exception(error_msg)

    def execute(self, params: WebFetchToolParams) -> ToolResult:
        """
        Execute the WebFetch tool

        Args:
            params: Tool parameters containing URL and prompt

        Returns:
            ToolResult with processed content
        """
        # Validate parameters
        validation_error = self.validate_params(params)
        if validation_error:
            return ToolResult(
                llm_content=f"Validation Error: {validation_error}",
                return_display=f"Error: {validation_error}",
            )

        # Check for confirmation if needed
        confirmation = self.should_confirm_execute(params)
        if confirmation and self.approval_mode == ApprovalMode.MANUAL:
            print(f"[WebFetchTool] {confirmation.title}: {confirmation.prompt}")
            user_input = input("Proceed? (y/n): ").strip().lower()
            if user_input != "y":
                return ToolResult(
                    llm_content="Operation cancelled by user",
                    return_display="Operation cancelled by user",
                )

        try:
            # Convert GitHub URLs if needed
            url = self.convert_github_url(params.url)

            # Check if private IP
            if self.is_private_ip(url):
                print(
                    f"[WebFetchTool] Private IP detected for {url}, using direct fetch"
                )
            else:
                print(
                    f"[WebFetchTool] Public URL detected for {url}, using direct fetch"
                )

            # Fetch content
            content = self.fetch_content(url)

            # Process with OpenAI
            result_text = self.process_with_openai(content, params.prompt, params.url)

            return ToolResult(
                llm_content=result_text,
                return_display=f"Content from {params.url} processed successfully.",
            )

        except Exception as e:
            error_message = f"Error during fetch for {params.url}: {str(e)}"
            print(f"[WebFetchTool] {error_message}")
            return ToolResult(
                llm_content=f"Error: {error_message}",
                return_display=f"Error: {error_message}",
            )


# Enhanced BSE News Agent using the WebFetch tool approach
class BSENewsAgent:
    def __init__(
        self,
        openai_client: OpenAI,
        approval_mode: ApprovalMode = ApprovalMode.AUTO_EDIT,
    ):
        """
        Initialize BSE News Agent with WebFetch capabilities

        Args:
            openai_client: Your OpenAI client instance
            approval_mode: Approval mode for web fetches
        """
        self.web_fetch_tool = WebFetchTool(openai_client)
        self.web_fetch_tool.approval_mode = approval_mode
        self.openai_client = openai_client

    def analyze_company_news(self, company_name: str) -> dict[str, Any]:
        """
        Analyze company news using RSS feeds and combined analysis

        Args:
            company_name: Name of the BSE-traded company

        Returns:
            Analysis results with structured sentiment data
        """
        import time

        start_time = time.time()

        print(f"[BSENewsAgent] Starting analysis for: {company_name}")

        # Generate multiple search queries for comprehensive coverage
        search_queries = [
            # Company-focused financial terms
            f'"{company_name}" earnings revenue profit loss when:7d',
            # Market-impact events
            f'"{company_name}" acquisition merger partnership contract deal when:7d',
            # Financial reporting
            f'"{company_name}" quarterly results guidance outlook forecast when:7d',
            # Regulatory/sector news
            f'"{company_name}" regulation policy government approval when:7d',
        ]

        print("=" * 60)
        print("SEARCH QUERY HEADERS:")
        for i, query in enumerate(search_queries, 1):
            print(f"{i}. {query}")
        print("=" * 60)

        all_articles = []
        query_results = {}

        # Collect articles from all RSS feeds
        for i, query in enumerate(search_queries, 1):
            try:
                print(f"[BSENewsAgent] Search {i}/{len(search_queries)}: {query}")

                encoded_query = urllib.parse.quote(query)
                rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
                print(f"[BSENewsAgent] RSS URL: {rss_url}")

                articles = self._parse_rss_feed(rss_url, limit=10)
                all_articles.extend(articles)
                query_results[query] = articles

                print(f"[BSENewsAgent] Found {len(articles)} articles from search {i}")

            except Exception as e:
                print(f"[BSENewsAgent] ERROR processing query '{query}': {str(e)}")
                continue

        # Deduplicate and limit articles
        print(f"[BSENewsAgent] Total articles collected: {len(all_articles)}")
        unique_articles = self._deduplicate_articles(all_articles)
        print(
            f"[BSENewsAgent] Unique articles after deduplication: {len(unique_articles)}"
        )

        # Show article sources
        print("[BSENewsAgent] Article Sources:")
        for query, articles in query_results.items():
            if articles:
                print(f"  - {query}: {len(articles)} articles")

        if not unique_articles:
            print("[BSENewsAgent] No articles found for analysis")
            return {
                "company": company_name,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "search_queries_used": search_queries,
                "articles_analyzed": 0,
                "overall_sentiment": 0,
                "key_positive_drivers": [],
                "key_risk_factors": [],
                "confidence": 0,
                "status": "error",
                "display_message": "No articles found for analysis",
            }

        print(f"[BSENewsAgent] Sending {len(unique_articles)} articles for analysis")

        # Combine articles into single text for analysis
        combined_articles_text = ""
        for i, article in enumerate(unique_articles, 1):
            combined_articles_text += f"ARTICLE {i}:\n"
            combined_articles_text += f"Content: {article['description']}\n\n"
            combined_articles_text += f"Date: {article['pub_date']}\n"

        # Create combined analysis prompt
        analysis_prompt = f"""
You are a financial news analyst specializing in stock market impact assessment. Analyze the following news articles and provide an overall sentiment score.

COMPANY: {company_name}

RECENT NEWS ARTICLES:
{combined_articles_text}

TASK: Evaluate how these news might impact the company's stock price in the short to medium term (1-30 days).

SCORING CRITERIA:
- Score from -5 to +5 (integers only)
- Consider: earnings impact, market share changes, regulatory effects, competitive position, operational efficiency, management changes, industry trends

POSITIVE INDICATORS (+1 to +5):
- Strong earnings/revenue growth
- New contracts/partnerships
- Product launches/innovations
- Regulatory approvals
- Market expansion
- Cost reductions
- Leadership appointments

NEGATIVE INDICATORS (-1 to -5):
- Declining profits/revenue
- Lost contracts/clients
- Regulatory issues/fines
- Competitive threats
- Operational disruptions
- Management scandals
- Industry headwinds

NEUTRAL (0):
- Routine announcements
- No clear financial impact
- Mixed positive/negative signals

OUTPUT FORMAT:
Score: [Integer from -5 to +5]
Reasoning: [2-3 sentence explanation focusing on stock price impact]
Key Factors: [List 2-3 most important factors]

Be objective and focus on quantifiable business impact rather than general market sentiment.
"""

        # Use the first article's link as a representative URL for WebFetch
        representative_url = (
            unique_articles[0]["link"]
            if unique_articles[0]["link"]
            else "https://news.google.com"
        )

        # Use WebFetch tool for combined analysis
        params = WebFetchToolParams(representative_url, analysis_prompt)
        result = self.web_fetch_tool.execute(params)

        if "Error:" in result.llm_content:
            return {
                "company": company_name,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "search_queries_used": search_queries,
                "articles_analyzed": len(unique_articles),
                "overall_sentiment": 0,
                "key_positive_drivers": [],
                "key_risk_factors": [],
                "confidence": 0,
                "status": "error",
                "display_message": result.llm_content,
            }

        # Parse the combined analysis result
        sentiment_data = self._parse_combined_analysis(
            result.llm_content, len(unique_articles)
        )

        # Add timing information
        end_time = time.time()
        print(
            f"[BSENewsAgent] Analysis completed in {end_time - start_time:.2f} seconds"
        )

        return {
            "company": company_name,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "search_queries_used": search_queries,
            "articles_analyzed": len(unique_articles),
            **sentiment_data,
            "status": "success",
            "display_message": f"Analyzed {len(unique_articles)} unique articles",
        }

    def _process_sentiment_results(
        self, articles: list, company_name: str
    ) -> dict[str, Any]:
        """Process article analyses to extract sentiment scores and key factors"""
        scores: list[int] = []
        key_positive_drivers: list[str] = []
        key_risk_factors: list[str] = []
        article_breakdown: list[dict] = []

        for article in articles:
            analysis_text = article["analysis"]

            # Extract score from analysis text
            score_match = re.search(r"Score:\s*(-?\d+)", analysis_text)
            if score_match:
                score = int(score_match.group(1))
                scores.append(score)

                # Extract reasoning and key factors
                reasoning_match = re.search(
                    r"Reasoning:\s*(.+?)(?=Key Factors:|$)", analysis_text, re.DOTALL
                )
                factors_match = re.search(
                    r"Key Factors:\s*(.+?)(?=Score:|$)", analysis_text, re.DOTALL
                )

                reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
                factors = (
                    factors_match.group(1).strip().split("\n") if factors_match else []
                )

                article_breakdown.append(
                    {
                        "score": score,
                        "reasoning": reasoning,
                        "key_factors": factors,
                        "query": article["query"],
                    }
                )

                # Categorize drivers based on score
                if score > 0:
                    key_positive_drivers.extend(factors)
                elif score < 0:
                    key_risk_factors.extend(factors)

        # Calculate overall sentiment
        overall_sentiment = sum(scores) / len(scores) if scores else 0

        # Remove duplicates from drivers
        key_positive_drivers = list(set(key_positive_drivers))
        key_risk_factors = list(set(key_risk_factors))

        return {
            "overall_sentiment": round(overall_sentiment, 2),
            "article_breakdown": article_breakdown,
            "key_positive_drivers": key_positive_drivers,
            "key_risk_factors": key_risk_factors,
            "confidence": min(100, len(scores) * 10),  # 10% per article, max 100%
        }

    def _parse_combined_analysis(
        self, analysis_text: str, article_count: int
    ) -> dict[str, Any]:
        """Parse combined analysis result to extract sentiment score and factors"""
        # Extract score from analysis text
        score_match = re.search(r"Score:\s*(-?\d+)", analysis_text)
        score = int(score_match.group(1)) if score_match else 0

        # Extract reasoning
        reasoning_match = re.search(
            r"Reasoning:\s*(.+?)(?=Key Factors:|$)", analysis_text, re.DOTALL
        )
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

        # Extract key factors
        factors_match = re.search(
            r"Key Factors:\s*(.+?)(?=Score:|$)", analysis_text, re.DOTALL
        )
        factors = factors_match.group(1).strip().split("\n") if factors_match else []

        # Categorize factors based on score
        key_positive_drivers: list[str] = []
        key_risk_factors: list[str] = []

        if score > 0:
            key_positive_drivers = factors
        elif score < 0:
            key_risk_factors = factors

        return {
            "overall_sentiment": score,
            "analysis_reasoning": reasoning,
            "key_positive_drivers": key_positive_drivers,
            "key_risk_factors": key_risk_factors,
            "confidence": min(100, article_count * 10),  # 10% per article, max 100%
        }

    def _parse_rss_feed(self, rss_url: str, limit: int = 10) -> list[dict[str, str]]:
        """Parse RSS feed and extract articles with limit"""
        try:
            response = requests.get(rss_url)
            response.raise_for_status()

            root = ET.fromstring(response.text)
            articles = []

            for item in root.findall(".//item")[:limit]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                source_elem = item.find("source")

                # Create clean description using title and source
                title = (
                    str(title_elem.text)
                    if title_elem is not None and title_elem.text is not None
                    else ""
                )
                source = (
                    str(source_elem.text)
                    if source_elem is not None and source_elem.text is not None
                    else ""
                )
                description = f"{title} - {source}" if source else title

                article = {
                    "title": title,
                    "link": str(link_elem.text)
                    if link_elem is not None and link_elem.text is not None
                    else "",
                    "pub_date": str(pub_date_elem.text)
                    if pub_date_elem is not None and pub_date_elem.text is not None
                    else "",
                    "description": description,
                }
                articles.append(article)

            return articles

        except Exception as e:
            print(f"Error parsing RSS feed {rss_url}: {str(e)}")
            return []

    def _deduplicate_articles(
        self, articles: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Remove duplicate articles by title and link"""
        seen = set()
        unique_articles = []

        for article in articles:
            # Create unique identifier from title and link
            article_id = f"{article['title']}|{article['link']}"
            if article_id not in seen:
                seen.add(article_id)
                unique_articles.append(article)

        return unique_articles

    def _generate_filename(self, company_name: str) -> str:
        """Generate standardized filename from company name"""
        # Convert to lowercase
        filename = company_name.lower()
        # Replace spaces and special characters with underscores
        filename = re.sub(r"[^a-z0-9]+", "_", filename)
        # Remove leading/trailing underscores
        filename = filename.strip("_")
        return f"{filename}.json"

    def save_analysis_to_file(self, analysis_data: dict[str, Any]) -> str:
        """Save analysis results to dated directory"""
        import json
        import os

        # Create outputs directory if it doesn't exist
        outputs_dir = "outputs"
        if not os.path.exists(outputs_dir):
            os.makedirs(outputs_dir)

        # Create dated subdirectory
        date_str = analysis_data.get(
            "analysis_date", datetime.now().strftime("%Y-%m-%d")
        )
        dated_dir = os.path.join(outputs_dir, date_str)
        if not os.path.exists(dated_dir):
            os.makedirs(dated_dir)

        # Generate filename
        filename = self._generate_filename(analysis_data["company"])
        filepath = os.path.join(dated_dir, filename)

        # Write JSON data
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)

        return filepath
