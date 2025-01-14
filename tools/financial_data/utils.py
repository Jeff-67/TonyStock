"""
Utility functions for financial data processing.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from . import config
import json

class PandasJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for pandas objects."""
    def default(self, obj):
        if isinstance(obj, pd.DataFrame):
            return obj.replace({np.nan: None}).to_dict(orient='records')
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
    """Prepare data for JSON serialization."""
    if not data:
        return {}
    
    # Use custom encoder for JSON serialization
    return json.loads(json.dumps(data, cls=PandasJSONEncoder))

def combine_market_data(data: dict) -> pd.DataFrame:
    """Combine market data from multiple symbols into a single DataFrame."""
    if not data:
        return None
        
    dfs = []
    for symbol, df in data.items():
        if isinstance(df, pd.DataFrame):
            df['Symbol'] = symbol
            dfs.append(df)
    
    if not dfs:
        return None
        
    return pd.concat(dfs, axis=0, ignore_index=True)

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

def format_taiwan_symbol(symbol: str) -> str:
    """
    Format symbol for Taiwan market.
    
    Args:
        symbol: Original stock symbol
        
    Returns:
        Properly formatted symbol for Taiwan market
    """
    # Remove any existing suffixes
    base_symbol = symbol.replace('.TW', '').replace('.TWO', '')
    
    # Check if OTC or TSE based on stock number
    if base_symbol.startswith('3') or base_symbol.startswith('6'):
        return f"{base_symbol}.TWO"  # OTC market
    return f"{base_symbol}.TW"      # Main market

def is_valid_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format.
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
        
    # Remove market suffixes for validation
    base_symbol = symbol.replace('.TW', '').replace('.TWO', '')
    
    # Basic validation - must be alphanumeric
    return base_symbol.isalnum()

def is_valid_market_data(data: pd.DataFrame) -> bool:
    """Validate market data format."""
    if data is None or data.empty:
        return False
    required_columns = {'Open', 'High', 'Low', 'Close', 'Volume'}
    return all(col in data.columns for col in required_columns) 