"""Analysis tool implementation.

This module implements the analysis tool for generating stock news analysis reports.
"""

from typing import Any, Callable, Dict, List

from agents.analysis_agents.analysis_report_agent import generate_analysis_report
from tools.core.tool_protocol import Tool


class AnalysisTool(Tool):
    """Tool for generating stock news analysis report."""

    def __init__(self, get_news_callback: Callable[[], List[Dict[str, str]]]):
        """Initialize the tool with a callback function.

        Args:
            get_news_callback: Function to get company news
        """
        self.get_news = get_news_callback

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute analysis query using the analysis_report function.

        Args:
            input_data: Dictionary containing the 'company_name' key

        Returns:
            Generated analysis report
        """
        return await generate_analysis_report(
            self.get_news(), input_data["company_name"]
        )
