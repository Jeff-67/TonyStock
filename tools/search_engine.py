"""Search engine module for performing web searches using DuckDuckGo.

This module provides functionality to search the web using DuckDuckGo's search engine,
with support for both API and HTML backends, retry mechanisms, and result formatting.
"""

# !/usr/bin/env python3

import argparse
import logging
import random
import sys
import time
from typing import Any, Dict, List

from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_random_user_agent():
    """Return a random User-Agent string."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    return random.choice(user_agents)


def search_with_retry(query, max_results=10, max_retries=3, initial_delay=2):
    """Perform search with retry mechanism.

    This function handles the actual search operation with a built-in retry mechanism
    to handle temporary failures and rate limiting.

    Args:
        query (str): Search query string to execute
        max_results (int, optional): Maximum number of results to return. Defaults to 10.
        max_retries (int, optional): Maximum number of retry attempts. Defaults to 3.
        initial_delay (int, optional): Initial delay between retries in seconds. Defaults to 2.

    Returns:
        list: List of search results, each containing URL, title, and snippet.

    Raises:
        Exception: If all retry attempts fail.
    """
    for attempt in range(max_retries):
        try:
            headers = {"User-Agent": get_random_user_agent()}

            print(
                f"DEBUG: Attempt {attempt + 1}/{max_retries} - Searching for query: {query}",
                file=sys.stderr,
            )

            with DDGS(headers=headers) as ddgs:
                # Try API backend first, fallback to HTML if needed
                try:
                    results = list(
                        ddgs.text(query, max_results=max_results, backend="api")
                    )
                except DuckDuckGoSearchException as api_error:
                    print(
                        f"DEBUG: API backend failed, trying HTML backend: {str(api_error)}",
                        file=sys.stderr,
                    )
                    # Add delay before trying HTML backend
                    time.sleep(1)
                    results = list(
                        ddgs.text(query, max_results=max_results, backend="html")
                    )

                if not results:
                    print("DEBUG: No results found", file=sys.stderr)
                    return []

                print(f"DEBUG: Found {len(results)} results", file=sys.stderr)
                return results

        except Exception as e:
            print(f"ERROR: Attempt {attempt + 1} failed: {str(e)}", file=sys.stderr)
            if attempt < max_retries - 1:
                delay = initial_delay * (attempt + 1) + random.random() * 2
                print(
                    f"DEBUG: Waiting {delay:.2f} seconds before retry...",
                    file=sys.stderr,
                )
                time.sleep(delay)
            else:
                print("ERROR: All retry attempts failed", file=sys.stderr)
                raise


def format_results(results):
    """Format and print search results in a human-readable format.

    Args:
        results (list): List of search results to format and print.
    """
    for i, r in enumerate(results, 1):
        print(f"\n=== Result {i} ===")
        print(f"URL: {r.get('link', r.get('href', 'N/A'))}")
        print(f"Title: {r.get('title', 'N/A')}")
        print(f"Snippet: {r.get('snippet', r.get('body', 'N/A'))}")


def search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Execute a search query and return formatted results.

    This is the main entry point for performing searches. It handles input validation,
    executes the search with retry mechanism, and formats the results.

    Args:
        query (str): Search query string to execute.
        max_results (int, optional): Maximum number of results to return. Defaults to 10.

    Returns:
        List[str]: List of formatted search results.

    Raises:
        ValueError: If the query is invalid.
        Exception: If the search operation fails.
    """
    try:
        if not query or not isinstance(query, str):
            logger.error("Invalid query")
            raise ValueError("Invalid query")

        results = search_with_retry(query, max_results)
        if results:
            format_results(results)
            formatted_results = []
            for r in results:
                formatted_results.append(
                    {
                        "url": r.get("link", r.get("href", "N/A")),
                        "title": r.get("title", "N/A"),
                        "snippet": r.get("snippet", r.get("body", "N/A")),
                    }
                )
            return formatted_results
        return []

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise  # Re-raise the exception instead of sys.exit()


def main():
    """Command-line interface for DuckDuckGo search.

    Provides a command-line interface for performing web searches using DuckDuckGo.
    Supports configurable maximum results and handles errors gracefully.

    Command-line Arguments:
        query: Search query string
        --max-results: Maximum number of results to return (default: 10)

    The results are printed to stdout in a formatted manner.
    """
    parser = argparse.ArgumentParser(
        description="Search using DuckDuckGo with fallback mechanisms"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )

    args = parser.parse_args()
    search(args.query, args.max_results)


if __name__ == "__main__":
    main()
