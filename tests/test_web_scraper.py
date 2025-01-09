import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from tools.web_scraper import (
    validate_url,
    parse_html,
    fetch_page,
    process_urls
)

class TestWebScraper(unittest.TestCase):
    def test_validate_url(self):
        # Test valid URLs
        self.assertTrue(validate_url('https://example.com'))
        self.assertTrue(validate_url('http://example.com/path?query=1'))
        self.assertTrue(validate_url('https://sub.example.com:8080/path'))
        
        # Test invalid URLs
        self.assertFalse(validate_url('not-a-url'))
        self.assertFalse(validate_url('http://'))
        self.assertFalse(validate_url('https://'))
        self.assertFalse(validate_url(''))

    def test_parse_html(self):
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
        self.assertNotIn("var x = 1", result)  # Script content should be filtered
        self.assertNotIn(".css", result)  # Style content should be filtered
        
        # Test with nested elements
        html = """
        <html>
            <body>
                <div>
                    <p>Level 1</p>
                    <div>
                        <p>Level 2</p>
                    </div>
                </div>
            </body>
        </html>
        """
        result = parse_html(html)
        self.assertIn("Level 1", result)
        self.assertIn("Level 2", result)
        
        # Test with malformed HTML
        html = "<p>Unclosed paragraph"
        result = parse_html(html)
        self.assertIn("Unclosed paragraph", result)

    @patch('tools.web_scraper.logger')
    async def test_fetch_page(self, mock_logger):
        # Create mock context and page
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_page.close = AsyncMock()
        
        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        
        # Test successful fetch
        content = await fetch_page("https://example.com", mock_context)
        self.assertEqual(content, "<html><body>Test content</body></html>")
        mock_logger.info.assert_any_call("Fetching https://example.com")
        mock_logger.info.assert_any_call("Successfully fetched https://example.com")
        
        # Test fetch error
        mock_page.goto.side_effect = Exception("Network error")
        content = await fetch_page("https://example.com", mock_context)
        self.assertIsNone(content)
        mock_logger.error.assert_called_with("Error fetching https://example.com: Network error")

    @patch('tools.web_scraper.async_playwright')
    @patch('tools.web_scraper.Pool')
    async def test_process_urls(self, mock_pool, mock_playwright):
        # Mock playwright setup
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_page.close = AsyncMock()
        
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Mock Pool for parallel HTML parsing
        mock_pool_instance = MagicMock()
        mock_pool_instance.map.return_value = ["Parsed content 1", "Parsed content 2"]
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

def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

# Patch async tests
TestWebScraper.test_fetch_page = async_test(TestWebScraper.test_fetch_page)
TestWebScraper.test_process_urls = async_test(TestWebScraper.test_process_urls)

if __name__ == '__main__':
    unittest.main()
