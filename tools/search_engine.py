"""Search engine module for performing web searches using DuckDuckGo and direct site search.

This module provides functionality to search the web using DuckDuckGo's search engine
and direct site search for specific financial news sources.
"""

import argparse
import asyncio
import logging
from typing import Dict, List
import urllib.parse

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

# Financial news sites to search directly
FINANCIAL_SITES = [
    {
        "domain": "money.udn.com",
        "search_url": "https://money.udn.com/search/result/1001/{query}",
        "result_selector": "div.story-list__news",
        "link_selector": "a.story-list__text",
        "snippet_selector": "p.story-list__text"
    },
    {
        "domain": "news.cnyes.com",
        "search_url": "https://news.cnyes.com/search?query={query}",
        "result_selector": "div.jsx-2605922312",
        "link_selector": "a.jsx-2605922312",
        "snippet_selector": "div.summary"
    },
    {
        "domain": "www.moneydj.com",
        "search_url": "https://www.moneydj.com/KMDJ/Search/list.aspx?_Query_={query}",
        "result_selector": "div.r-list",
        "link_selector": "a.r-title",
        "snippet_selector": "div.r-desc"
    }
]

@track()
async def search_financial_sites(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Search specific financial news sites directly.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries containing title, url, and snippet
    """
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache"
    }
    
    async with httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT,
        headers=headers,
        follow_redirects=True
    ) as client:
        for site in FINANCIAL_SITES:
            try:
                encoded_query = urllib.parse.quote(query)
                url = site["search_url"].format(query=encoded_query)
                
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Try multiple selector combinations
                items = (
                    soup.select(site["result_selector"]) or
                    soup.find_all("div", class_=lambda x: x and "story" in x.lower()) or
                    soup.find_all("div", class_=lambda x: x and "news" in x.lower()) or
                    []
                )
                
                logger.debug(f"Found {len(items)} items on {site['domain']}")
                
                for item in items[:max_results]:
                    # Try to find the link with multiple selectors
                    link = (
                        item.select_one(site["link_selector"]) or
                        item.find("a", class_=lambda x: x and ("title" in x.lower() or "headline" in x.lower())) or
                        item.find("a")
                    )
                    
                    if not link:
                        continue
                        
                    title = link.get_text(strip=True)
                    url = link.get("href", "")
                    
                    # Handle relative URLs
                    if url and not url.startswith(("http://", "https://")):
                        url = f"https://{site['domain']}" + (url if url.startswith("/") else f"/{url}")
                        
                    # Skip if missing essential info
                    if not (title and url):
                        continue
                        
                    # Try to find snippet with multiple selectors
                    snippet_elem = (
                        item.select_one(site["snippet_selector"]) or
                        item.find("p", class_=lambda x: x and ("desc" in x.lower() or "summary" in x.lower())) or
                        item.find("div", class_=lambda x: x and ("desc" in x.lower() or "summary" in x.lower()))
                    )
                    
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
                    
                    if len(results) >= max_results:
                        return results
                        
            except Exception as e:
                logger.warning(f"Error searching {site['domain']}: {str(e)}")
                continue
                
    return results[:max_results]

@track()
async def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Search DuckDuckGo using async HTTP client.

    Returns a list of dictionaries containing title, url, and snippet.
    """
    results: List[Dict[str, str]] = []
    
    # Encode query properly for Chinese characters
    encoded_query = urllib.parse.quote(query)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

    async with httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT,
        headers=headers,
        follow_redirects=True,
    ) as client:
        try:
            # Try both HTML and lite versions
            urls = [
                f"https://html.duckduckgo.com/html/?q={encoded_query}",
                f"https://duckduckgo.com/lite?q={encoded_query}"
            ]
            
            for url in urls:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Try different result selectors
                    result_elements = (
                        soup.find_all("div", class_="result") or  # HTML version
                        soup.find_all("tr", class_="result-link") or  # Lite version
                        []
                    )
                    
                    for element in result_elements:
                        if len(results) >= max_results:
                            break
                            
                        link = element.find("a")
                        if not link:
                            continue
                            
                        title = link.get_text(strip=True)
                        url = link.get("href", "")
                        
                        # Skip if missing essential info
                        if not (title and url):
                            continue
                            
                        snippet = ""
                        snippet_element = element.find(
                            ["div", "td"], 
                            class_=["result__snippet", "result-snippet"]
                        )
                        if snippet_element:
                            snippet = snippet_element.get_text(strip=True)
                            
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
                    
                    if results:  # If we got results, no need to try other URLs
                        break
                        
                except Exception as e:
                    logger.warning(f"Error with URL {url}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Search error: {str(e)}")

    return results[:max_results]

async def search(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Combined search function that tries both DuckDuckGo and direct site search.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        Combined list of search results
    """
    # Try DuckDuckGo first
    results = await search_duckduckgo(query, max_results)
    
    # If no results, try financial sites
    if not results:
        logger.info("No DuckDuckGo results, trying financial sites...")
        results = await search_financial_sites(query, max_results)
        
    return results

async def main():
    """Command line interface for the search engine."""
    parser = argparse.ArgumentParser(description="Search engine tool")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--max-results", type=int, default=10, help="Maximum number of results"
    )
    args = parser.parse_args()

    results = await search(args.query, args.max_results)

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
