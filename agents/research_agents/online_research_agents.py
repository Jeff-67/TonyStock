"""Online research agent module for combining search and web scraping functionality.

This module provides a unified interface to search for content using search engine
and automatically scrape all retrieved URLs. It returns the scraped content in a
structured JSON format.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from opik import track

from tools.search_engine import search_duckduckgo
from tools.web_scraper_by_ai import scrape_urls

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MAX_SEARCH_RESULTS = 8


@track()
async def research_keyword(
    keyword: str, max_results: Optional[int] = None
) -> List[Dict]:
    """Search for a keyword and scrape all retrieved URLs.

    Args:
        keyword: The search query to look up
        max_results: Maximum number of search results to process. Defaults to MAX_SEARCH_RESULTS.

    Returns:
        List of dictionaries containing scraped content from each URL:
        [
            {
                "url": str,
                "title": str,
                "content": str,
                "error": Optional[str]
            },
            ...
        ]
    """
    try:
        # Use the search engine to get URLs
        search_results = search_duckduckgo(
            keyword, max_results=max_results or MAX_SEARCH_RESULTS
        )

        if not search_results:
            logger.warning(f"No search results found for keyword: {keyword}")
            return []

        # Extract URLs from search results
        urls = [result["url"] for result in search_results]

        # Scrape all URLs
        scraped_contents = await scrape_urls(urls=urls, query=keyword)

        # Combine search results with scraped content
        research_results = []
        for search_result, scraped_content in zip(search_results, scraped_contents):
            result = {
                "url": search_result["url"],
                "title": search_result["title"],
                "content": (
                    scraped_content
                    if isinstance(scraped_content, str)
                    else scraped_content.get("content", "")
                ),
                "error": (
                    None
                    if isinstance(scraped_content, str)
                    else scraped_content.get("error")
                ),
            }
            research_results.append(result)

        return research_results

    except Exception as e:
        logger.error(f"Error in research_keyword: {str(e)}")
        return [{"error": f"Research failed: {str(e)}"}]


async def main():
    """Test function for the research agent."""
    test_query = "京鼎 3413 半導體設備 訂單 2025"
    logger.info(f"Starting research with query: {test_query}")

    results = await research_keyword(test_query)

    # Print summary
    print("\nResearch Results Summary:")
    print(f"Total results: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        if result.get("error"):
            print(f"Error: {result['error']}")
        else:
            content_preview = (
                result["content"][:200] + "..." if result["content"] else "No content"
            )
            print(f"Content preview: {content_preview}")


if __name__ == "__main__":
    asyncio.run(main())
