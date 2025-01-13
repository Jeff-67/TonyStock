#!/usr/bin/env python3
"""
Command-line tool for fetching market data from various sources.
"""
import argparse
import json
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import logging

from financial_data import formatters
from financial_data import utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_argparse():
    """Setup argument parser."""
    parser = argparse.ArgumentParser(description='Fetch market data for stocks')
    parser.add_argument('symbols', nargs='+', help='Stock symbols to fetch data for')
    parser.add_argument('--interval', default='1d', choices=['1d', '1wk', '1mo'],
                       help='Data interval (default: 1d)')
    parser.add_argument('--days', type=int, default=365,
                       help='Number of days of historical data to fetch (default: 365)')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser

def fetch_market_data(symbol: str, interval: str = '1d', days: int = 365) -> pd.DataFrame:
    """
    Fetch market data for a symbol.
    
    Args:
        symbol: Stock symbol
        interval: Time interval ('1d', '1wk', '1mo')
        days: Number of days of historical data
        
    Returns:
        DataFrame with market data
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        logger.info(f"Fetching {interval} data for {symbol} from {start_time.date()} to {end_time.date()}")
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(
            interval=interval,
            start=start_time,
            end=end_time
        )
        
        if data.empty:
            logger.error(f"No data available for {symbol}")
            return None
            
        # Use standardization function from formatters
        return formatters.standardize_market_data(data)
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

def save_output(data: dict, output_path: str = None, format: str = 'json'):
    """Save data to file or print to stdout."""
    if format == 'json':
        # Use utils function for JSON serialization
        output_data = utils.prepare_json_data(data)
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
        else:
            print(json.dumps(output_data, indent=2))
            
    elif format == 'csv':
        # Use utils function for CSV formatting
        combined_df = utils.combine_market_data(data)
        if combined_df is not None:
            if output_path:
                combined_df.to_csv(output_path, index=False)
            else:
                print(combined_df.to_csv(index=False))

def main():
    """Main function."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Fetch data for each symbol
    results = {}
    for symbol in args.symbols:
        data = fetch_market_data(
            symbol=symbol,
            interval=args.interval,
            days=args.days
        )
        results[symbol] = data
    
    # Save or print results
    save_output(results, args.output, args.format)

if __name__ == "__main__":
    main() 