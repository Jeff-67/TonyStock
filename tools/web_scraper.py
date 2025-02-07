"""Web scraper module for fetching and extracting text content from webpages.

This module provides functionality to asynchronously scrape web pages using Playwright,
parse their HTML content, and extract meaningful text while preserving hyperlinks in
markdown format. It supports concurrent processing of multiple URLs and includes
validation and error handling.
"""

# mypy: ignore-errors

import argparse
import asyncio
import logging
import os
import sys
import time
from multiprocessing import Pool
from typing import List, Optional
from urllib.parse import urlparse

import html5lib
from opik import track
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


async def download_file(
    url: str, context, download_dir: str = "downloads"
) -> Optional[str]:
    """Asynchronously download a file."""
    page = await context.new_page()
    try:
        logger.info(f"Downloading file from {url}")

        # Create downloads directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)

        # First navigate to the page
        await page.goto(url)
        await page.wait_for_load_state("networkidle")

        # Try to find the main content area or PDF viewer
        content_selectors = [
            "#annotationLayer1",  # Try the annotation layer directly
            "canvas",
            ".contextMenu__link",
            "#pdf-viewer",
            ".pdf-container",
        ]

        for selector in content_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    logger.info(f"Found content element with selector: {selector}")

                    # Get element position
                    box = await element.bounding_box()
                    if box:
                        # Click in the middle of the element
                        x = box["x"] + box["width"] / 2
                        y = box["y"] + box["height"] / 2

                        # Simulate right click at coordinates
                        await page.mouse.move(x, y)
                        await page.mouse.down(button="right")
                        await page.mouse.up(button="right")
                        await page.wait_for_timeout(1000)  # Wait for context menu

                        # Look for download links in the context menu
                        download_selectors = [
                            'a:has-text("下載")',
                            "a.contextMenu__link",
                            "a[download]",
                            'a[href*=".pdf"]',
                        ]

                        for download_selector in download_selectors:
                            try:
                                # Use JavaScript to find and click the download link
                                download_element = await page.wait_for_selector(
                                    download_selector, timeout=5000
                                )
                                if download_element:
                                    logger.info(
                                        f"Found download element with selector: {download_selector}"
                                    )

                                    # Get the href and download attributes
                                    href = await download_element.get_attribute("href")
                                    download_filename = (
                                        await download_element.get_attribute("download")
                                    )

                                    if href:
                                        logger.info(f"Found download link: {href}")
                                        # If it's a relative URL, make it absolute
                                        if href.startswith("/"):
                                            parsed_url = urlparse(url)
                                            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                            href = base_url + href

                                        # Setup download handling
                                        async with page.expect_download(
                                            timeout=30000
                                        ) as download_info:
                                            # Use JavaScript to trigger the download
                                            await page.evaluate(
                                                """(element) => {
                                                element.click();
                                                if (!element.click) {
                                                    const event = new MouseEvent('click', {
                                                        bubbles: true,
                                                        cancelable: true,
                                                        view: window
                                                    });
                                                    element.dispatchEvent(event);
                                                }
                                            }""",
                                                download_element,
                                            )

                                            download = await download_info.value

                                            # Use the download attribute filename if available
                                            filename = (
                                                download_filename
                                                or download.suggested_filename
                                            )
                                            path = os.path.join(download_dir, filename)
                                            await download.save_as(path)

                                            logger.info(
                                                f"Successfully downloaded file to {path}"
                                            )
                                            return path
                            except Exception as e:
                                logger.debug(
                                    f"Download selector {download_selector} failed: {str(e)}"
                                )
                                continue
            except Exception as e:
                logger.debug(f"Content selector {selector} failed: {str(e)}")
                continue

        logger.error("No download link found on the page")
        return None

    except Exception as e:
        logger.error(f"Error downloading from {url}: {str(e)}")
        return None
    finally:
        await page.close()


async def fetch_page(url: str, context) -> Optional[str]:
    """Asynchronously fetch a webpage's content."""
    page = await context.new_page()
    try:
        logger.info(f"Fetching {url}")

        # Monitor network requests
        async def log_request(request):
            if request.resource_type in ["xhr", "fetch"]:
                logger.info(f"Network request: {request.method} {request.url}")
                if request.post_data:
                    logger.info(f"Post data: {request.post_data}")

        page.on("request", log_request)

        # Enable JavaScript console
        page.on("console", lambda msg: logger.info(f"Console: {msg.text}"))

        await page.goto(url)
        await page.wait_for_load_state("networkidle")

        # Get page state
        state = await page.evaluate(
            """() => {
            return {
                url: window.location.href,
                token: new URLSearchParams(window.location.search).get('token'),
                documentId: window.__NUXT__?.state?.document?.id,
                fileInfo: window.__NUXT__?.state?.document?.fileInfo
            }
        }"""
        )
        logger.info(f"Page state: {state}")

        content = await page.content()
        logger.info(f"Successfully fetched {url}")
        return content
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None
    finally:
        await page.close()


@track()
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


@track()
async def scrape_urls(
    urls: List[str],
    max_concurrent: int = 5,
    download_mode: bool = False,
    download_dir: str = "downloads",
) -> List[str]:
    """Process multiple URLs concurrently."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            # Create browser contexts
            n_contexts = min(len(urls), max_concurrent)
            contexts = [await browser.new_context() for _ in range(n_contexts)]

            # Create tasks for each URL
            tasks = []
            for i, url in enumerate(urls):
                context = contexts[i % len(contexts)]
                if download_mode:
                    task = download_file(url, context, download_dir)
                else:
                    task = fetch_page(url, context)
                tasks.append(task)

            # Gather results
            results = await asyncio.gather(*tasks)

            if not download_mode:
                # Parse HTML contents in parallel
                with Pool() as pool:
                    results = pool.map(parse_html, results)

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


def main():
    """Execute the web scraper from command line arguments.

    Parses command line arguments, validates URLs, and orchestrates the web scraping
    process. Supports concurrent processing of multiple URLs and outputs the extracted
    content to stdout. Includes debug logging options and error handling.
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
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download files instead of scraping content",
    )
    parser.add_argument(
        "--download-dir", default="downloads", help="Directory to save downloaded files"
    )

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
        results = asyncio.run(
            scrape_urls(
                valid_urls, args.max_concurrent, args.download, args.download_dir
            )
        )

        # Print results to stdout
        for url, result in zip(valid_urls, results):
            if args.download:
                if result:
                    print(f"Successfully downloaded from {url} to {result}")
                else:
                    print(f"Failed to download from {url}")
            else:
                print(f"\n=== Content from {url} ===")
                print(result)
                print("=" * 80)

        logger.info(f"Total processing time: {time.time() - start_time:.2f}s")

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
