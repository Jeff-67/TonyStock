"""Research agent module that combines search framework generation and online research.

This module provides a unified interface that:
1. Generates a structured search framework using search_framework_agent
2. Uses the generated queries to perform online research using online_search_agents
3. Returns combined research results
"""

import asyncio
import logging
from typing import Any, Dict, List

from opik import track

from agents.research_agents.online_search_agents import search_keyword
from agents.research_agents.search_framework_agent import generate_search_framework

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@track()
async def perform_research(
    company_name: str, user_message: str
) -> List[Dict[str, Any]]:
    """Perform comprehensive research by combining search framework and online research.

    Args:
        company_name: Name of the company to research
        user_message: User's specific research request or focus

    Returns:
        Dict containing:
        {
            "framework": str,  # The generated search framework
            "research_results": List[Dict]  # Results from online research
        }
    """
    try:
        # Step 1: Generate search framework
        logger.info(f"Generating search framework for: {company_name}")
        framework = await generate_search_framework(company_name, user_message)

        # Step 2: Create tasks for concurrent execution
        tasks = []
        for query_item in framework:
            query = query_item["query"]
            logger.info(f"Creating research task for query: {query}")
            tasks.append(search_keyword(query))

        # Step 3: Execute all research tasks concurrently
        search_results = await asyncio.gather(*tasks)

        # Step 4: Combine results with their corresponding queries
        research_results = [
            {"query": query_item, "search_results": results}
            for query_item, results in zip(framework, search_results)
        ]

        return research_results

    except Exception as e:
        logger.error(f"Error in perform_research: {str(e)}")
        raise


async def main():
    """Test function for the research agent."""
    test_company = "群聯"
    test_message = "Please research recent news about AI and their market strategy"

    logger.info(f"Starting comprehensive research for: {test_company}")

    try:
        research_results = await perform_research(test_company, test_message)

        # Print results
        print("\nResearch Results:")
        for i, result in enumerate(research_results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Query Item: {result['query']}")
            for search_result in result["search_results"]:
                print("\nSearch Result:")
                print(f"Title: {search_result.get('title', 'No title')}")
                print(f"URL: {search_result.get('url', 'No URL')}")
                if search_result.get("error"):
                    print(f"Error: {search_result['error']}")
                else:
                    content = search_result.get("content", "")
                    content_preview = f"{content[:200]}..." if content else "No content"
                    print(f"Content preview: {content_preview}")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise  # Add raise to propagate the error for better debugging


if __name__ == "__main__":
    asyncio.run(main())
