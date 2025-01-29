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

import anthropic
from opik import opik_context, track
from opik.integrations.anthropic import track_anthropic
from tokencost import calculate_cost_by_tokens

from agents.research_agents.onlin_research_agents import research_keyword
from agents.research_agents.search_framework_agent import generate_search_framework
from prompts.system_prompts import (
    finance_agent_prompt,
    system_prompt,
    tool_prompt_construct_anthropic,
)
from settings import Settings
from tools.time_tool import get_current_time
from utils.stock_utils import retrieve_stock_name, stock_name_to_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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


class ClaudeAgent:
    """Agent for interacting with Claude AI model."""

    def __init__(
        self,
        client: Optional[anthropic.Client] = None,
        settings: Optional[Settings] = None,
    ):
        """Initialize the Claude agent.

        Args:
            client: Anthropic client instance
            settings: Settings instance
        """
        self.client = client or track_anthropic(anthropic.Client())
        self.settings = settings or Settings()
        self.message_history: List[Dict[str, Any]] = []
        self.tools: Dict[str, Tool] = {
            "research": ResearchTool(),
            "time_tool": TimeTool(),
            "search_framework": SearchFrameworkTool(),
        }

    @track()
    def process_model_response(
        self,
        system: str,
        model: str,
        max_tokens: int,
        tool_choice: Dict[str, Any],
        tools: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> ModelResponse:
        """Process the model response."""
        response = self.client.messages.create(
            system=system,
            model=model,
            max_tokens=max_tokens,
            tool_choice=tool_choice,
            tools=tools,
            messages=messages,
        )

        text_content = next(
            (block.text for block in response.content if hasattr(block, "text")), None
        )
        tool_use = next(
            (block for block in response.content if block.type == "tool_use"), None
        )

        opik_context.update_current_span(
            total_cost=calculate_cost_by_tokens(
                response.usage.input_tokens, model=response.model, token_type="input"
            )
            + calculate_cost_by_tokens(
                response.usage.output_tokens, model=response.model, token_type="output"
            )
        )

        return ModelResponse(
            stop_reason=response.stop_reason,
            content=response.content,
            tool_use=tool_use,
            text_content=text_content,
        )

    @track()
    def call_model(
        self,
        user_messages: List[Dict[str, Any]],
    ) -> ModelResponse:
        """Make an API call to the model."""
        self.message_history.extend(user_messages)
        stock_name = retrieve_stock_name(user_messages)
        system_text = (
            system_prompt(stock_name=stock_name)
            + f"\n<{stock_name} instruction>"
            + finance_agent_prompt(stock_id=stock_name_to_id(stock_name) or stock_name)
            + f"</{stock_name} instruction>"
        )
        tool_choice = {"type": "auto"}
        tool_prompt_text = tool_prompt_construct_anthropic()["tools"]

        return self.process_model_response(
            system=system_text,
            model=self.settings.model.claude_large,
            max_tokens=self.settings.max_tokens,
            tool_choice=tool_choice,
            tools=tool_prompt_text,
            messages=self.message_history,
        )

    @track()
    async def process_tool_call(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Any:
        """Process a tool call and return the result."""
        try:
            tool = self.tools.get(tool_name)
            if tool is None:
                raise ToolExecutionError(f"Unknown tool: {tool_name}")
            return await tool.execute(tool_input)
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")

    @track(project_name="tony_stock")
    async def chat(self, user_message: str) -> str:
        """Handle the chat flow with tool usage."""
        try:
            # Initial call with system prompt
            response = self.call_model([{"role": "user", "content": user_message}])

            while response.stop_reason == "tool_use" and response.tool_use:
                tool_name = response.tool_use.name
                tool_input = response.tool_use.input

                logger.info(f"Executing tool {tool_name} with input: {tool_input}")

                try:
                    # Execute tool
                    tool_result = await self.process_tool_call(tool_name, tool_input)
                    logger.info(f"Tool result: {tool_result}")

                    # Continue conversation with verified result
                    self.message_history.append(
                        {"role": "assistant", "content": response.content}
                    )

                    # Format tool result as JSON string if it's a list or dict
                    formatted_result = (
                        json.dumps(tool_result, ensure_ascii=False, indent=2)
                        if isinstance(tool_result, (list, dict))
                        else str(tool_result)
                    )

                    response = self.call_model(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": response.tool_use.id,
                                        "content": formatted_result,
                                    }
                                ],
                            }
                        ]
                    )
                except ToolExecutionError as e:
                    logger.error(f"Tool execution error: {str(e)}")
                    return f"Error executing tool: {str(e)}"

            return response.text_content or "No response generated"
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return f"Error during chat: {str(e)}"


if __name__ == "__main__":
    agent = ClaudeAgent()
    response = asyncio.run(agent.chat("群聯"))
    print(response)
