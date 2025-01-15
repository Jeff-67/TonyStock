"""Utility functions for financial data processing.

This module provides utility functions for processing, validating, and formatting
financial data, including market data and financial statements.
"""

import json
from datetime import datetime
from typing import Dict, Optional

import numpy as np
import pandas as pd
import pytz

from tools.financial_data import config


class PandasJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for pandas and numpy data types.

    This encoder handles pandas DataFrames, Series, and numpy data types
    for JSON serialization.
    """

    def default(self, obj):
        """Convert pandas and numpy objects to JSON-serializable types.

        Args:
            obj: Object to encode.

        Returns:
            JSON-serializable version of the object.
        """
        if isinstance(obj, pd.DataFrame):
            return obj.replace({np.nan: None}).to_dict(orient="records")
        elif isinstance(obj, pd.Series):
            return obj.replace({np.nan: None}).to_dict()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def prepare_json_data(data: dict) -> dict:
    """Prepare data for JSON serialization.

    Args:
        data (dict): Data to prepare for JSON serialization.

    Returns:
        dict: JSON-serializable data.
    """
    if not data:
        return {}

    return json.loads(json.dumps(data, cls=PandasJSONEncoder))


def combine_market_data(data: dict) -> Optional[pd.DataFrame]:
    """Combine market data from multiple symbols into a single DataFrame.

    Args:
        data (dict): Dictionary mapping symbols to market data DataFrames.

    Returns:
        Optional[pd.DataFrame]: Combined DataFrame with all symbols' data,
            or None if no valid data is provided.
    """
    if not data:
        return None

    dfs = []
    for symbol, df in data.items():
        if isinstance(df, pd.DataFrame):
            df["Symbol"] = symbol
            dfs.append(df)

    if not dfs:
        return None

    return pd.concat(dfs, axis=0, ignore_index=True)


def combine_financial_statements(
    data: Dict[str, Dict[str, pd.DataFrame]]
) -> Optional[pd.DataFrame]:
    """Combine financial statements from multiple symbols into a single DataFrame.

    Args:
        data (Dict[str, Dict[str, pd.DataFrame]]): Dictionary mapping symbols
            to statement dictionaries.

    Returns:
        Optional[pd.DataFrame]: Combined DataFrame with symbol and statement_type
            columns, or None if no valid data is provided.
    """
    combined_data = []
    for symbol, statements in data.items():
        if statements:
            for stmt_type, df in statements.items():
                df = df.copy()
                df["symbol"] = symbol
                df["statement_type"] = stmt_type
                combined_data.append(df)

    if combined_data:
        return pd.concat(combined_data, ignore_index=True)
    return None


def validate_symbol(symbol: str) -> bool:
    """Validate if a stock symbol is properly formatted.

    Args:
        symbol (str): Stock symbol to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not symbol:
        return False

    # Basic format check
    if not symbol.replace(".", "").replace("-", "").isalnum():
        return False

    return True


def calculate_change(current: float, previous: float) -> Dict[str, float]:
    """Calculate price/value change and percentage change.

    Args:
        current (float): Current value.
        previous (float): Previous value.

    Returns:
        Dict[str, float]: Dictionary containing:
            - change: Absolute change
            - pct_change: Percentage change
    """
    change = current - previous
    pct_change = (change / previous) * 100 if previous != 0 else np.nan

    return {"change": change, "pct_change": pct_change}


def calculate_moving_average(data: pd.Series, window: int) -> pd.Series:
    """Calculate moving average for a series.

    Args:
        data (pd.Series): Input data series.
        window (int): Moving average window size.

    Returns:
        pd.Series: Series containing the moving average values.
    """
    return data.rolling(window=window).mean()


def calculate_volatility(data: pd.Series, window: int) -> pd.Series:
    """Calculate rolling volatility for a series.

    Args:
        data (pd.Series): Input data series.
        window (int): Volatility calculation window size.

    Returns:
        pd.Series: Series containing annualized volatility values.
    """
    return data.pct_change().rolling(window=window).std() * np.sqrt(252)


def format_currency(value: float, currency: str) -> str:
    """Format monetary value with currency symbol.

    Args:
        value (float): Monetary value to format.
        currency (str): Currency code (e.g., 'USD', 'TWD').

    Returns:
        str: Formatted string with currency symbol.
    """
    currency_symbols = {"USD": "$", "TWD": "NT$"}

    symbol = currency_symbols.get(currency, "")
    return f"{symbol}{value:,.2f}"


def get_trading_hours(market: str) -> Dict[str, datetime | str]:
    """Get trading hours for a specific market.

    Args:
        market (str): Market code ('US' or 'TW')

    Returns:
        Dict[str, Union[datetime, str]]: Dictionary containing:
            - open: Market opening time (datetime)
            - close: Market closing time (datetime)
            - timezone: Market timezone string
    """
    tz = config.SUPPORTED_MARKETS[market]["timezone"]
    market_tz = pytz.timezone(tz)
    now = datetime.now(market_tz)

    if market == "US":
        open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    elif market == "TW":
        open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        close_time = now.replace(hour=13, minute=30, second=0, microsecond=0)

    return {"open": open_time, "close": close_time, "timezone": tz}


def is_market_open(market: str) -> bool:
    """Check if a market is currently open.

    Args:
        market (str): Market code ('US' or 'TW').

    Returns:
        bool: True if market is open, False otherwise.
    """
    hours = get_trading_hours(market)
    tz = hours["timezone"]
    if isinstance(tz, str):
        market_tz = pytz.timezone(tz)
        now = datetime.now(market_tz)
        open_time = hours["open"]
        close_time = hours["close"]
        if isinstance(open_time, datetime) and isinstance(close_time, datetime):
            return open_time <= now <= close_time
    return False


def format_taiwan_symbol(symbol: str) -> str:
    """Format symbol for Taiwan market.

    Args:
        symbol (str): Original stock symbol.

    Returns:
        str: Properly formatted symbol for Taiwan market
            (appends .TW for TSE or .TWO for OTC).
    """
    # Remove any existing suffixes
    base_symbol = symbol.replace(".TW", "").replace(".TWO", "")

    # Check if OTC or TSE based on stock number
    if base_symbol.startswith("3") or base_symbol.startswith("6"):
        return f"{base_symbol}.TWO"  # OTC market
    return f"{base_symbol}.TW"  # Main market


def is_valid_symbol(symbol: str) -> bool:
    """Validate stock symbol format.

    Args:
        symbol (str): Stock symbol to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not symbol or not isinstance(symbol, str):
        return False

    # Remove market suffixes for validation
    base_symbol = symbol.replace(".TW", "").replace(".TWO", "")

    # Basic validation - must be alphanumeric
    return base_symbol.isalnum()


def is_valid_market_data(data: pd.DataFrame) -> bool:
    """Validate market data format.

    Args:
        data (pd.DataFrame): Market data to validate.

    Returns:
        bool: True if data format is valid, False otherwise.
    """
    if data is None or data.empty:
        return False
    required_columns = {"Open", "High", "Low", "Close", "Volume"}
    return all(col in data.columns for col in required_columns)
