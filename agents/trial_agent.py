"""Trial agent module for interacting with Claude AI model.

This module implements a chat agent that can interact with Claude AI model,
process its responses, execute tools based on model requests, and verify
tool execution results. It provides a structured way to handle conversations
with tool usage capabilities.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from opik import track

from agents.research_agents.online_research_agents import research_keyword
from agents.research_agents.search_framework_agent import generate_search_framework
from prompts.system_prompts import (
    finance_agent_prompt,
    system_prompt,
    tool_prompt_construct_anthropic,
    tool_prompt_construct_openai,
)
from settings import Settings
from tools.llm_api import query_llm
from tools.time_tool import get_current_time
from utils.stock_utils import stock_name_to_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
settings = Settings()


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""

    pass


@dataclass
class ToolExecutionResult:
    """Result of a tool execution including success status and output.

    Attributes:
        success: Whether the tool execution was successful
        tool_name: Name of the tool that was executed
        result: Optional result data from the tool execution
        message: Optional message describing the execution result
    """

    success: bool
    tool_name: str
    result: Optional[Any] = None
    message: str = ""


@dataclass
class ModelResponse:
    """Structured response from the Claude model.

    Attributes:
        stop_reason: Reason why the model stopped generating
        content: List of content blocks from the model
        tool_use: Optional tool use request from the model
        text_content: Optional extracted text content from the response
    """

    stop_reason: str
    content: List[Any]
    tool_use: Optional[Dict[str, Any]] = None
    text_content: Optional[str] = None


class Tool(Protocol):
    """Protocol defining the interface for tools."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute the tool with given input data."""
        ...


class ResearchTool:
    """Tool for performing research queries."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute research query using the research_keyword function.

        Args:
            input_data: Dictionary containing the 'query' key with search term

        Returns:
            Research results from the query
        """
        return await research_keyword(input_data["query"])


class TimeTool:
    """Tool for getting current time."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Get current time for specified timezone.

        Args:
            input_data: Dictionary optionally containing 'timezone' key (defaults to 'Asia/Taipei')

        Returns:
            Current time in specified timezone
        """
        return get_current_time(input_data.get("timezone", "Asia/Taipei"))


class SearchFrameworkTool:
    """Tool for generating search frameworks."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Generate a search framework for the given query.

        Args:
            input_data: Dictionary containing the 'query' key with search term

        Returns:
            Generated search framework
        """
        return generate_search_framework(input_data["query"])


class Agent:
    """Agent for interacting with Claude AI model."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        tools: Optional[Dict[str, Tool]] = None,
        stock_name: Optional[str] = None,
    ):
        """Initialize the LLM agent.

        Args:
            provider: Provider name
            model_name: Model name
            tools: Tools
            stock_name: Stock name for system prompt
        """
        self.provider = provider
        self.model_name = model_name
        self.tools: Dict[str, Tool] = tools if tools is not None else {}

        # Initialize system message in history
        system_text = (
            system_prompt(stock_name=stock_name)
            + f"\n<{stock_name} instruction>"
            + finance_agent_prompt(stock_id=stock_name_to_id(stock_name) or stock_name)
            + f"</{stock_name} instruction>"
        )
        self.message_history: List[Dict[str, Any]] = [
            {"role": "system", "content": system_text}
        ]

    @track()
    def call_model(self) -> ModelResponse:
        """Make an API call to the model."""
        # Create new list with shallow copies of each message dict
        messages = [dict(msg) for msg in self.message_history]

        tool_prompt_text = (
            tool_prompt_construct_anthropic()
            if self.provider == "anthropic"
            else tool_prompt_construct_openai()
        )

        return query_llm(
            messages=messages,
            model=self.model_name,
            provider=self.provider,
            tools=tool_prompt_text,
        )

    @track()
    async def process_tool_call(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Any:
        """Process a tool call and return the result."""
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                raise ToolExecutionError(f"Unknown tool: {tool_name}")
            return await tool.execute(tool_input)

        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")

    @track(project_name="tony_stock")
    async def chat(self, user_message: str) -> str:
        """Handle the chat flow with tool usage."""
        try:
            # Add user message to history
            self.message_history.append({"role": "user", "content": user_message})
            response, _ = self.call_model()
            # Add the assistant's message with tool calls to history
            self.message_history.append(response.choices[0].message.model_dump())

            while response.choices[0].message.tool_calls:
                # Process all tool calls and collect their responses
                tool_responses = []
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)

                    logger.info(f"Executing tool {tool_name} with input: {tool_input}")

                    try:
                        # Execute tool
                        tool_result = await self.process_tool_call(
                            tool_name, tool_input
                        )
                        logger.info(f"Tool result: {tool_result}")

                        # Format tool result as JSON string if it's a list or dict
                        formatted_result = (
                            json.dumps(tool_result, ensure_ascii=False, indent=2)
                            if isinstance(tool_result, (list, dict))
                            else str(tool_result)
                        )

                        # Create tool response
                        tool_response = {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_name,
                            "content": formatted_result,
                        }
                        tool_responses.append(tool_response)
                    except ToolExecutionError as e:
                        logger.error(f"Tool execution error: {str(e)}")
                        return f"Error executing tool: {str(e)}"

                # Update message history with all tool responses at once
                self.message_history.extend(tool_responses)

                # Continue conversation with empty messages since history is updated
                response, _ = self.call_model()
                self.message_history.append(response.choices[0].message.model_dump())

            return response.choices[0].message.content or "No response generated"
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return f"Error during chat: {str(e)}"


if __name__ == "__main__":
    agent = Agent(
        provider="anthropic",
        model_name="claude-3-5-sonnet-latest",
        tools={
            "research": ResearchTool(),
            "time_tool": TimeTool(),
            "search_framework": SearchFrameworkTool(),
        },
        stock_name="京鼎",
    )
    response = asyncio.run(agent.chat("請幫我統整京鼎新聞"))
    print(response)
