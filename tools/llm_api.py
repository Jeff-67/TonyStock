"""Language Model (LLM) API interface module using LiteLLM.

This module provides a unified interface for interacting with various LLM providers
using LiteLLM. It handles query management and response processing with appropriate
error handling. Supports both sync and async operations.
"""

import argparse
import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

import litellm
from dotenv import load_dotenv
from litellm import acompletion, completion
from litellm.integrations.opik.opik import OpikLogger
from opik import opik_context, track
from opik.opik_context import get_current_span_data
from tokencost import calculate_cost_by_tokens

from settings import Settings

Settings()
load_dotenv()

opik_logger = OpikLogger()
litellm.callbacks = [opik_logger]


class Provider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class Message(TypedDict):
    """Type definition for a message."""

    role: str
    content: str


@dataclass
class LLMConfig:
    """Configuration for LLM API calls."""

    provider: Provider
    model: str
    api_base: Optional[str] = None
    response_format: Optional[Dict] = None

    def __post_init__(self):
        """Validate and process the configuration after initialization."""
        if not self.model:
            self.model = "gpt-4o"
        if not self.provider:
            self.provider = Provider.OPENAI

        # Set API base for local models
        if self.provider == Provider.OLLAMA and not self.api_base:
            self.api_base = "http://192.168.180.137:8006"

    @property
    def full_model_name(self) -> str:
        """Get the full model name with provider prefix."""
        return f"{self.provider}/{self.model}"


def create_completion_params(
    config: LLMConfig,
    messages: List[Message],
    tools: Optional[List[Dict]] = None,
    json_mode: bool = False,
    response_format: Optional[Dict] = None,
) -> Dict:
    """Create parameters for LLM API completion.

    Args:
        config: LLM configuration
        messages: List of message dictionaries
        tools: List of tool dictionaries
        json_mode: Whether to request JSON output
        response_format: Custom response format configuration

    Returns:
        Dictionary of completion parameters
    """
    params = {
        "model": config.full_model_name,
        "messages": messages,
        "metadata": {
            "opik": {
                "current_span_data": get_current_span_data(),
                "tags": ["llm-api"],
            },
        },
    }

    if tools:
        params["tools"] = tools
        params["tool_choice"] = "auto"

    # Add API base if specified
    if config.api_base:
        params["api_base"] = config.api_base

    # Handle response format configuration
    if config.provider == Provider.OPENAI:
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        elif response_format:
            params["response_format"] = response_format

    return params


@track()
def query_llm(
    messages: List[Message],
    tools: Optional[List[Dict]] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    json_mode: bool = False,
    response_format: Optional[Dict] = None,
) -> Any:
    """Send a synchronous query to the LLM and get the response using LiteLLM.

    Args:
        messages: List of message dictionaries with role and content
        model: The specific model to use (defaults to "gpt-4o")
        provider: The provider to use (defaults to "openai")
        json_mode: Whether to request JSON output (OpenAI only)
        response_format: Custom response format configuration

    Returns:
        The model's response text, or None if the query fails
    """
    try:
        # Create and validate configuration
        config = LLMConfig(
            provider=Provider(provider) if provider else Provider.OPENAI,
            model=model or "gpt-4o",
            response_format=response_format,
        )

        # Get completion parameters
        completion_params = create_completion_params(
            config=config,
            messages=messages,
            tools=tools,
            json_mode=json_mode,
            response_format=response_format,
        )

        # Make the API call
        response = completion(**completion_params)
        opik_context.update_current_span(
            total_cost=calculate_cost_by_tokens(
                response.usage.prompt_tokens, model=response.model, token_type="input"
            )
            + calculate_cost_by_tokens(
                response.usage.completion_tokens,
                model=response.model,
                token_type="output",
            )
        )

        content = response.choices[0].message.content

        # Handle tool calls serialization
        tool_calls = []
        if (
            hasattr(response.choices[0].message, "tool_calls")
            and response.choices[0].message.tool_calls
        ):
            for tool_call in response.choices[0].message.tool_calls:
                try:
                    tool_calls.append(
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": json.loads(tool_call.function.arguments),
                            },
                        }
                    )
                except Exception as e:
                    print(f"Error parsing tool call arguments: {e}")
                    tool_calls.append(
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    )

        return response, {"content": content, "tool_calls": tool_calls}

    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None


@track()
async def aquery_llm(
    messages: List[Message],
    model: Optional[str] = None,
    provider: Optional[str] = None,
    json_mode: bool = False,
    response_format: Optional[Dict] = None,
) -> Optional[str]:
    """Send an asynchronous query to the LLM and get the response using LiteLLM.

    Args:
        messages: List of message dictionaries with role and content
        model: The specific model to use (defaults to "gpt-4o")
        provider: The provider to use (defaults to "openai")
        json_mode: Whether to request JSON output (OpenAI only)
        response_format: Custom response format configuration

    Returns:
        The model's response text, or None if the query fails
    """
    try:
        # Create and validate configuration
        config = LLMConfig(
            provider=Provider(provider) if provider else Provider.OPENAI,
            model=model or "gpt-4o",
            response_format=response_format,
        )

        # Get completion parameters
        completion_params = create_completion_params(
            config=config,
            messages=messages,
            json_mode=json_mode,
            response_format=response_format,
        )

        # Make the async API call
        response = await acompletion(**completion_params)

        # Handle response based on format
        if (
            response_format
            and config.provider == Provider.OPENAI
            and hasattr(response.choices[0].message, "parsed")
        ):
            return response.choices[0].message.parsed.filtered_content

        return response.choices[0].message

    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None


async def async_main(
    messages: List[Message], model: str = "gpt-4o", provider: str = "openai"
) -> None:
    """Async entry point for command line usage."""
    response = await aquery_llm(messages, model=model, provider=provider)
    if response:
        print(response)
    else:
        print("Failed to get response from LLM")


def main():
    """Command-line interface for querying LLMs."""
    parser = argparse.ArgumentParser(description="Query an LLM with a prompt")
    parser.add_argument(
        "--prompt", type=str, help="The prompt to send to the LLM", required=True
    )
    parser.add_argument(
        "--model",
        type=str,
        help="The model to use (e.g., openai/gpt-4o, anthropic/claude-3-sonnet-20240229)",
    )
    parser.add_argument(
        "--async",
        action="store_true",
        help="Use async version of the API",
        dest="use_async",
    )
    args = parser.parse_args()

    messages = [{"role": "user", "content": args.prompt}]

    if args.use_async:
        asyncio.run(async_main(messages, model=args.model))
    else:
        response, _ = query_llm(messages, model=args.model)
        if response:
            print(response)
        else:
            print("Failed to get response from LLM")


if __name__ == "__main__":
    main()
