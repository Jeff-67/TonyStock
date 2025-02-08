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
from typing import Any, Dict, List, Optional

from opik import track

from prompts.agents.planning import report_planning_prompt
from prompts.tools.tools_schema import (
    tool_prompt_construct_anthropic,
    tool_prompt_construct_openai,
)
from settings import Settings
from tools.analysis.analysis_tool import AnalysisTool
from tools.core.tool_protocol import Tool
from tools.llm_api import aquery_llm
from tools.research.research_tool import ResearchTool
from tools.technical_analysis.ta_tool import TATool
from tools.time.time_tool import get_current_time

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


class Agent:
    """Agent for interacting with Claude AI model."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        tools: Optional[Dict[str, Tool]] = None,
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
        system_text = report_planning_prompt(current_time=get_current_time())
        self.message_history: List[Dict[str, Any]] = [
            {"role": "system", "content": system_text},
            {
                "role": "system",
                "content": "如果有user問你你是誰，或是問候你，請回答你的專長是分析京鼎、文曄還有群聯這三隻股票的觀察家。",
            },
        ]
        self.company_news: list[Dict[str, Any]] = []

    @track()
    async def call_model(self) -> ModelResponse:
        """Make an API call to the model."""
        try:
            # Create new list with shallow copies of each message dict
            messages = [dict(msg) for msg in self.message_history]

            tool_prompt_text = (
                tool_prompt_construct_anthropic()
                if self.provider == "anthropic"
                else tool_prompt_construct_openai()
            )

            return await aquery_llm(
                messages=messages,
                model=self.model_name,
                provider=self.provider,
                tools=tool_prompt_text,
            )
        except Exception as e:
            logger.error(f"Model call failed: {str(e)}")
            raise

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
            response, _ = await self.call_model()
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
                response, _ = await self.call_model()
                self.message_history.append(response.choices[0].message.model_dump())

            return response.choices[0].message.content or "No response generated"
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return f"Error during chat: {str(e)}"


async def main():
    """Run an interactive chat session with the agent."""
    # Create agent first without tools
    agent = Agent(
        provider="anthropic",
        model_name="claude-3-sonnet-20240229",
        tools={},  # Empty tools dict initially
    )

    # Now set up tools using the fully created agent
    tools: Dict[str, Tool] = {
        "research": ResearchTool(lambda news: agent.company_news.extend(news)),
        "analysis_report": AnalysisTool(lambda: agent.company_news),
        "technical_analysis": TATool(),
    }

    # Update agent's tools
    agent.tools = tools
    
    response = await agent.chat("請分析京鼎(3413)近期走勢")
    print('='*100)
    print(response)
    print('='*100)


if __name__ == "__main__":
    asyncio.run(main())
