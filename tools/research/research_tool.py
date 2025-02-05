"""Research tool implementation.

This module implements the research tool for performing keyword searches.
"""

from typing import Any, Callable, Dict, List

from agents.research_agents.online_search_agents import research_keyword
from tools.core.tool_protocol import Tool


class ResearchTool(Tool):
    """Tool for performing research queries."""

    def __init__(self, update_news_callback: Callable[[List[Dict[str, str]]], None]):
        """Initialize the tool with a callback function.

        Args:
            update_news_callback: Function to call with new company news
        """
        self.update_news = update_news_callback

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute research query using the research_keyword function.

        Args:
            input_data: Dictionary containing the 'query' key with search term

        Returns:
            Research results from the query
        """
        company_news = await research_keyword(input_data["query"])
        self.update_news(company_news)
        return company_news
