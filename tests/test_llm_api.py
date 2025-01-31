"""Test module for LLM API functionality using LiteLLM.

This module contains test cases for the Language Model (LLM) API interface,
including synchronous and asynchronous query handling, and error cases for
multiple providers (OpenAI, Anthropic). It supports skipping tests when
LLM is not configured and provides mock objects for testing without actual API calls.
"""

import asyncio
import os
import unittest
from unittest.mock import MagicMock, patch

from tools.llm_api import aquery_llm, query_llm


def is_llm_configured():
    """Check if LLM is configured by checking environment variables."""
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


# Skip all LLM tests if LLM is not configured
skip_llm_tests = not is_llm_configured()
skip_message = "Skipping LLM tests as no API keys are configured."


class TestLLMAPI(unittest.TestCase):
    """Test suite for LLM API functionality.

    This class tests both synchronous and asynchronous query functionality
    for multiple providers, including various configurations and error cases.
    """

    def setUp(self):
        """Set up test fixtures before each test method.

        Creates mock response structure to simulate LiteLLM responses
        without actual API calls.
        """
        # Create mock response structure
        self.mock_response = MagicMock()
        self.mock_choice = MagicMock()
        self.mock_message = MagicMock()

        # Set up the mock response structure
        self.mock_message.content = "Test response"
        self.mock_choice.message = self.mock_message
        self.mock_response.choices = [self.mock_choice]

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.completion")
    def test_query_llm_openai_success(self, mock_completion):
        """Test successful synchronous OpenAI query."""
        mock_completion.return_value = self.mock_response
        messages = [{"role": "user", "content": "Test prompt"}]

        response = query_llm(messages, model="openai/gpt-4o")

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify completion was called correctly
        mock_completion.assert_called_once_with(
            model="openai/gpt-4o", messages=messages
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.completion")
    def test_query_llm_anthropic_success(self, mock_completion):
        """Test successful synchronous Anthropic query."""
        mock_completion.return_value = self.mock_response
        messages = [{"role": "user", "content": "Test prompt"}]

        response = query_llm(messages, model="anthropic/claude-3-sonnet-20240229")

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify completion was called correctly
        mock_completion.assert_called_once_with(
            model="anthropic/claude-3-sonnet-20240229", messages=messages
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.completion")
    def test_query_llm_json_mode(self, mock_completion):
        """Test query with JSON mode enabled."""
        mock_completion.return_value = self.mock_response
        messages = [{"role": "user", "content": "Test prompt"}]

        response = query_llm(messages, model="openai/gpt-4o", json_mode=True)

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify completion was called with JSON mode
        mock_completion.assert_called_once_with(
            model="openai/gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.completion")
    def test_query_llm_error(self, mock_completion):
        """Test error handling in synchronous query."""
        mock_completion.side_effect = Exception("Test error")
        messages = [{"role": "user", "content": "Test prompt"}]

        response = query_llm(messages)
        self.assertIsNone(response)

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.acompletion")
    def test_aquery_llm_openai_success(self, mock_acompletion):
        """Test successful asynchronous OpenAI query."""
        mock_acompletion.return_value = self.mock_response
        messages = [{"role": "user", "content": "Test prompt"}]

        async def run_test():
            return await aquery_llm(messages, model="openai/gpt-4o")

        response = asyncio.run(run_test())

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify acompletion was called correctly
        mock_acompletion.assert_called_once_with(
            model="openai/gpt-4o", messages=messages
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.acompletion")
    def test_aquery_llm_anthropic_success(self, mock_acompletion):
        """Test successful asynchronous Anthropic query."""
        mock_acompletion.return_value = self.mock_response
        messages = [{"role": "user", "content": "Test prompt"}]

        async def run_test():
            return await aquery_llm(
                messages, model="anthropic/claude-3-sonnet-20240229"
            )

        response = asyncio.run(run_test())

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify acompletion was called correctly
        mock_acompletion.assert_called_once_with(
            model="anthropic/claude-3-sonnet-20240229", messages=messages
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.acompletion")
    def test_aquery_llm_error(self, mock_acompletion):
        """Test error handling in asynchronous query."""
        mock_acompletion.side_effect = Exception("Test error")
        messages = [{"role": "user", "content": "Test prompt"}]

        async def run_test():
            return await aquery_llm(messages)

        response = asyncio.run(run_test())
        self.assertIsNone(response)


if __name__ == "__main__":
    unittest.main()
