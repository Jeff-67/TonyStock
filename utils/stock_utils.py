"""Utility functions for stock-related operations including name/ID mapping and message parsing."""

from typing import Any, Dict, List

from database.utils import db_manager


def get_all_stock_mapping() -> Dict[str, str]:
    """Get mapping of stock names to their IDs.

    Returns:
        dict: Mapping of stock names (str) to stock IDs (str)
    """
    query = "SELECT company_name, ticker FROM TSE_STOCKS"
    results = db_manager.get_data(
        db_type="mysql", key="ticker", query=query, collection_or_table="TSE_STOCKS"
    )

    if not results:
        return {}

    # Convert the list of dicts to the required format
    return {record["company_name"]: record["ticker"] for record in results}


def stock_name_to_id(stock_name: str | None = None) -> str | None:
    """Convert stock name to its corresponding ID."""
    if stock_name is None:
        return None

    query = f"SELECT ticker FROM TSE_STOCKS WHERE company_name = '{stock_name}'"
    result = db_manager.get_data(
        db_type="mysql", key="ticker", query=query, collection_or_table="TSE_STOCKS"
    )

    if result and isinstance(result, list) and len(result) > 0:
        return result[0]["ticker"]
    return None


def stock_id_to_name(stock_id: str | None = None) -> str | None:
    """Convert stock ID to its corresponding name.

    Args:
        stock_id (str | None): The stock ID to convert. If None, returns None.

    Returns:
        str | None: The corresponding stock name if found, None otherwise.
    """
    if stock_id is None:
        return None

    query = f"SELECT company_name FROM TSE_STOCKS WHERE ticker = '{stock_id}'"
    result = db_manager.get_data(
        db_type="mysql", key="ticker", query=query, collection_or_table="TSE_STOCKS"
    )

    if result and isinstance(result, list) and len(result) > 0:
        return result[0]["company_name"]
    return None


def retrieve_stock_name(user_messages: List[Dict[str, Any]]) -> str | None:
    """Retrieve the stock name from the user's messages."""
    last_message = user_messages[-1]["content"]

    # Get all stock names from database
    query = "SELECT company_name FROM TSE_STOCKS"
    results = db_manager.get_data(
        db_type="mysql",
        key="company_name",
        query=query,
        collection_or_table="TSE_STOCKS",
    )

    if not results:
        return None

    # Check if any stock name appears in the message
    for record in results:
        stock_name = record["company_name"]
        if stock_name in last_message:
            return stock_name

    return None
