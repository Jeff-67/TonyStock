"""Utility functions for stock-related operations including name/ID mapping and message parsing."""

from typing import Any, Dict, List


def get_all_stock_mapping():
    """Get mapping of stock names to their IDs.

    Returns:
        dict: Mapping of stock names (str) to stock IDs (str)
    """
    return {
        "群聯": "8299",
        "京鼎": "3413",
        "文曄": "3036",
        "裕山": "7715",
        "台積電": "2330",
        "大成鋼": "2027",
        "聯發科": "2454",
    }


def stock_name_to_id(stock_name: str | None = None) -> str | None:
    """Convert stock name to its corresponding ID."""
    mapping = get_all_stock_mapping()
    return mapping.get(stock_name)


def stock_id_to_name(stock_id: str | None = None) -> str | None:
    """Convert stock ID to its corresponding name.

    Args:
        stock_id (str | None): The stock ID to convert. If None, returns None.

    Returns:
        str | None: The corresponding stock name if found, None otherwise.
    """
    if stock_id is None:
        return None

    mapping = get_all_stock_mapping()
    # Invert the mapping to get ID -> name
    inverted_mapping = {v: k for k, v in mapping.items()}
    return inverted_mapping.get(stock_id)


def retrieve_stock_name(user_messages: List[Dict[str, Any]]) -> str | None:
    """Retrieve the stock name from the user's messages."""
    last_message = user_messages[-1]["content"]
    for stock_name in get_all_stock_mapping().keys():
        if stock_name in last_message:
            return stock_name

    return None
