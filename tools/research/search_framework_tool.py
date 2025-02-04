"""Search framework tool implementation.

This module implements the search framework tool for generating search frameworks.
"""

from typing import Any, Dict

from agents.research_agents.search_framework_agent import generate_search_framework
from tools.core.tool_protocol import Tool


class SearchFrameworkTool(Tool):
    """Tool for generating search frameworks."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Generate a search framework for the given query.

        Args:
            input_data: Dictionary containing the 'query' key with search term

        Returns:
            Generated search framework
        """
        return generate_search_framework(input_data["query"])
