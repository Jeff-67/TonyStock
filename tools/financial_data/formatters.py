"""Data formatting and standardization for financial data.

This module provides functions to standardize financial data formats,
including market data (price, volume) and financial statements.
"""

import pandas as pd

from . import config


def standardize_market_data(data: pd.DataFrame) -> pd.DataFrame:
    """Standardize market data (price, volume) into a consistent format.

    Takes raw market data from yfinance and standardizes it into a consistent format
    with specific column names and data types.

    Args:
        data (pd.DataFrame): Raw market data DataFrame from yfinance.

    Returns:
        pd.DataFrame: Standardized DataFrame with columns:
            - date (str): Trading date in YYYY-MM-DD format
            - open (float): Opening price
            - high (float): Highest price
            - low (float): Lowest price
            - close (float): Closing price
            - volume (int): Trading volume

    Raises:
        ValueError: If required columns are missing from input data.
    """
    # Reset index to get date as column
    df = data.reset_index()

    # Format date
    df["Date"] = df["Date"].dt.strftime(config.DATE_FORMAT)

    # Select and rename columns
    required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError(
            f"Missing required columns. Expected {required_columns}, got {df.columns.tolist()}"
        )

    df = df[required_columns].copy()
    df.columns = config.MARKET_DATA_COLUMNS

    # Convert to appropriate types
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["volume"] = df["volume"].astype(int)

    return df


def standardize_financial_statement(data: pd.DataFrame) -> pd.DataFrame:
    """Standardize financial statement data into a consistent format.

    Takes raw financial statement data from yfinance and standardizes it into a
    consistent format with metrics as rows and dates as columns.

    Args:
        data (pd.DataFrame): Raw financial statement DataFrame from yfinance.

    Returns:
        pd.DataFrame: Standardized DataFrame with:
            - metric column: Financial metrics
            - date columns: Values for each reporting period
    """
    # Reset index to get metrics as column
    df = data.reset_index()

    # Rename index column to 'metric'
    df.rename(columns={df.columns[0]: "metric"}, inplace=True)

    # Format date columns
    date_columns = [col for col in df.columns if col != "metric"]
    df.columns = ["metric"] + [
        pd.to_datetime(col).strftime(config.DATE_FORMAT) for col in date_columns
    ]

    # Convert numeric columns to float
    for col in df.columns[1:]:  # Skip metric column
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
