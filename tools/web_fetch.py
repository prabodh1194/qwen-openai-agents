import requests
import html2text
import urllib.parse
from typing import Any, Callable
from dataclasses import dataclass
from enum import Enum

from openai import OpenAI

import client.qwen
from client.qwen import QwenClient


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
        try:
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
        except:
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
            return text_content

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

    def analyze_company_news(
        self, company_name: str, max_articles: int = 5
    ) -> dict[str, Any]:
        """
        Analyze company news using WebFetch approach

        Args:
            company_name: Name of the BSE-traded company
            max_articles: Maximum number of articles to analyze

        Returns:
            Analysis results
        """
        # Construct Google News URL
        query = f"{company_name} BSE stock market news"
        encoded_query = urllib.parse.quote(query)
        news_url = f"https://news.google.com/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN%3Aen"

        # Create analysis prompt
        analysis_prompt = f"""
        Analyze the news content for {company_name}, a company traded on the Bombay Stock Exchange (BSE).

        Please provide:
        1. A summary of key recent developments
        2. Financial performance highlights or concerns
        3. Strategic initiatives and business updates
        4. Market sentiment and investor outlook
        5. Any regulatory or compliance matters

        Focus on information relevant to investors and stakeholders. If there are multiple news articles visible, analyze all of them collectively.
        """

        # Use WebFetch tool to get and analyze content
        params = WebFetchToolParams(news_url, analysis_prompt)
        result = self.web_fetch_tool.execute(params)

        return {
            "company": company_name,
            "url": news_url,
            "analysis": result.llm_content,
            "status": "success" if "Error:" not in result.llm_content else "error",
            "display_message": result.return_display,
        }


# Example usage
if __name__ == "__main__":
    qwen = QwenClient().client

    # Method 1: Use WebFetch tool directly
    # web_fetch = WebFetchTool(qwen)
    # params = WebFetchToolParams(
    #     url="https://news.google.com/search?q=Reliance+Industries+BSE",
    #     prompt="Summarize the latest news about this company's stock performance",
    # )
    # result = web_fetch.execute(params)
    # print(result.llm_content)

    # Method 2: Use BSE News Agent
    agent = BSENewsAgent(qwen, ApprovalMode.AUTO_EDIT)
    analysis = agent.analyze_company_news("Tata Consultancy Services")
    print(f"Analysis: {analysis['analysis']}")

    pass
