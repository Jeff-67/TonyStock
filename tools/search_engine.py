"""Search engine module for performing web searches using DuckDuckGo.

This module provides functionality to search the web using DuckDuckGo's search engine,
with support for both API and HTML backends, retry mechanisms, and result formatting.
"""

import argparse
import asyncio
import logging
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup
from opik import track

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

    Returns a list of dictionaries containing title, url, and snippet.
    """
    results: List[Dict[str, str]] = []

    async with httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        },
        follow_redirects=True,
    ) as client:
        try:
            url = "https://duckduckgo.com/lite"
            params = {"q": query, "kl": "tw-tzh"}

            response = await client.get(url, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.find_all("tr")

            current_result: Dict[str, str] = {}
            for row in rows:
                link = row.find("a", class_="result-link")
                snippet = row.find("td", class_="result-snippet")

                if link:
                    if current_result and len(results) < max_results:
                        results.append(current_result)
                    current_result = {
                        "title": link.get_text(strip=True),
                        "url": link.get("href", ""),
                        "snippet": "",
                    }
                elif snippet and current_result:
                    current_result["snippet"] = snippet.get_text(strip=True)

            if current_result and len(results) < max_results:
                results.append(current_result)

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
