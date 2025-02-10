"""Analysis tool module.

This module provides tools for performing various types of analysis.
"""

import logging
from typing import Any, Callable, Dict, List

from tools.core.tool_protocol import Tool
from agents.planning_agents.planning_report_agent import PlanningAgent

logger = logging.getLogger(__name__)


class PlanningTool(Tool):
    """Tool for generating analysis plans."""

    def __init__(self, news_callback: Callable[[], List[Dict[str, Any]]]):
        """Initialize the planning tool.
        
        Args:
            news_callback: Callback to get news data
        """
        super().__init__()
        self.news_callback = news_callback

    async def execute(self, params: Dict[str, Any]) -> tuple[str, str]:
        """Execute the planning tool.
        
        Args:
            params: Parameters including user message
            
        Returns:
            Tuple of (plan, company_name)
        """
        try:
            user_message = params.get("user_message")
            if not user_message:
                raise ValueError("User message is required")

            # Get news data using callback
            news_data = self.news_callback()

            # Generate planning report
            agent = PlanningAgent()
            result = await agent.analyze(
                query=user_message,
                news_data=news_data
            )

            if not result.success:
                raise ValueError(f"Planning failed: {result.error}")

            return result.content, result.metadata["company_name"]

        except Exception as e:
            logger.error(f"Planning tool execution failed: {str(e)}")
            raise
