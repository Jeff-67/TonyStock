"""Search engine module for performing web searches using DuckDuckGo.

This module provides functionality to search the web using DuckDuckGo's search engine,
with support for both API and HTML backends, retry mechanisms, and result formatting.
"""

import json
import logging
import random
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
PROXY_TEST_TIMEOUT = 5
MAX_RETRIES = 3
BATCH_SIZE = 10

# List of proxies
PROXY_LIST = [
    "156.228.109.7:3128",
    "156.228.104.132:3128",
    "154.213.193.17:3128",
    "154.94.15.112:3128",
    "156.253.167.233:3128",
    "154.214.1.75:3128",
]


def get_working_proxy() -> Optional[str]:
    """Get a working proxy from the list."""
    proxies = PROXY_LIST.copy()
    random.shuffle(proxies)

    for proxy in proxies:
        if validate_proxy(proxy):
            return proxy
    return None


def validate_proxy(proxy: str) -> bool:
    """Test if a proxy is working."""
    try:
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        response = requests.get(
            "https://api.ipify.org",
            params={"format": "json"},
            proxies=proxies,
            timeout=PROXY_TEST_TIMEOUT,
        )
        if response.ok:
            data = response.json()
            logger.info(f"Proxy {proxy} is working (IP: {data.get('ip')})")
            return True
    except (requests.RequestException, json.JSONDecodeError) as e:
        logger.debug(f"Proxy {proxy} validation failed: {str(e)}")
    return False


def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Search DuckDuckGo using requests library.

    Returns a list of dictionaries containing title, url, and snippet.
    """
    results: List[Dict[str, str]] = []
    proxy = get_working_proxy()

    if not proxy:
        logger.warning("No working proxy found, attempting search without proxy")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        proxies = None
        if proxy:
            proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}

        safe_query = quote_plus(query)
        response = requests.get(
            "https://duckduckgo.com/lite",
            params={"q": safe_query},
            headers=headers,
            proxies=proxies,
            timeout=DEFAULT_TIMEOUT,
        )

        if response.ok:
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
        else:
            logger.error(f"Search failed with status code {response.status_code}")

    except Exception as e:
        logger.error(f"Search error: {str(e)}")

    return results[:max_results]


def main():
    """Command line interface for the search engine."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Search engine tool")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum number of results"
    )
    args = parser.parse_args()

    results = search_duckduckgo(args.query, args.max_results)

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
    main()
