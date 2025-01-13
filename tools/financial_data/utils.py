"""
Utility functions for financial data processing.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from . import config

def prepare_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare data for JSON serialization.
    
    Args:
        data: Dictionary containing DataFrames or nested dictionaries with DataFrames
        
    Returns:
        JSON-serializable dictionary
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, pd.DataFrame):
                result[key] = value.to_dict('records')
            elif isinstance(value, dict):
                result[key] = prepare_json_data(value)
            elif value is None:
                result[key] = None
            else:
                result[key] = value
        return result
    return data

def combine_market_data(data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Combine market data from multiple symbols into a single DataFrame.
    
    Args:
        data: Dictionary mapping symbols to DataFrames
        
    Returns:
        Combined DataFrame with symbol column
    """
    combined_data = []
    for symbol, df in data.items():
        if df is not None:
            df = df.copy()
            df['symbol'] = symbol
            combined_data.append(df)
    
    if combined_data:
        return pd.concat(combined_data, ignore_index=True)
    return None

def combine_financial_statements(data: Dict[str, Dict[str, pd.DataFrame]]) -> Optional[pd.DataFrame]:
    """
    Combine financial statements from multiple symbols into a single DataFrame.
    
    Args:
        data: Dictionary mapping symbols to statement dictionaries
        
    Returns:
        Combined DataFrame with symbol and statement_type columns
    """
    combined_data = []
    for symbol, statements in data.items():
        if statements:
            for stmt_type, df in statements.items():
                df = df.copy()
                df['symbol'] = symbol
                df['statement_type'] = stmt_type
                combined_data.append(df)
    
    if combined_data:
        return pd.concat(combined_data, ignore_index=True)
    return None

def validate_symbol(symbol: str) -> bool:
    """
    Validate if a stock symbol is properly formatted.
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not symbol:
        return False
    
    # Basic format check
    if not symbol.replace('.', '').replace('-', '').isalnum():
        return False
    
    return True

def calculate_change(current: float, previous: float) -> Dict[str, float]:
    """
    Calculate price/value change and percentage change.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Dict with absolute and percentage change
    """
    change = current - previous
    pct_change = (change / previous) * 100 if previous != 0 else np.nan
    
    return {
        'change': change,
        'pct_change': pct_change
    }

def calculate_moving_average(data: pd.Series, window: int) -> pd.Series:
    """
    Calculate moving average for a series.
    
    Args:
        data: Input data series
        window: Moving average window
        
    Returns:
        Series with moving average
    """
    return data.rolling(window=window).mean()

def calculate_volatility(data: pd.Series, window: int) -> pd.Series:
    """
    Calculate rolling volatility for a series.
    
    Args:
        data: Input data series
        window: Volatility calculation window
        
    Returns:
        Series with rolling volatility
    """
    return data.pct_change().rolling(window=window).std() * np.sqrt(252)

def format_currency(value: float, currency: str) -> str:
    """
    Format monetary value with currency symbol.
    
    Args:
        value: Monetary value
        currency: Currency code
        
    Returns:
        Formatted string with currency symbol
    """
    currency_symbols = {
        'USD': '$',
        'TWD': 'NT$'
    }
    
    symbol = currency_symbols.get(currency, '')
    return f"{symbol}{value:,.2f}"

def get_trading_hours(market: str) -> Dict[str, datetime]:
    """
    Get trading hours for a market.
    
    Args:
        market: Market code ('US' or 'TW')
        
    Returns:
        Dict with market hours information
    """
    tz = config.SUPPORTED_MARKETS[market]['timezone']
    market_tz = pytz.timezone(tz)
    now = datetime.now(market_tz)
    
    if market == 'US':
        open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    elif market == 'TW':
        open_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        close_time = now.replace(hour=13, minute=30, second=0, microsecond=0)
    
    return {
        'open': open_time,
        'close': close_time,
        'timezone': tz
    }

def is_market_open(market: str) -> bool:
    """
    Check if a market is currently open.
    
    Args:
        market: Market code ('US' or 'TW')
        
    Returns:
        bool: True if market is open, False otherwise
    """
    hours = get_trading_hours(market)
    now = datetime.now(pytz.timezone(hours['timezone']))
    
    return hours['open'] <= now <= hours['close'] 