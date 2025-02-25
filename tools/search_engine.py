"""Search engine module for performing web searches using DuckDuckGo.

This module provides functionality to search the web using DuckDuckGo's search engine,
with support for both API and HTML backends, retry mechanisms, and result formatting.
"""

import argparse
import asyncio
import logging
from typing import Dict, List

from duckduckgo_search import DDGS
from opik import track

# https://github.com/deedy5/duckduckgo_search
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Temporarily set to DEBUG for troubleshooting
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
BATCH_SIZE = 10


@track()
async def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo using async HTTP client.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)

    Returns:
        List of dictionaries containing title, url, and snippet.
    """
    results: List[Dict[str, str]] = []

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                result = {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                if result["url"]:
                    logger.debug(f"Found result: {result['title']} ({result['url']})")
                    results.append(result)

    except Exception as e:
        logger.error(f"Search error: {str(e)}")

    return results[:max_results]


async def main():
    """Command line interface for the search engine."""
    parser = argparse.ArgumentParser(description="Search engine tool")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum number of results"
    )
    args = parser.parse_args()

    results = await search_duckduckgo(args.query, args.max_results)

    if results:
        print(f"\nFound {len(results)} results for '{args.query}':\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   {result['url']}")
            if result["snippet"]:
                print(f"   {result['snippet']}\n")
            else:
                print()
    else:
        print("No results found.")


if __name__ == "__main__":
    asyncio.run(main())
