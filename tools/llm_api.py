"""Language Model (LLM) API interface module using LiteLLM.

This module provides a unified interface for interacting with various LLM providers
using LiteLLM. It handles query management and response processing with appropriate
error handling. Supports both sync and async operations.
"""

import argparse
import asyncio
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Tuple

import litellm
from dotenv import load_dotenv
from litellm import acompletion, completion
from litellm.integrations.opik.opik import OpikLogger
from opik import track
from opik.opik_context import get_current_span_data
from tools.tokencost import calculate_cost_by_tokens

from settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
        # For Anthropic models, add anthropic/ prefix
        if self.provider == Provider.ANTHROPIC:
            return f"anthropic/{self.model}"
        # For OpenAI models, add openai/ prefix
        if self.provider == Provider.OPENAI:
            return f"openai/{self.model}"
        # For other providers, prefix with provider name
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
        "messages": messages.copy(),
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
    elif config.provider == Provider.ANTHROPIC and json_mode:
        # Add system message for JSON output
        params["messages"].insert(0, {
            "role": "system",
            "content": "You must respond with valid JSON only, without any additional text or markdown formatting."
        })

    params["fallbacks"] = ["openai/gpt-4o"]

    return params


@track()
async def aquery_llm(
    messages: List[Message],
    tools: Optional[List[Dict]] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    json_mode: bool = False,
    response_format: Optional[Dict] = None,
) -> Tuple[Any, Dict[str, Any]]:
    """Send an asynchronous query to the LLM and get the response using LiteLLM.

    Args:
        messages: List of message dictionaries with role and content
        tools: List of tool dictionaries
        model: The specific model to use (defaults to "gpt-4o")
        provider: The provider to use (defaults to "openai")
        json_mode: Whether to request JSON output
        response_format: Custom response format configuration

    Returns:
        Tuple of (response object, dict with content and tool_calls)

    Raises:
        ValueError: If response validation fails
        Exception: For other errors during API call
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

        logger.info(f"Making LLM API call with model {config.model}")
        # Make the async API call
        response = await acompletion(**completion_params)
        
        if not response:
            logger.error("LLM API call returned None")
            raise ValueError("Empty response from LLM API")
            
        if not hasattr(response, 'choices') or not response.choices:
            logger.error("LLM response missing choices")
            raise ValueError("Invalid response format from LLM API")
            
        if not response.choices[0].message:
            logger.error("LLM response missing message")
            raise ValueError("No message in LLM response")

        # Update cost metrics
        update_cost_metrics(response)

        content = response.choices[0].message.content
        logger.info("Successfully received LLM response")

        # Process tool calls
        tool_calls = process_tool_calls(response.choices[0].message)

        return response, {"content": content, "tool_calls": tool_calls}

    except Exception as e:
        logger.error(f"Error in LLM API call: {str(e)}")
        raise


@track()
def query_llm(
    messages: List[Message],
    tools: Optional[List[Dict]] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    json_mode: bool = False,
    response_format: Optional[Dict] = None,
) -> Tuple[Any, Dict[str, Any]]:
    """Send a synchronous query to the LLM and get the response using LiteLLM.

    Args:
        messages: List of message dictionaries with role and content
        tools: List of tool dictionaries
        model: The specific model to use (defaults to "gpt-4o")
        provider: The provider to use (defaults to "openai")
        json_mode: Whether to request JSON output
        response_format: Custom response format configuration

    Returns:
        Tuple of (response object, dict with content and tool_calls)

    Raises:
        ValueError: If response validation fails
        Exception: For other errors during API call
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

        logger.info(f"Making LLM API call with model {config.model}")
        # Make the API call
        response = completion(**completion_params)
        
        if not response:
            logger.error("LLM API call returned None")
            raise ValueError("Empty response from LLM API")
            
        if not hasattr(response, 'choices') or not response.choices:
            logger.error("LLM response missing choices")
            raise ValueError("Invalid response format from LLM API")
            
        if not response.choices[0].message:
            logger.error("LLM response missing message")
            raise ValueError("No message in LLM response")

        # Update cost metrics
        update_cost_metrics(response)

        content = response.choices[0].message.content
        logger.info("Successfully received LLM response")

        # Process tool calls
        tool_calls = process_tool_calls(response.choices[0].message)

        return response, {"content": content, "tool_calls": tool_calls}

    except Exception as e:
        logger.error(f"Error in LLM API call: {str(e)}")
        raise


async def async_main(
    messages: List[Message], model: str = "gpt-4o", provider: str = "openai"
) -> None:
    """Async main function for testing."""
    response, _ = await aquery_llm(messages=messages, model=model, provider=provider)
    print(response.choices[0].message.content)


def main():
    """Main function for testing."""
    parser = argparse.ArgumentParser(description="Test LLM API")
    parser.add_argument("--model", default="gpt-4o", help="Model name")
    parser.add_argument("--provider", default="openai", help="Provider name")
    args = parser.parse_args()

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! How are you?"},
    ]

    if sys.platform == "win32":
        # Windows specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(async_main(messages, args.model, args.provider))


def process_tool_calls(message: Any) -> List[Dict]:
    """Process tool calls from the message.

    Args:
        message: Message object from LLM response

    Returns:
        List of tool call dictionaries
    """
    tool_calls = []
    if hasattr(message, "tool_calls") and message.tool_calls:
        for tool_call in message.tool_calls:
            if tool_call.type == "function":
                tool_calls.append({
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                })
    return tool_calls


def update_cost_metrics(response: Any) -> None:
    """Update cost metrics based on token usage.
    
    Args:
        response: Response object from LLM API
    """
    try:
        if not hasattr(response, 'usage'):
            return
            
        usage = response.usage
        if not usage:
            return
            
        # Get token counts
        input_tokens = getattr(usage, 'prompt_tokens', 0)
        output_tokens = getattr(usage, 'completion_tokens', 0)
        
        # Calculate cost
        model = response.model.split('/')[-1]  # Remove provider prefix
        cost = calculate_cost_by_tokens(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Log cost information
        logger.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}")
        logger.info(f"Estimated cost: ${cost:.4f}")
        
    except Exception as e:
        logger.warning(f"Error updating cost metrics: {str(e)}")


if __name__ == "__main__":
    main()
