#!/usr/bin/env python3
"""Command-line tool for fetching Taiwan stock market data.

This module provides functionality to fetch various types of Taiwan stock market data
using the FinMind API, including:
- Margin purchase and short sale data
- Institutional investors' buy/sell data
- Foreign shareholding data
- Securities lending data
- Daily short sale balances
- Total institutional investors data
- Total margin purchase and short sale data
- Securities trader information

Example usage:
    # Get institutional investors data for TSMC (2330)
    python -m tools.taiwan_market_data_fetcher 2330 --data-types institutional

    # Get multiple data types for multiple stocks
    python -m tools.taiwan_market_data_fetcher 2330 2454 --data-types margin institutional

    # Save output to CSV file
    python -m tools.taiwan_market_data_fetcher 2330 --data-types institutional --format csv -o data.csv
"""
import argparse
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

import pandas as pd
from FinMind.data import DataLoader
import os
from tools import get_api

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_argparse():
    """Set up argument parser."""
    parser = argparse.ArgumentParser(
        description="Fetch Taiwan stock market data from FinMind"
    )
    parser.add_argument("symbols", nargs="+", help="Stock symbols to fetch data for")
    parser.add_argument(
        "--data-types",
        nargs="+",
        choices=[
            "margin",
            "institutional",
            "shareholding",
            "lending",
            "short_sale",
            "total_institutional",
            "total_margin",
            "trader_info",
            "price"
        ],
        default=["institutional"],
        help="Data types to fetch (default: institutional)",
    )
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format (default: 30 days ago)",
    )
    parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser


def get_margin_purchase_short_sale(
    api: DataLoader,
    stock_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get margin purchase and short sale data for a specific stock.

    Args:
        api: FinMind DataLoader instance
        stock_id: Stock ID
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        DataFrame containing margin purchase and short sale data
    """
    try:
        return api.taiwan_stock_margin_purchase_short_sale(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching margin data for {stock_id}: {str(e)}")
        return pd.DataFrame()


def get_institutional_investors(
    api: DataLoader,
    stock_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get institutional investors' buy/sell data for a specific stock.

    Args:
        api: FinMind DataLoader instance
        stock_id: Stock ID
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        DataFrame containing institutional investors data
    """
    try:
        return api.taiwan_stock_institutional_investors(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching institutional data for {stock_id}: {str(e)}")
        return pd.DataFrame()


def get_shareholding(
    api: DataLoader,
    stock_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get foreign shareholding data for a specific stock.

    Args:
        api: FinMind DataLoader instance
        stock_id: Stock ID
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        DataFrame containing shareholding data
    """
    try:
        return api.taiwan_stock_shareholding(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching shareholding data for {stock_id}: {str(e)}")
        return pd.DataFrame()


def get_securities_lending(
    api: DataLoader,
    stock_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get securities lending data for a specific stock.

    Args:
        api: FinMind DataLoader instance
        stock_id: Stock ID
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        DataFrame containing securities lending data
    """
    try:
        return api.taiwan_stock_securities_lending(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching lending data for {stock_id}: {str(e)}")
        return pd.DataFrame()


def get_daily_short_sale_balances(
    api: DataLoader,
    stock_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get daily short sale balances data for a specific stock.

    Args:
        api: FinMind DataLoader instance
        stock_id: Stock ID
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        DataFrame containing daily short sale balances data
    """
    try:
        return api.taiwan_daily_short_sale_balances(
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching short sale data for {stock_id}: {str(e)}")
        return pd.DataFrame()


def get_total_institutional_investors(
    api: DataLoader,
    start_date: str,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get total institutional investors data.

    Args:
        api: FinMind DataLoader instance
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        DataFrame containing total institutional investors data
    """
    try:
        return api.taiwan_stock_institutional_investors_total(
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching total institutional data: {str(e)}")
        return pd.DataFrame()


def get_total_margin_purchase_short_sale(
    api: DataLoader,
    start_date: str,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get total margin purchase and short sale data.

    Args:
        api: FinMind DataLoader instance
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD

    Returns:
        DataFrame containing total margin purchase and short sale data
    """
    try:
        return api.taiwan_stock_margin_purchase_short_sale_total(
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"Error fetching total margin data: {str(e)}")
        return pd.DataFrame()


def get_securities_trader_info(api: DataLoader) -> pd.DataFrame:
    """
    Get securities trader information.

    Args:
        api: FinMind DataLoader instance

    Returns:
        DataFrame containing securities trader information
    """
    try:
        return api.taiwan_securities_trader_info()
    except Exception as e:
        logger.error(f"Error fetching trader info: {str(e)}")
        return pd.DataFrame()


async def fetch_market_data(stock_id: str) -> Dict[str, Any]:
    """Fetch market data for a stock.
    
    Args:
        stock_id: Stock ID in format "XXXX.TW"
        
    Returns:
        Dictionary containing market data
    """
    try:
        # Initialize API
        api = get_api()
        if api is None:
            logger.error("Failed to initialize FinMind API")
            return {}
        
        # Calculate date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        # Remove .TW suffix for FinMind API
        stock_number = stock_id.replace(".TW", "")
        
        # Fetch data
        market_data = {}
        
        # Get margin data
        margin_df = get_margin_purchase_short_sale(api, stock_number, start_date, end_date)
        if not margin_df.empty:
            market_data["margin"] = margin_df
            
        # Get institutional data    
        inst_df = get_institutional_investors(api, stock_number, start_date, end_date)
        if not inst_df.empty:
            market_data["institutional"] = inst_df
            
        # Get shareholding data
        share_df = get_shareholding(api, stock_number, start_date, end_date)
        if not share_df.empty:
            market_data["shareholding"] = share_df
            
        # Get price data
        price_df = api.taiwan_stock_daily(
            stock_id=stock_number,
            start_date=start_date,
            end_date=end_date
        )
        if not price_df.empty:
            market_data["price"] = price_df
            
        return market_data
        
    except Exception as e:
        logger.error(f"Error fetching market data for {stock_id}: {str(e)}")
        return {}


def save_output(data: Dict[str, Any], output_path: str = "", format: str = "json"):
    """Save data to file or print to stdout."""
    if format == "json":
        output_data = {}
        for symbol, data_types in data.items():
            if data_types is None:
                output_data[symbol] = None
                continue

            output_data[symbol] = {}
            for data_type, df in data_types.items():
                if isinstance(df, pd.DataFrame):
                    output_data[symbol][data_type] = df.to_dict(orient="records")
                else:
                    output_data[symbol][data_type] = df

        if output_path:
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
        else:
            print(json.dumps(output_data, indent=2))

    elif format == "csv":
        # Combine all DataFrames with symbol and data_type columns
        dfs = []
        for symbol, data_types in data.items():
            if data_types is not None:
                for data_type, df in data_types.items():
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        df = df.copy()
                        df["symbol"] = symbol
                        df["data_type"] = data_type
                        dfs.append(df)

        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            if output_path:
                combined_df.to_csv(output_path, index=False)
            else:
                print(combined_df.to_csv(index=False))


def main():
    """Run the main function."""
    parser = setup_argparse()
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Set up dates
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or (
        datetime.now() - timedelta(days=30)
    ).strftime("%Y-%m-%d")

    # Fetch data for each symbol
    results = {}
    for symbol in args.symbols:
        data = fetch_market_data(symbol)
        results[symbol] = data

    # Save or print results
    save_output(results, args.output, args.format)


if __name__ == "__main__":
    main()






