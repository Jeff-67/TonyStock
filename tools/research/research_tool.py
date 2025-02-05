"""Research tool implementation.

This module implements the research tool for performing keyword searches.
"""

from typing import Any, Callable, Dict, List

from agents.research_agents.research_agent import perform_research
from tools.core.tool_protocol import Tool


class ResearchTool(Tool):
    """Tool for performing research queries."""

    def __init__(self, update_news_callback: Callable[[List[Dict[str, Any]]], None]):
        """Initialize the tool with a callback function.

        Args:
            update_news_callback: Function to call with new company news
        """
        self.update_news = update_news_callback

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute research query using the search_keyword function.

        Args:
            input_data: Dictionary containing the 'company_name' and 'user_message' keys

        Returns:
            Research results from the query
        """
        company_news = await perform_research(
            input_data["company_name"], input_data["user_message"]
        )
        self.update_news(company_news)
        return company_news
