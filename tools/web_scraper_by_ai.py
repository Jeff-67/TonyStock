"""Module for crawling and cleaning web content from financial news sources."""

import asyncio
import json
import logging
import re
from typing import List

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from dotenv import load_dotenv
from opik import track
from pydantic import BaseModel

from tools.llm_api import aquery_llm

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants for timeout and retry configuration
DEFAULT_TIMEOUT = 60  # Increased timeout for slower sites
MAX_RETRIES = 3  # Increased retries
RETRY_DELAY = 2  # Increased delay between retries


class FilteredContent(BaseModel):
    """Pydantic model for structured parsing of filtered content from LLM response.

    Attributes:
        filtered_content (str): The filtered and cleaned content extracted from the raw text.
        time (str): The time information extracted from the content.
    """

    filtered_content: str
    time: str


@track()
async def LLMfilter(scrapped_content: str, query: str) -> FilteredContent:
    """Filter the scrapped content by the query.

    Args:
        scrapped_content (str): The raw content to filter
        query (str): The query to filter with

    Returns:
        FilteredContent: A model containing the filtered content and time

    Note:
        In case of error, returns a FilteredContent with the original conten
        and current timestamp.
    """
    prompt = f"""
    Given web-scraped raw content in Markdown format and a specific query, extract and return only the most relevant portion that may answer the query. Remove clearly irrelevant elements such as navigation menus, sidebars, and footer content, while preserving the exact language and structure of the original content.
    Here is the query: {query}
    Here is the scrapped content: {scrapped_content}

    return the filtered content and the time of the content in JSON format.
    """
    try:
        # Format messages properly for LLM API
        messages = [{"role": "user", "content": prompt}]
        response, _ = await aquery_llm(
            messages=messages,
            model="gpt-4o-2024-08-06",
            provider="openai",
            response_format=FilteredContent,
        )
        json_response = json.loads(response.choices[0].message.content)
        return FilteredContent(**json_response)
    except Exception as e:
        logger.error(f"Error parsing response: {str(e)}")
        # Return a FilteredContent with original content and current time
        from datetime import datetime

        return FilteredContent(
            filtered_content=scrapped_content, time=datetime.now().isoformat()
        )


def clean_markdown(text: str) -> str:
    """Clean markdown content by removing messy hyperlinks and formatting.

    Args:
        text (str): The markdown text to clean

    Returns:
        str: Cleaned text with hyperlinks removed
    """
    if not text:  # Handle None or empty string
        return ""

    try:
        # Remove markdown links while keeping the text
        # This pattern matches [text](url) and keeps only the text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove any remaining URLs
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        # Remove empty lines and excessive whitespace
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

        return text
    except Exception as e:
        logger.error(f"Error cleaning markdown: {str(e)}")
        return text if isinstance(text, str) else ""


