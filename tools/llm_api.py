"""Language Model (LLM) API interface module using LiteLLM.

This module provides a unified interface for interacting with various LLM providers
using LiteLLM. It handles query management and response processing with appropriate
error handling. Supports both sync and async operations.
"""

import argparse
import asyncio

import litellm
from dotenv import load_dotenv
from litellm import acompletion, completion
from litellm.integrations.opik.opik import OpikLogger
from opik import track
from opik.opik_context import get_current_span_data

from settings import Settings

Settings()
opik_logger = OpikLogger()
litellm.callbacks = [opik_logger]

# Load .env.local file
load_dotenv()


@track()
def query_llm(messages, model=None, provider=None, json_mode=False):
    """Send a synchronous query to the LLM and get the response using LiteLLM.

    Args:
        messages (list): List of message dictionaries with role and content.
        model (str, optional): The specific model to use. Defaults to "openai/gpt-4o".
            Supported formats:
            - OpenAI: "openai/gpt-4o"
            - Anthropic: "anthropic/claude-3-sonnet-20240229"
            - Local: "ollama/Qwen2.5-32B-Instruct-AWQ"
        json_mode (bool, optional): Whether to request JSON output (OpenAI only). Defaults to False.

    Returns:
        Optional[str]: The model's response text, or None if the query fails.
    """
    try:
        # Ensure model has a value
        if model is None:
            model = "openai/gpt-4o"

        # Configure completion parameters
        completion_params = {
            "model": provider + "/" + model,
            "messages": messages,
        }

        # Add JSON mode for OpenAI if requested
        if json_mode and model.startswith("openai/"):
            completion_params["response_format"] = {"type": "json_object"}

        # Add API base for local models
        if model.startswith("ollama/"):
            completion_params["api_base"] = "http://192.168.180.137:8006"

        # Make the API call
        response = completion(
            **completion_params,
            metadata={
                "opik": {
                    "current_span_data": get_current_span_data(),
                    "tags": ["streaming-test"],
                },
            },
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None


@track()
async def aquery_llm(messages, model=None, provider=None, json_mode=False):
    """Send an asynchronous query to the LLM and get the response using LiteLLM.

    Args:
        messages (list): List of message dictionaries with role and content.
        model (str, optional): The specific model to use. Defaults to "openai/gpt-4o".
            Supported formats:
            - OpenAI: "openai/gpt-4o"
            - Anthropic: "anthropic/claude-3-sonnet-20240229"
            - Local: "ollama/Qwen2.5-32B-Instruct-AWQ"
        json_mode (bool, optional): Whether to request JSON output (OpenAI only). Defaults to False.

    Returns:
        Optional[str]: The model's response text, or None if the query fails.
    """
    try:
        # Ensure model has a value
        if model is None:
            model = "openai/gpt-4o"

        # Configure completion parameters
        completion_params = {
            "model": provider + "/" + model,
            "messages": messages,
        }

        # Add JSON mode for OpenAI if requested
        if json_mode and model.startswith("openai/"):
            completion_params["response_format"] = {"type": "json_object"}

        # Add API base for local models
        if model.startswith("ollama/"):
            completion_params["api_base"] = "http://192.168.180.137:8006"

        # Make the async API call
        response = await acompletion(
            **completion_params,
            metadata={
                "opik": {
                    "current_span_data": get_current_span_data(),
                    "tags": ["streaming-test"],
                },
            },
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None


async def async_main(messages, model="openai/gpt-4o"):
    """Async entry point for command line usage."""
    response = await aquery_llm(messages, model=model)
    if response:
        print(response)
    else:
        print("Failed to get response from LLM")


def main():
    """Command-line interface for querying LLMs.

    Provides a command-line interface for sending prompts to various LLM providers
    with configurable models. Handles argument parsing and displays the results
    or error messages.
    """
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

    if args.use_async:
        messages = [{"role": "user", "content": args.prompt}]
        asyncio.run(async_main(messages, model=args.model))
    else:
        messages = [{"role": "user", "content": args.prompt}]
        response = query_llm(messages, model=args.model)
        if response:
            print(response)
        else:
            print("Failed to get response from LLM")


if __name__ == "__main__":
    main()
