#!/usr/bin/env python3
"""Command-line tool for fetching financial statements from various sources."""
import argparse
import json
import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
import yfinance as yf

from tools.financial_data import formatters, utils

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_argparse():
    """Set up argument parser."""
    parser = argparse.ArgumentParser(
        description="Fetch financial statements for stocks"
    )
    parser.add_argument("symbols", nargs="+", help="Stock symbols to fetch data for")
    parser.add_argument(
        "--statements",
        nargs="+",
        choices=["income", "balance", "cash"],
        default=["income", "balance", "cash"],
        help="Statements to fetch (default: all)",
    )
    parser.add_argument(
        "--quarterly",
        action="store_true",
        default=True,
        help="Fetch quarterly statements (default: True)",
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


def fetch_financial_statements(
    symbol: str, statements=None, quarterly=True
) -> dict | None:
    """Fetch financial statements for a symbol.

    Args:
        symbol: Stock symbol to fetch data for
        statements: List of statements to fetch. Defaults to ["income", "balance"]
        quarterly: Whether to fetch quarterly (True) or annual (False) data

    Returns:
        dict: Dictionary containing the requested financial statements
    """
    if statements is None:
        statements = ["income", "balance"]

    try:
        if not utils.is_valid_symbol(symbol):
            logger.error(f"Invalid symbol: {symbol}")
            return None

        logger.info(
            f"Fetching {'quarterly' if quarterly else 'annual'} financial statements for {symbol}"
        )

        ticker = yf.Ticker(symbol)
        results = {}

        # Map statement types to their yfinance attributes and output names
        statement_map = {
            "income": {
                "data": (
                    ticker.quarterly_financials if quarterly else ticker.financials
                ),
                "name": "income_statement",
            },
            "balance": {
                "data": (
                    ticker.quarterly_balance_sheet
                    if quarterly
                    else ticker.balance_sheet
                ),
                "name": "balance_sheet",
            },
            "cash": {
                "data": (ticker.quarterly_cashflow if quarterly else ticker.cashflow),
                "name": "cash_flow",
            },
        }

        for stmt in statements:
            if stmt in statement_map:
                try:
                    data = statement_map[stmt]["data"]
                    # Check if data exists and is not empty
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        # Convert timestamps to strings in column names
                        data.columns = data.columns.strftime("%Y-%m-%d")
                        results[statement_map[stmt]["name"]] = (
                            formatters.standardize_financial_statement(data)
                        )
                    elif isinstance(data, (dict, list)):  # Handle mock data in tests
                        results[statement_map[stmt]["name"]] = data
                except Exception as e:
                    logger.warning(f"Error processing {stmt} statement: {str(e)}")
                    continue

        if not results:
            logger.error(f"No financial statements available for {symbol}")
            return None

        return results

    except Exception as e:
        logger.error(f"Error fetching financial statements for {symbol}: {str(e)}")
        return None


def save_output(data: Dict[str, Any], output_path: str = "", format: str = "json"):
    """Save data to file or print to stdout."""
    if format == "json":
        # Convert DataFrames to dictionaries before JSON serialization
        output_data: Dict[str, Any] = {}
        for symbol, statements in data.items():
            if statements is None:
                output_data[symbol] = None
                continue

            output_data[symbol] = {}
            for stmt_type, df in statements.items():
                if isinstance(df, pd.DataFrame):
                    # Convert DataFrame to dict and handle NaN values
                    output_data[symbol][stmt_type] = df.replace({np.nan: None}).to_dict(
                        orient="records"
                    )
                else:
                    output_data[symbol][stmt_type] = df

        if output_path:
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
        else:
            print(json.dumps(output_data, indent=2))

    elif format == "csv":
        combined_df = utils.combine_financial_statements(data)
        if combined_df is not None:
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

    # Fetch data for each symbol
    results = {}
    for symbol in args.symbols:
        data = fetch_financial_statements(
            symbol=symbol, statements=args.statements, quarterly=args.quarterly
        )
        results[symbol] = data

    # Save or print results
    save_output(results, args.output, args.format)


if __name__ == "__main__":
    main()
