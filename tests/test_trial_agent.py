"""Tests for the trial agent module."""

import pytest

from agents.trial_agent import process_tool_call


@pytest.mark.asyncio
async def test_search_engine():
    """Test search_engine tool call."""
    result = await process_tool_call("search_engine", {"query": "宏達電 AI眼鏡 鉅亨"})
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, dict) for item in result)
    assert all(
        "title" in item and "url" in item and "snippet" in item for item in result
    )


@pytest.mark.asyncio
async def test_web_scraper():
    """Test web_scraper tool call."""
    result = await process_tool_call(
        "web_scraper", {"urls": ["https://news.cnyes.com/news/id/5844128"]}
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert all(key in result[0] for key in ["title", "date", "content", "url"])


@pytest.mark.asyncio
async def test_unknown_tool():
    """Test handling of unknown tool."""
    result = await process_tool_call("unknown_tool", {"param": "test"})
    assert isinstance(result, str)
    assert "Unknown tool" in result
