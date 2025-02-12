"""Online research agent module for combining search and web scraping functionality.

This module provides a unified interface to search for content using search engine
and automatically scrape all retrieved URLs. It returns the scraped content in a
structured JSON format.
"""

import asyncio
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from opik import track

from tools.search_engine import search
from tools.web_scraper_by_ai import scrape_urls
from ..base import BaseAgent, AnalysisResult, BaseAnalysisData

# Configure logging
logger = logging.getLogger(__name__)

MAX_SEARCH_RESULTS = 2

@dataclass
class SearchResult:
    """Structure for individual search result."""
    url: str
    title: str
    content: str = ""
    error: Optional[str] = None

@dataclass
class SearchAnalysisData(BaseAnalysisData):
    """Structure for search analysis data."""
    keyword: str
    max_results: int
    search_results: List[SearchResult]
    total_results: int = 0
    
    @classmethod
    def from_search_results(cls, keyword: str, max_results: int, results: List[SearchResult]) -> 'SearchAnalysisData':
        """Create instance from search results."""
        return cls(
            symbol=keyword,  # Using keyword as symbol for compatibility
            date=datetime.now().strftime("%Y%m%d"),
            keyword=keyword,
            max_results=max_results,
            search_results=results,
            total_results=len(results)
        )

class OnlineSearchAgent(BaseAgent):
    """Agent specialized in online search and web scraping."""
    
    def __init__(self, provider: str = "anthropic", model_name: str = "claude-3-sonnet-20240229"):
        """Initialize the online search agent."""
        super().__init__(provider=provider, model_name=model_name)
        
    @track()
    async def search_keyword(self, keyword: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """Search for a keyword and scrape all retrieved URLs.

        Args:
            keyword: The search query to look up
            max_results: Maximum number of search results to process. Defaults to MAX_SEARCH_RESULTS.

        Returns:
            List of SearchResult objects containing scraped content from each URL
        """
        try:
            # Use the combined search function
            search_results = await search(
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
            results = []
            for search_result, scraped_content in zip(search_results, scraped_contents):
                content = (
                    scraped_content
                    if isinstance(scraped_content, str)
                    else scraped_content.get("content", "")
                )
                error = (
                    None
                    if isinstance(scraped_content, str)
                    else scraped_content.get("error")
                )
                
                result = SearchResult(
                    url=search_result["url"],
                    title=search_result["title"],
                    content=content,
                    error=error
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error in search_keyword: {str(e)}")
            return [SearchResult(url="", title="", error=f"Search failed: {str(e)}")]
            
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Perform search analysis for the given query.
        
        Args:
            query: The search query
            **kwargs: Additional arguments including max_results
            
        Returns:
            AnalysisResult containing the search results
        """
        try:
            max_results = kwargs.get('max_results', MAX_SEARCH_RESULTS)
            
            # Execute search
            search_results = await self.search_keyword(query, max_results)
            
            # Prepare analysis data
            analysis_data = SearchAnalysisData.from_search_results(
                keyword=query,
                max_results=max_results,
                results=search_results
            )
            
            # Format content summary
            content_summary = []
            for result in search_results:
                if result.error:
                    content_summary.append(f"Error: {result.error}")
                else:
                    preview = f"{result.content[:200]}..." if result.content else "No content"
                    content_summary.append(
                        f"Title: {result.title}\n"
                        f"URL: {result.url}\n"
                        f"Preview: {preview}\n"
                    )
            
            return AnalysisResult(
                success=True,
                content="\n\n".join(content_summary),
                metadata={
                    "query": query,
                    "max_results": max_results,
                    "total_results": len(search_results)
                },
                analysis_data=analysis_data
            )
            
        except Exception as e:
            return self.format_error_response(e)

async def main():
    """Test function for the online search agent."""
    test_query = "京鼎精密 3413 半導體設備"  # Updated query
    logger.info(f"Starting research with query: {test_query}")

    try:
        agent = OnlineSearchAgent()
        result = await agent.analyze(test_query, max_results=3)
        
        if result.success:
            print("\nSearch Results Summary:")
            print(f"Total results: {result.metadata['total_results']}")
            print("\nResults:")
            print(result.content)
            
            if result.metadata['total_results'] == 0:
                print("\nNo results found. Try these troubleshooting steps:")
                print("1. Check internet connectivity")
                print("2. Try a different search query")
                print("3. Verify the search service is accessible")
                print("\nDebug Info:")
                print(f"Query used: {test_query}")
                print(f"Metadata: {result.metadata}")
        else:
            print(f"\nError: {result.error}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 