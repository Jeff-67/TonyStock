"""Language Model (LLM) API interface module.

This module provides a unified interface for interacting with various LLM providers,
including OpenAI, Anthropic, and local models. It handles client creation,
query management, and response processing with appropriate error handling.
"""

import argparse
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI

# Load .env.local file
env_path = Path(".") / ".env.local"
load_dotenv(dotenv_path=env_path)


def create_llm_client(provider="openai"):
    """Create a client instance for the specified LLM provider.

    Args:
        provider (str, optional): The LLM provider to use. Defaults to "openai".
            Supported providers: "openai", "anthropic", "local".

    Returns:
        Union[OpenAI, Anthropic]: A client instance for the specified provider.

    Raises:
        ValueError: If the provider is not supported or if required API keys
            are not found in environment variables.
    """
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return OpenAI(api_key=api_key)
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        return Anthropic(api_key=api_key)
    elif provider == "local":
        return OpenAI(
            base_url="http://192.168.180.137:8006/v1",
            api_key="not-needed",
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def query_llm(prompt, client=None, model=None, provider="openai"):
    """Send a query to the LLM and get the response.

    Args:
        prompt (str): The prompt to send to the LLM.
        client (Union[OpenAI, Anthropic], optional): Pre-configured client instance.
            If None, a new client will be created. Defaults to None.
        model (str, optional): The specific model to use. If None, defaults to:
            - OpenAI: "gpt-4o"
            - Anthropic: "claude-3-sonnet-20240229"
            - Local: "Qwen/Qwen2.5-32B-Instruct-AWQ"
        provider (str, optional): The LLM provider to use. Defaults to "openai".

    Returns:
        Optional[str]: The model's response text, or None if the query fails.
    """
    if client is None:
        client = create_llm_client(provider)
    try:
        # Set default model
        if model is None:
            if provider == "openai":
                model = "gpt-4o"
            elif provider == "anthropic":
                model = "claude-3-sonnet-20240229"
            elif provider == "local":
                model = "Qwen/Qwen2.5-32B-Instruct-AWQ"

        if provider == "openai" or provider == "local":
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        elif provider == "anthropic":
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None


def main():
    """Command-line interface for querying LLMs.

    Provides a command-line interface for sending prompts to various LLM providers
    with configurable models and providers. Handles argument parsing and
    displays the results or error messages.
    """
    parser = argparse.ArgumentParser(description="Query an LLM with a prompt")
    parser.add_argument(
        "--prompt", type=str, help="The prompt to send to the LLM", required=True
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic"],
        default="openai",
        help="The API provider to use",
    )
    parser.add_argument(
        "--model", type=str, help="The model to use (default depends on provider)"
    )
    args = parser.parse_args()

    # Set default model
    if not args.model:
        if args.provider == "openai":
            args.model = "gpt-4o"
        else:
            args.model = "claude-3-5-sonnet-20241022"

    client = create_llm_client(args.provider)
    response = query_llm(args.prompt, client, model=args.model, provider=args.provider)
    if response:
        print(response)
    else:
        print("Failed to get response from LLM")


if __name__ == "__main__":
    main()
