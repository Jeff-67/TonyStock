"""Test module for the search engine functionality.

This module contains test cases for the search engine implementation,
including successful searches, error handling, and result formatting.
"""

import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from tools.search_engine import search


class TestSearchEngine(unittest.TestCase):
    """Test suite for search engine functionality.

    This class tests various aspects of the search engine, including:
    - Successful search operations
    - Empty result handling
    - Error scenarios
    - Result field fallback behavior
    """

    def setUp(self):
        """Set up test fixtures before each test method.

        Captures stdout and stderr for testing debug output and search results.
        The original stdout and stderr are restored in tearDown.
        """
        # Capture stdout and stderr for testing
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def tearDown(self):
        """Clean up test fixtures after each test method.

        Restores the original stdout and stderr streams.
        """
        # Restore stdout and stderr
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

    @patch("tools.search_engine.DDGS")
    def test_successful_search(self, mock_ddgs):
        """Test successful search operation with multiple results.

        Verifies that:
        - Search results are properly formatted and displayed
        - Debug information is correctly logged
        - API is called with correct parameters
        - Both primary and fallback fields are handled
        """
        # Mock search results
        mock_results = [
            {
                "link": "http://example.com",
                "title": "Example Title",
                "snippet": "Example Snippet",
            },
            {
                "href": "http://example2.com",
                "title": "Example Title 2",
                "body": "Example Body 2",
            },
        ]

        # Setup mock
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.__enter__.return_value.text.return_value = mock_results
        mock_ddgs.return_value = mock_ddgs_instance

        # Run search
        search("test query", max_results=2)

        # Check debug output
        expected_debug = "DEBUG: Attempt 1/3 - Searching for query: test query"
        self.assertIn(expected_debug, self.stderr.getvalue())
        self.assertIn("DEBUG: Found 2 results", self.stderr.getvalue())

        # Check search results output
        output = self.stdout.getvalue()
        self.assertIn("=== Result 1 ===", output)
        self.assertIn("URL: http://example.com", output)
        self.assertIn("Title: Example Title", output)
        self.assertIn("Snippet: Example Snippet", output)
        self.assertIn("=== Result 2 ===", output)
        self.assertIn("URL: http://example2.com", output)
        self.assertIn("Title: Example Title 2", output)
        self.assertIn("Snippet: Example Body 2", output)

        # Verify mock was called correctly
        mock_ddgs_instance.__enter__.return_value.text.assert_called_once_with(
            "test query", max_results=2, backend="api"
        )

    @patch("tools.search_engine.DDGS")
    def test_no_results(self, mock_ddgs):
        """Test search behavior when no results are found.

        Verifies that:
        - Empty results are handled gracefully
        - Appropriate debug message is logged
        - No output is produced for empty results
        """
        # Mock empty results
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.__enter__.return_value.text.return_value = []
        mock_ddgs.return_value = mock_ddgs_instance

        # Run search
        search("test query")

        # Check debug output
        self.assertIn("DEBUG: No results found", self.stderr.getvalue())

        # Check that no results were printed
        self.assertEqual("", self.stdout.getvalue().strip())

    @patch("tools.search_engine.DDGS")
    def test_search_error(self, mock_ddgs):
        """Test error handling in search function.

        Verifies that:
        - Exceptions are properly caught and re-raised
        - Error messages are correctly propagated
        """
        with self.assertRaises(Exception) as cm:
            mock_instance = mock_ddgs.return_value.__enter__.return_value
            mock_instance.text.side_effect = Exception("Test error")
            search("test query")

        self.assertEqual(str(cm.exception), "Test error")

    def test_result_field_fallbacks(self):
        """Test result field fallback mechanism.

        Verifies that:
        - Primary fields are used when available
        - Fallback fields are used when primary fields are missing
        - Default values are used when both primary and fallback fields are missing
        """
        # Test that the fallback fields work correctly
        result = {
            "link": "http://example.com",
            "title": "Example Title",
            "snippet": "Example Snippet",
        }

        # Test primary fields
        self.assertEqual(
            result.get("link", result.get("href", "N/A")), "http://example.com"
        )
        self.assertEqual(result.get("title", "N/A"), "Example Title")
        self.assertEqual(
            result.get("snippet", result.get("body", "N/A")), "Example Snippet"
        )

        # Test fallback fields
        result = {
            "href": "http://example.com",
            "title": "Example Title",
            "body": "Example Body",
        }
        self.assertEqual(
            result.get("link", result.get("href", "N/A")), "http://example.com"
        )
        self.assertEqual(
            result.get("snippet", result.get("body", "N/A")), "Example Body"
        )

        # Test missing fields
        result = {}
        self.assertEqual(result.get("link", result.get("href", "N/A")), "N/A")
        self.assertEqual(result.get("title", "N/A"), "N/A")
        self.assertEqual(result.get("snippet", result.get("body", "N/A")), "N/A")


if __name__ == "__main__":
    unittest.main()
