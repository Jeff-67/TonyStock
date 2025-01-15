"""Test module for LLM API functionality.

This module contains test cases for the Language Model (LLM) API interface,
including client creation, query handling, and error cases. It supports
skipping tests when LLM is not configured and provides mock objects for
testing without actual API calls.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from tools.llm_api import create_llm_client, query_llm


def is_llm_configured():
    """Check if LLM is configured by trying to connect to the server."""
    try:
        client = create_llm_client()
        response = query_llm("test", client)
        return response is not None
    except Exception:
        return False


# Skip all LLM tests if LLM is not configured
skip_llm_tests = not is_llm_configured()
skip_message = "Skipping LLM tests as LLM is not configured. This is normal if you haven't set up a local LLM server."


class TestLLMAPI(unittest.TestCase):
    """Test suite for LLM API functionality.

    This class tests the creation of LLM clients and query functionality,
    including various configurations and error cases.
    """

    def setUp(self):
        """Set up test fixtures before each test method.

        Creates mock objects for OpenAI client, response, choice, and message
        to simulate LLM API interactions without actual API calls.
        """
        # Create a mock OpenAI client
        self.mock_client = MagicMock()
        self.mock_response = MagicMock()
        self.mock_choice = MagicMock()
        self.mock_message = MagicMock()

        # Set up the mock response structure
        self.mock_message.content = "Test response"
        self.mock_choice.message = self.mock_message
        self.mock_response.choices = [self.mock_choice]

        # Set up the mock client's chat.completions.create method
        self.mock_client.chat.completions.create.return_value = self.mock_response

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.OpenAI")
    def test_create_llm_client(self, mock_openai):
        """Test LLM client creation with default provider.

        Verifies that the client is created with correct API key and
        returns the expected client object.
        """
        mock_openai.return_value = self.mock_client
        client = create_llm_client()

        # Verify OpenAI was called with correct parameters
        mock_openai.assert_called_once_with(api_key=os.getenv("OPENAI_API_KEY"))

        self.assertEqual(client, self.mock_client)

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.create_llm_client")
    def test_query_llm_success(self, mock_create_client):
        """Test successful LLM query with default settings.

        Verifies that the query is made with correct parameters and
        returns the expected response.
        """
        mock_create_client.return_value = self.mock_client

        response = query_llm("Test prompt")

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify client was called correctly
        self.mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.create_llm_client")
    def test_query_llm_with_custom_model(self, mock_create_client):
        """Test LLM query with a custom model.

        Verifies that the query uses the specified custom model and
        returns the expected response.
        """
        mock_create_client.return_value = self.mock_client

        response = query_llm("Test prompt", model="custom-model")

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify client was called with custom model
        self.mock_client.chat.completions.create.assert_called_once_with(
            model="custom-model",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.create_llm_client")
    def test_query_llm_with_existing_client(self, mock_create_client):
        """Test LLM query with a pre-existing client.

        Verifies that the query uses the provided client without creating
        a new one and returns the expected response.
        """
        response = query_llm("Test prompt", client=self.mock_client)

        # Verify response
        self.assertEqual(response, "Test response")

        # Verify create_client was not called
        mock_create_client.assert_not_called()

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch("tools.llm_api.create_llm_client")
    def test_query_llm_error(self, mock_create_client):
        """Test LLM query error handling.

        Verifies that the query handles errors gracefully by returning None
        when an exception occurs.
        """
        # Set up mock to raise an exception
        self.mock_client.chat.completions.create.side_effect = Exception("Test error")
        mock_create_client.return_value = self.mock_client

        # Test query with error
        response = query_llm("Test prompt")

        # Verify error handling
        self.assertIsNone(response)


if __name__ == "__main__":
    unittest.main()
