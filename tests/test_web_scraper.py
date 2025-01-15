"""Test module for the web scraper functionality.

This module contains test cases for the web scraper implementation,
including URL validation, HTML parsing, page fetching, and concurrent URL processing.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tools.web_scraper import fetch_page, parse_html, process_urls, validate_url


def async_test(coro):
    """Execute an async test coroutine in an event loop.

    Args:
        coro: The coroutine (async function) to be wrapped.

    Returns:
        function: A wrapper function that runs the coroutine in an event loop.
    """

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))

    return wrapper


class TestWebScraper(unittest.TestCase):
    """Test suite for web scraper functionality."""

    def test_validate_url(self):
        """Test URL validation functionality."""
        # Test valid URLs
        self.assertTrue(validate_url("https://example.com"))
        self.assertTrue(validate_url("http://example.com/path?query=1"))
        self.assertTrue(validate_url("https://sub.example.com:8080/path"))

        # Test invalid URLs
        self.assertFalse(validate_url("not-a-url"))
        self.assertFalse(validate_url("http://"))
        self.assertFalse(validate_url("https://"))
        self.assertFalse(validate_url(""))

    def test_parse_html(self):
        """Test HTML parsing and cleaning functionality."""
        # Test with empty or None input
        self.assertEqual(parse_html(None), "")
        self.assertEqual(parse_html(""), "")

        # Test with simple HTML
        html = """
        <html>
            <body>
                <h1>Title</h1>
                <p>Paragraph text</p>
                <a href="https://example.com">Link text</a>
                <script>var x = 1;</script>
                <style>.css { color: red; }</style>
            </body>
        </html>
        """
        result = parse_html(html)
        self.assertIn("Title", result)
        self.assertIn("Paragraph text", result)
        self.assertIn("[Link text](https://example.com)", result)
        self.assertNotIn("var x = 1", result)
        self.assertNotIn(".css", result)

    @async_test
    async def test_fetch_page(self):
        """Test asynchronous page fetching functionality."""
        # Create mock context and page
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(
            return_value="<html><body>Test content</body></html>"
        )
        mock_page.close = AsyncMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        # Test successful fetch
        content = await fetch_page("https://example.com", mock_context)
        self.assertEqual(content, "<html><body>Test content</body></html>")

        # Test fetch error
        mock_page.goto.side_effect = Exception("Network error")
        content = await fetch_page("https://example.com", mock_context)
        self.assertIsNone(content)

    @async_test
    async def test_process_urls(self):
        """Test concurrent URL processing functionality."""
        # Mock playwright setup
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(
            return_value="<html><body>Test content</body></html>"
        )
        mock_page.close = AsyncMock()

        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("tools.web_scraper.async_playwright") as mock_playwright:
            mock_playwright.return_value.__aenter__.return_value = (
                mock_playwright_instance
            )

            # Mock Pool for parallel HTML parsing
            mock_pool_instance = MagicMock()
            mock_pool_instance.map.return_value = [
                "Parsed content 1",
                "Parsed content 2",
            ]

            with patch("tools.web_scraper.Pool") as mock_pool:
                mock_pool.return_value.__enter__.return_value = mock_pool_instance

                # Test processing multiple URLs
                urls = ["https://example1.com", "https://example2.com"]
                results = await process_urls(urls, max_concurrent=2)

                # Verify results
                self.assertEqual(len(results), 2)
                self.assertEqual(results[0], "Parsed content 1")
                self.assertEqual(results[1], "Parsed content 2")

                # Verify mocks were called correctly
                self.assertEqual(mock_browser.new_context.call_count, 2)
                mock_pool_instance.map.assert_called_once()
                mock_browser.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
