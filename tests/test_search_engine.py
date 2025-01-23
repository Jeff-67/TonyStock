"""Test module for search engine functionality."""

import pytest

from tools.search_engine import get_working_proxy, search_duckduckgo, validate_proxy


def test_search_basic():
    """Test basic search functionality."""
    query = "Python programming language"
    results = search_duckduckgo(query, max_results=3)

    assert isinstance(results, list)
    assert len(results) <= 3
    for result in results:
        assert isinstance(result, dict)
        assert all(key in result for key in ["title", "url", "snippet"])
        assert all(isinstance(result[key], str) for key in result)


def test_search_chinese():
    """Test search with Chinese query."""
    query = "台積電 半導體"
    results = search_duckduckgo(query, max_results=3)

    assert isinstance(results, list)
    assert len(results) <= 3
    for result in results:
        assert isinstance(result, dict)
        assert all(key in result for key in ["title", "url", "snippet"])


def test_search_empty_query():
    """Test search with empty query."""
    results = search_duckduckgo("", max_results=1)
    assert isinstance(results, list)
    assert len(results) <= 1


def test_search_special_characters():
    """Test search with special characters."""
    query = "C++ & Python @ programming!"
    results = search_duckduckgo(query, max_results=2)

    assert isinstance(results, list)
    assert len(results) <= 2
    for result in results:
        assert isinstance(result, dict)
        assert all(key in result for key in ["title", "url", "snippet"])


def test_proxy_functions():
    """Test proxy-related functions."""
    # Test get_working_proxy
    proxy = get_working_proxy()
    if proxy:
        assert isinstance(proxy, str)
        assert ":" in proxy  # Should be in format IP:PORT

        # Test validate_proxy with working proxy
        assert validate_proxy(proxy) is True
    else:
        # If no working proxy found, the search should still work
        results = search_duckduckgo("test", max_results=1)
        assert isinstance(results, list)


def test_max_results_limit():
    """Test max_results parameter behavior."""
    max_results = 5
    results = search_duckduckgo("test", max_results=max_results)
    assert len(results) <= max_results


if __name__ == "__main__":
    pytest.main([__file__])