@track()
async def scrape_url(url: str, query: str, crawler: AsyncWebCrawler) -> str:
    """Run the web crawler and clean the retrieved content.

    Args:
        url (str): The URL to scrape
        query (str): The query to filter content with
        crawler (AsyncWebCrawler): The crawler instance to use

    Returns:
        str: A JSON string containing:
            - content: The filtered content relevant to the query
            - time: The time of the conten
            - url: The source URL
            - error: Error message if any
    """
    try:
        # Implement retry logic directly in this function
        result = None
        for attempt in range(MAX_RETRIES):
            try:
                # The crawler already has timeout configured in CrawlerRunConfig
                result = await crawler.arun(url=url)
                if result and result.markdown:  # Verify we got actual conten
                    break
                logger.warning(
                    f"No content retrieved from {url} (attempt {attempt+1}/{MAX_RETRIES})"
                )
            except Exception as e:
                logger.error(
                    f"Error crawling {url} (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}"
                )

            if attempt < MAX_RETRIES - 1:
                # Exponential backoff for retries
                retry_delay = RETRY_DELAY * (2**attempt)
                logger.info(f"Waiting {retry_delay}s before retry...")
                await asyncio.sleep(retry_delay)

        if not result or not result.markdown:
            logger.error(f"Failed to crawl {url} after {MAX_RETRIES} attempts")
            return json.dumps(
                {
                    "content": "",
                    "time": "",
                    "url": url,
                    "error": "No content retrieved",
                },
                ensure_ascii=False,
            )

        # Clean the markdown conten
        cleaned_content = clean_markdown(result.markdown)
        if not cleaned_content:
            return json.dumps(
                {
                    "content": "",
                    "time": "",
                    "url": url,
                    "error": "Content cleaning failed",
                },
                ensure_ascii=False,
            )

        # Filter conten
        try:
            filtered_result = await LLMfilter(cleaned_content, query)
            response_dict = {
                "content": filtered_result.filtered_content,
                "time": filtered_result.time,
                "url": url,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error filtering content: {str(e)}")
            response_dict = {
                "content": cleaned_content,  # Use cleaned but unfiltered conten
                "time": "",
                "url": url,
                "error": f"Content filtering failed: {str(e)}",
            }

        return json.dumps(response_dict, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return json.dumps(
            {
                "content": "",
                "time": "",
                "url": url,
                "error": f"Scraping failed: {str(e)}",
            },
            ensure_ascii=False,
        )


@track()
async def scrape_urls(urls: List[str], query: str) -> List[str]:
    """Process multiple URLs concurrently using AsyncWebCrawler.

    Args:
        urls: List of URLs to scrape
        query: Query to extract relevant conten

    Returns:
        List of JSON strings containing scraped content and error information
    """
    try:
        # Create browser config with correct parameters
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            java_script_enabled=True,
            viewport_width=1920,
            viewport_height=1080,
            ignore_https_errors=True,
        )

        # Create crawler run config
        crawler_run_config = CrawlerRunConfig(
            wait_until="networkidle",
            page_timeout=DEFAULT_TIMEOUT * 1000,  # Convert to milliseconds
            ignore_body_visibility=True,
            scan_full_page=True,
            scroll_delay=0.5,
            remove_overlay_elements=True,
            simulate_user=True,
            magic=True,  # Enable automatic handling of overlays/popups
        )

        # Pass both configs to AsyncWebCrawler
        async with AsyncWebCrawler(
            config=browser_config, run_config=crawler_run_config
        ) as crawler:
            tasks = []
            for url in urls:
                task = scrape_url(url, query, crawler)
                tasks.append(task)

            # Use gather with return_exceptions=True to prevent one failure from affecting others
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle any exceptions in results
            processed_results = []
            for url, result in zip(urls, results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {url}: {str(result)}")
                    processed_results.append(
                        json.dumps(
                            {
                                "content": "",
                                "time": "",
                                "url": url,
                                "error": f"Processing failed: {str(result)}",
                            },
                            ensure_ascii=False,
                        )
                    )
                else:
                    # Ensure result is a string before appending
                    processed_results.append(
                        str(result) if not isinstance(result, str) else result
                    )

            return processed_results
    except Exception as e:
        logger.error(f"Error in scrape_urls: {str(e)}")
        # Return empty results for all URLs in case of catastrophic failure
        return [
            json.dumps(
                {
                    "content": "",
                    "time": "",
                    "url": url,
                    "error": f"Scraping infrastructure failed: {str(e)}",
                },
                ensure_ascii=False,
            )
            for url in urls
        ]


if __name__ == "__main__":
    # Test URLs - using a mix of fast and potentially slow loading sites
    test_urls = [
        "https://finance.ettoday.net/news/2898977",  # ETtoday
        "https://money.udn.com/money/story/5607/7704246",  # UDN
        "https://www.chinatimes.com/realtimenews/20240226002579-260410",  # ChinaTimes
        "https://tw.stock.yahoo.com/news/台積電-2330-台股-113926345.html",  # Yahoo Finance
    ]

    print("Starting to scrape URLs...")
    print(
        f"Using timeout: {DEFAULT_TIMEOUT}s, max retries: {MAX_RETRIES}, initial delay: {RETRY_DELAY}s"
    )
    print(
        f"Browser config: headless={True}, wait_until='networkidle', viewport=1920x1080"
    )
    print("\nTesting with URLs:", *test_urls, sep="\n- ")

    async def run_test():
        """Run a test of the web scraper with predefined URLs and query.

        This function demonstrates the usage of the scrape_urls function by:
        1. Scraping a list of test URLs with a sample query
        2. Processing and displaying the results for each URL
        3. Handling any errors that occur during the process
        """
        try:
            results = await scrape_urls(test_urls, "台積電")

            # Print results for each URL
            for url, content in zip(test_urls, results):
                print(f"\n{'='*40}")
                print(f"URL: {url}")

                try:
                    # Parse the JSON conten
                    result = json.loads(content)
                    if result.get("error"):
                        print(f"Error: {result['error']}")
                    else:
                        print(f"Time: {result.get('time', 'Not available')}")
                        content_preview = result.get("content", "")[:300]
                        print(f"Content preview: {content_preview}...")
                except json.JSONDecodeError:
                    print("Error: Could not parse result JSON")
                except Exception as e:
                    print(f"Error processing result: {str(e)}")

                print(f"{'='*40}")

        except Exception as e:
            print(f"Test failed with error: {str(e)}")

    # Run the tes
    asyncio.run(run_test())
