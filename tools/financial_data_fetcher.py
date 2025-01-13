#!/usr/bin/env python3
"""
Command-line tool for fetching financial statements from various sources.
"""
import argparse
import json
import pandas as pd
import yfinance as yf
import logging

from financial_data import formatters
from financial_data import utils
from financial_data import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_argparse():
    """Setup argument parser."""
    parser = argparse.ArgumentParser(description='Fetch financial statements for stocks')
    parser.add_argument('symbols', nargs='+', help='Stock symbols to fetch data for')
    parser.add_argument('--statements', nargs='+', 
                       choices=['income', 'balance', 'cash'],
                       default=['income', 'balance', 'cash'],
                       help='Statements to fetch (default: all)')
    parser.add_argument('--quarterly', action='store_true', default=True,
                       help='Fetch quarterly statements (default: True)')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser

def fetch_financial_statements(symbol: str, statements: list, quarterly: bool = True) -> dict:
    """
    Fetch financial statements for a symbol.
    
    Args:
        symbol: Stock symbol
        statements: List of statements to fetch
        quarterly: If True, fetch quarterly statements, else annual
        
    Returns:
        Dict containing requested financial statements
    """
    try:
        logger.info(f"Fetching {'quarterly' if quarterly else 'annual'} financial statements for {symbol}")
        
        ticker = yf.Ticker(symbol)
        results = {}
        
        if 'income' in statements:
            income_stmt = ticker.quarterly_financials if quarterly else ticker.financials
            if not income_stmt.empty:
                results['income_statement'] = formatters.standardize_financial_statement(income_stmt)
        
        if 'balance' in statements:
            balance_sheet = ticker.quarterly_balance_sheet if quarterly else ticker.balance_sheet
            if not balance_sheet.empty:
                results['balance_sheet'] = formatters.standardize_financial_statement(balance_sheet)
        
        if 'cash' in statements:
            cash_flow = ticker.quarterly_cashflow if quarterly else ticker.cashflow
            if not cash_flow.empty:
                results['cash_flow'] = formatters.standardize_financial_statement(cash_flow)
        
        if not results:
            logger.error(f"No financial statements available for {symbol}")
            return None
            
        return results
        
    except Exception as e:
        logger.error(f"Error fetching financial statements for {symbol}: {str(e)}")
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
        combined_df = utils.combine_financial_statements(data)
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
        data = fetch_financial_statements(
            symbol=symbol,
            statements=args.statements,
            quarterly=args.quarterly
        )
        results[symbol] = data
    
    # Save or print results
    save_output(results, args.output, args.format)

if __name__ == "__main__":
    main() 