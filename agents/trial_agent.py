"""Trial agent module for interacting with Claude AI model.

This module implements a chat agent that can interact with Claude AI model,
process its responses, execute tools based on model requests, and verify
tool execution results. It provides a structured way to handle conversations
with tool usage capabilities.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import anthropic
from opik import track

from prompts.system_prompts import (
    finance_agent_prompt,
    system_prompt,
    tool_prompt_construct_anthropic,
)
from settings import Settings
from tools.search_engine import search_duckduckgo
from tools.web_scraper import scrape_urls

client = anthropic.Client()
settings = Settings()
MODEL_NAME = settings.model.claude_large
MAX_SEARCH_RESULTS = 5
MESSAGE_HISTORY = []


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


@track()
def process_model_response(response: anthropic.types.Message) -> ModelResponse:
    """Process the raw model response into a structured format.

    Args:
        response: Raw response from the model

    Returns:
        ModelResponse containing structured response data
    """
    text_content = next(
        (block.text for block in response.content if hasattr(block, "text")), None
    )
    tool_use = next(
        (block for block in response.content if block.type == "tool_use"), None
    )

    return ModelResponse(
        stop_reason=response.stop_reason,
        content=response.content,
        tool_use=tool_use,
        text_content=text_content,
    )


@track()
def call_model(
    user_messages: List[Dict[str, Any]],
) -> ModelResponse:
    """Make an API call to the model.

    Args:
        messages: List of message objects to send
    
    Returns:
        ModelResponse containing the processed response
    """
    MESSAGE_HISTORY.extend(user_messages)

    response = client.messages.create(
        system=system_prompt(model_name=MODEL_NAME) + "\n<instructions>" + finance_agent_prompt() + "</instructions>",
        model=MODEL_NAME,
        max_tokens=settings.max_tokens,
        tool_choice={"type": "auto"},
        tools=tool_prompt_construct_anthropic()["tools"],
        messages=MESSAGE_HISTORY,
    )

    return process_model_response(response)


@track()
def process_tool_call(tool_name: str, tool_input: Dict[str, Any]) -> Any:
    """Process a tool call and return the result.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool

    Returns:
        Result of the tool execution, or error message if execution fails
    """
    try:
        if tool_name == "search_engine":
            return search_duckduckgo(tool_input["query"], max_results=MAX_SEARCH_RESULTS)
        elif tool_name == "web_scraper":
            return scrape_urls(tool_input["urls"])
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Tool execution failed: {str(e)}"


@track(project_name="tony_stock")
def chat_with_claude(user_message: str) -> str:
    """Handle the chat flow with tool usage.

    Args:
        user_message: The user's input message to process

    Returns:
        Generated response from Claude, or error message if processing fails
    """
    # Initial call with system prompt
    response = call_model([{"role": "user", "content": user_message}])

    while response.stop_reason == "tool_use" and response.tool_use:
        tool_name = response.tool_use.name
        tool_input = response.tool_use.input

        # Execute tool
        tool_result = process_tool_call(tool_name, tool_input)

        # Continue conversation with verified result
        MESSAGE_HISTORY.append({"role": "assistant", "content": response.content})
        
        response = call_model([{
            "role": "user", 
            "content": [{
                "type": "tool_result",
                "tool_use_id": response.tool_use.id,
                "content": str(tool_result),
            }]
        }])

    return response.text_content or "No response generated"


if __name__ == "__main__":
    chat_with_claude("智原佈局如何")
