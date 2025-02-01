"""Test module for online research agents functionality.

This module contains test cases for the online research agent that combines
search engine and web scraping functionality.
"""

import json
import logging
import os
from unittest.mock import AsyncMock, patch

import pytest

from agents.research_agents.online_research_agents import research_keyword

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test data
MOCK_SEARCH_RESULTS = [
    {
        "url": "https://test1.com",
        "title": "Test Article 1",
    },
    {
        "url": "https://test2.com",
        "title": "Test Article 2",
    },
]

MOCK_SCRAPE_RESULTS = [
    {"content": "Test content 1", "error": None},
    {"content": "Test content 2", "error": None},
]


@pytest.mark.asyncio
async def test_research_keyword_success():
    """Test successful research keyword execution."""
    with patch(
        "agents.research_agents.onlin_research_agents.search_duckduckgo",
        return_value=MOCK_SEARCH_RESULTS,
    ):
        with patch(
            "agents.research_agents.onlin_research_agents.scrape_urls",
            new_callable=AsyncMock,
            return_value=MOCK_SCRAPE_RESULTS,
        ):

            results = await research_keyword("test query")

            assert len(results) == 2
            assert results[0]["url"] == "https://test1.com"
            assert results[0]["title"] == "Test Article 1"
            assert results[0]["content"] == "Test content 1"
            assert results[0]["error"] is None


@pytest.mark.asyncio
async def test_research_keyword_no_results():
    """Test research keyword with no search results."""
    with patch(
        "agents.research_agents.onlin_research_agents.search_duckduckgo",
        return_value=[],
    ):
        results = await research_keyword("test query")
        assert len(results) == 0


@pytest.mark.asyncio
async def test_research_keyword_scraping_error():
    """Test research keyword with scraping errors."""
    mock_scrape_results = [{"content": "", "error": "Failed to scrape"}]

    with patch(
        "agents.research_agents.onlin_research_agents.search_duckduckgo",
        return_value=[MOCK_SEARCH_RESULTS[0]],
    ):
        with patch(
            "agents.research_agents.onlin_research_agents.scrape_urls",
            new_callable=AsyncMock,
            return_value=mock_scrape_results,
        ):

            results = await research_keyword("test query")

            assert len(results) == 1
            assert results[0]["error"] == "Failed to scrape"


@pytest.mark.asyncio
async def test_research_keyword_integration():
    """Integration test with real search and scraping."""
    test_query = "京鼎 3413 半導體設備 訂單 2025"
    results = await research_keyword(test_query, max_results=2)

    assert len(results) > 0
    for result in results:
        assert "url" in result
        assert "title" in result
        assert "content" in result

        # Save test results for manual inspection
        output_dir = "tests/test_outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "test_research_results.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"Integration test results saved to {output_file}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
