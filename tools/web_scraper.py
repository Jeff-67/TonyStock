"""Web scraper module for extracting content from web pages.

This module provides functionality to scrape web content using Playwright,
with support for concurrent processing, HTML parsing, and content extraction.
Features include:
- Asynchronous page fetching with timeout handling
- Concurrent processing of multiple URLs
- HTML parsing with markdown link formatting
- Content cleaning and standardization
- Error handling and logging
"""

# !/usr/bin/env python3

import argparse
import asyncio
import logging
import sys
import time
from multiprocessing import Pool
from typing import List, Optional
from urllib.parse import urlparse

import html5lib
from playwright.async_api import TimeoutError, async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


async def fetch_page(url: str, context) -> Optional[str]:
    """Asynchronously fetch a webpage's content."""
    page = await context.new_page()
    try:
        logger.info(f"Fetching {url}")
        # Set timeout to 30 seconds
        await page.goto(url, timeout=30000)
        # Wait for page load, maximum 30 seconds
        await page.wait_for_load_state("networkidle", timeout=30000)
        content = await page.content()
        logger.info(f"Successfully fetched {url}")
        return content
    except TimeoutError:
        logger.error(f"Timeout fetching {url}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None
    finally:
        await page.close()


def parse_html(html_content: Optional[str]) -> str:
    """Parse HTML content and extract text with hyperlinks in markdown format."""
    if not html_content:
        return ""

    try:
        document = html5lib.parse(html_content)
        result = []
        seen_texts = set()  # To avoid duplicates

        def should_skip_element(elem) -> bool:
            """Check if the element should be skipped."""
            # Skip script and style tags
            if elem.tag in [
                "{http://www.w3.org/1999/xhtml}script",
                "{http://www.w3.org/1999/xhtml}style",
            ]:
                return True
            # Skip empty elements or elements with only whitespace
            if not any(text.strip() for text in elem.itertext()):
                return True
            return False

        def process_element(elem, depth=0):
            """Process an element and its children recursively."""
            if should_skip_element(elem):
                return

            # Handle text content
            if hasattr(elem, "text") and elem.text:
                text = elem.text.strip()
                if text and text not in seen_texts:
                    # Check if this is an anchor tag
                    if elem.tag == "{http://www.w3.org/1999/xhtml}a":
                        href = None
                        for attr, value in elem.items():
                            if attr.endswith("href"):
                                href = value
                                break
                        if href and not href.startswith(("#", "javascript:")):
                            # Format as markdown link
                            link_text = f"[{text}]({href})"
                            result.append("  " * depth + link_text)
                            seen_texts.add(text)
                    else:
                        result.append("  " * depth + text)
                        seen_texts.add(text)

            # Process children
            for child in elem:
                process_element(child, depth + 1)

            # Handle tail text
            if hasattr(elem, "tail") and elem.tail:
                tail = elem.tail.strip()
                if tail and tail not in seen_texts:
                    result.append("  " * depth + tail)
                    seen_texts.add(tail)

        # Start processing from the body tag
        body = document.find(".//{http://www.w3.org/1999/xhtml}body")
        if body is not None:
            process_element(body)
        else:
            # Fallback to processing the entire document
            process_element(document)

        # Filter out common unwanted patterns
        filtered_result = []
        for line in result:
            # Skip lines that are likely to be noise
            if any(
                pattern in line.lower()
                for pattern in [
                    "var ",
                    "function()",
                    ".js",
                    ".css",
                    "google-analytics",
                    "disqus",
                    "{",
                    "}",
                ]
            ):
                continue
            filtered_result.append(line)

        return "\n".join(filtered_result)
    except Exception as e:
        logger.error(f"Error parsing HTML: {str(e)}")
        return ""


async def process_urls(urls: List[str], max_concurrent: int = 5) -> List[str]:
    """Process multiple URLs concurrently."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            # Create browser contexts
            n_contexts = min(len(urls), max_concurrent)
            contexts = [
                await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )
                for _ in range(n_contexts)
            ]

            # Create tasks for each URL
            tasks = []
            for i, url in enumerate(urls):
                context = contexts[i % len(contexts)]
                task = fetch_page(url, context)
                tasks.append(task)

            # Gather results with timeout
            try:
                html_contents = await asyncio.gather(*tasks, return_exceptions=True)
                # Handle exceptions and convert all results to strings
                processed_contents: List[str] = []
                for content in html_contents:
                    if isinstance(content, BaseException):
                        logger.error(f"Error processing URL: {str(content)}")
                        processed_contents.append("")
                    elif isinstance(content, str):
                        processed_contents.append(content)
                    else:  # content is None
                        processed_contents.append("")

            except Exception as e:
                logger.error(f"Error gathering results: {str(e)}")
                processed_contents = [""] * len(urls)

            # Parse HTML contents in parallel
            with Pool() as pool:
                results = pool.map(parse_html, processed_contents)

            return results

        finally:
            # Cleanup
            for context in contexts:
                await context.close()
            await browser.close()


def validate_url(url: str) -> bool:
    """Validate if the given string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def main_scraper(urls: List[str]) -> str:
    """Process a list of URLs and extract their content.

    Args:
        urls: List of URLs to scrape content from.

    Returns:
        A string representation of a dictionary mapping URLs to their content.

    Raises:
        SystemExit: If no valid URLs are provided or if an error occurs during execution.
    """
    valid_urls = []
    for url in urls:
        if validate_url(url):
            valid_urls.append(url)
        else:
            logger.error(f"Invalid URL: {url}")

    if not valid_urls:
        logger.error("No valid URLs provided")
        sys.exit(1)

    start_time = time.time()
    try:
        results = asyncio.run(process_urls(valid_urls))
        url_content = {}

        # Print results to stdout
        for url, text in zip(valid_urls, results):
            url_content[url] = text

        logger.info(f"Total processing time: {time.time() - start_time:.2f}s")

        return str(url_content)

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        sys.exit(1)


def main():
    """Command-line interface for the web scraper.

    Provides a command-line interface for fetching and extracting text content
    from webpages. Supports concurrent processing of multiple URLs and debug logging.
    Results are printed to stdout with URL-specific headers.

    Command-line Arguments:
        urls: One or more URLs to process
        --max-concurrent: Maximum number of concurrent browser instances (default: 5)
        --debug: Enable debug logging

    Raises:
        SystemExit: If no valid URLs are provided or if an error occurs during execution.
    """
    parser = argparse.ArgumentParser(
        description="Fetch and extract text content from webpages."
    )
    parser.add_argument("urls", nargs="+", help="URLs to process")
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum number of concurrent browser instances (default: 5)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Validate URLs
    valid_urls = []
    for url in args.urls:
        if validate_url(url):
            valid_urls.append(url)
        else:
            logger.error(f"Invalid URL: {url}")

    if not valid_urls:
        logger.error("No valid URLs provided")
        sys.exit(1)

    start_time = time.time()
    try:
        results = asyncio.run(process_urls(valid_urls, args.max_concurrent))

        # Print results to stdout
        for url, text in zip(valid_urls, results):
            print(f"\n=== Content from {url} ===")
            print(text)
            print("=" * 80)

        logger.info(f"Total processing time: {time.time() - start_time:.2f}s")

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
