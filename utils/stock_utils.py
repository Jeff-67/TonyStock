"""Utility functions for stock-related operations including name/ID mapping and message parsing."""

from typing import Any, Dict, List


def get_all_stock_mapping():
    """Get mapping of stock names to their IDs.

    Returns:
        dict: Mapping of stock names (str) to stock IDs (str)
    """
    return {"群聯": "8299", "京鼎": "3413", "文曄": "3036", "裕山": "7715"}


def stock_name_to_id(stock_name: str | None = None) -> str | None:
    """Convert stock name to its corresponding ID."""
    mapping = get_all_stock_mapping()
    return mapping.get(stock_name)


def retrieve_stock_name(user_messages: List[Dict[str, Any]]) -> str | None:
    """Retrieve the stock name from the user's messages."""
    last_message = user_messages[-1]["content"]
    for stock_name in get_all_stock_mapping().keys():
        if stock_name in last_message:
            return stock_name

    return None
