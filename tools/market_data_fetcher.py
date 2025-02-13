#!/usr/bin/env python3
"""Command-line tool for fetching market data from various sources."""
import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf
import asyncio

from tools.financial_data import utils
from settings import Settings

settings = Settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_argparse():
    """Set up argument parser."""
    parser = argparse.ArgumentParser(description="Fetch market data for stocks")
    parser.add_argument("symbols", nargs="+", help="Stock symbols to fetch data for")
    parser.add_argument(
        "--interval",
        default="1d",
        choices=["1d", "1wk", "1mo"],
        help="Data interval (default: 1d)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days of historical data to fetch (default: 365)",
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



async def fetch_market_data(
    symbol: Any, interval: str = "1d", days: int = 365
) -> Optional[pd.DataFrame]:
    """
    Fetch market data for a symbol.

    Args:
        symbol: Stock symbol (can be string or int)
        interval: Data interval (1d, 1wk, 1mo)
        days: Number of days of historical data

    Returns:
        DataFrame with market data or None if error
    """
    try:
        # Get current date and adjust for business days
        end_time = datetime.now()
        while end_time.weekday() > 4:  # Adjust if current day is weekend
            end_time -= timedelta(days=1)
        
        start_time = end_time - timedelta(days=days)
        # Format dates as strings
        end_date = end_time.strftime("%Y-%m-%d")
        start_date = start_time.strftime("%Y-%m-%d")

        # Convert symbol to string and format Taiwan stock symbols
        symbol_str = str(symbol)
        logger.info(
            f"Fetching {interval} data for {symbol_str} from {start_date} to {end_date}"
        )

        # Format Taiwan stock symbols
        if symbol_str.isdigit() or any(
            symbol_str.startswith(prefix) for prefix in ["2", "3", "4", "6", "8", "9"]
        ):
            symbol_str = utils.format_taiwan_symbol(symbol_str)

        if not utils.is_valid_symbol(symbol_str):
            logger.error(f"Invalid symbol: {symbol_str}")
            return None

        try:
            # Convert dates to strings for yfinance
            start_str = start_date
            end_str = end_date
            
            for attempt in range(settings.max_retries):
                try:
                    ticker = yf.Ticker(symbol_str)
                    data = ticker.history(interval=interval, start=start_str, end=end_str)
                    
                    if data is not None and not data.empty:
                        break
                        
                    if attempt < settings.max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{settings.max_retries} for {symbol_str}")
                        await asyncio.sleep(settings.retry_delay)
                        settings.retry_delay *= 2  # Exponential backoff
                except Exception as e:
                    if attempt < settings.max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{settings.max_retries} for {symbol_str} due to error: {str(e)}")
                        await asyncio.sleep(settings.retry_delay)
                        settings.retry_delay *= 2
                    else:
                        raise

            if data is None or data.empty:
                logger.error(f"No data available for {symbol_str} after {settings.max_retries} retries")
                return None

            if not isinstance(data, pd.DataFrame):
                logger.error(f"Invalid data type returned for {symbol_str}: {type(data)}")
                return None

            # Reset index to get Date as a column
            data = data.reset_index()

            # Rename columns to match expected format
            column_mapping = {
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            data = data.rename(columns=column_mapping)

            # Select only required columns
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            data = data[required_columns]

            # Convert numeric columns to appropriate types
            for col in ['open', 'high', 'low', 'close']:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            data['volume'] = pd.to_numeric(data['volume'], errors='coerce').astype('int64')

            # Format date column
            data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

            # Validate data completeness
            if len(data) < days * 0.8:  # If the amount of data is less than 80% of the expected
                logger.warning(f"Retrieved only {len(data)} days of data for {symbol_str}, expected {days} days")
            
            return data

        except Exception as e:
            logger.error(f"Error fetching data from yfinance for {symbol_str}: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Error in fetch_market_data for {symbol}: {str(e)}")
        return None


def save_output(data: Dict[str, Any], output_path: str = "", format: str = "json"):
    """Save data to file or print to stdout."""
    if format == "json":
        # Use utils function for JSON serialization
        output_data = utils.prepare_json_data(data)

        if output_path:
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
        else:
            print(json.dumps(output_data, indent=2))

    elif format == "csv":
        # Use utils function for CSV formatting
        combined_df = utils.combine_market_data(data)
        if combined_df is not None:
            if output_path:
                combined_df.to_csv(output_path, index=False)
            else:
                print(combined_df.to_csv(index=False))


async def main_async():
    """Execute the main function asynchronously."""
    parser = setup_argparse()
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Fetch data for each symbol
    results = {}
    for symbol in args.symbols:
        data = await fetch_market_data(symbol=symbol, interval=args.interval, days=args.days)
        results[symbol] = data

    # Save or print results
    save_output(results, args.output, args.format)


def main():
    """Execute the main function."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
