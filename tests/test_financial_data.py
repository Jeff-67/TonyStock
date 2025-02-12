"""Test script for financial data fetcher functionality."""

import json
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd

from tools.financial_data_fetcher import fetch_financial_statements, main, save_output


class TestFinancialDataFetcher(unittest.TestCase):
    """Test cases for financial data fetcher."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample financial statements with datetime index
        dates = pd.date_range(start="2022-01-01", periods=3, freq="YE")

        # Create transposed DataFrames to match yfinance format
        self.sample_income = pd.DataFrame(
            {
                "Revenue": [800000, 900000, 1000000],
                "Net Income": [160000, 180000, 200000],
                "Operating Income": [240000, 270000, 300000],
            },
            index=dates,
        ).T

        self.sample_balance = pd.DataFrame(
            {
                "Total Assets": [1600000, 1800000, 2000000],
                "Total Liabilities": [800000, 900000, 1000000],
                "Equity": [800000, 900000, 1000000],
            },
            index=dates,
        ).T

        self.sample_cash = pd.DataFrame(
            {
                "Operating Cash Flow": [240000, 270000, 300000],
                "Investing Cash Flow": [-80000, -90000, -100000],
                "Financing Cash Flow": [-40000, -45000, -50000],
            },
            index=dates,
        ).T

    def _prepare_statement_for_test(self, df):
        """Prepare financial statement for testing."""
        df = df.reset_index()
        df.columns = ["metric"] + [d.strftime("%Y-%m-%d") for d in df.columns[1:]]
        return df

    @patch("yfinance.Ticker")
    def test_fetch_financial_statements_success(self, mock_ticker):
        """Test successful financial statements fetching."""
        # Setup mock data with proper datetime index
        dates = pd.date_range(start="2023-01-01", periods=2, freq="QE")

        mock_instance = mock_ticker.return_value
        mock_financials = pd.DataFrame(
            {dates[0]: [100, 50], dates[1]: [200, 100]}, index=["Revenue", "Expenses"]
        )
        mock_instance.quarterly_financials = mock_financials

        mock_balance = pd.DataFrame(
            {dates[0]: [1000, 500], dates[1]: [2000, 1000]},
            index=["Assets", "Liabilities"],
        )
        mock_instance.quarterly_balance_sheet = mock_balance

        # Call function
        result = fetch_financial_statements("AAPL", statements=["income", "balance"])

        self.assertIsNotNone(result)
        self.assertIn("income_statement", result)
        self.assertIn("balance_sheet", result)

    @patch("yfinance.Ticker")
    def test_fetch_financial_statements_partial(self, mock_ticker):
        """Test fetching specific statements."""
        # Setup mock data with proper datetime index
        dates = pd.date_range(start="2023-01-01", periods=2, freq="QE")

        mock_instance = mock_ticker.return_value
        mock_financials = pd.DataFrame(
            {dates[0]: [100, 50], dates[1]: [200, 100]}, index=["Revenue", "Expenses"]
        )
        mock_instance.quarterly_financials = mock_financials

        # Call function with only income statement
        result = fetch_financial_statements("AAPL", statements=["income"])

        self.assertIsNotNone(result)
        self.assertIn("income_statement", result)
        self.assertNotIn("balance_sheet", result)

    @patch("yfinance.Ticker")
    def test_fetch_financial_statements_empty(self, mock_ticker):
        """Test handling of empty data."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.financials = pd.DataFrame()
        mock_instance.balance_sheet = pd.DataFrame()
        mock_instance.cashflow = pd.DataFrame()
        mock_ticker.return_value = mock_instance

        # Test
        result = fetch_financial_statements("INVALID", ["income", "balance", "cash"])

        # Verify
        self.assertIsNone(result)

    def test_save_output_json(self):
        """Test JSON output format."""
        # Prepare test data - keep as DataFrame until save_output
        data = {
            "AAPL": {
                "income_statement": self._prepare_statement_for_test(
                    self.sample_income
                ),
                "balance_sheet": self._prepare_statement_for_test(self.sample_balance),
                "cash_flow": self._prepare_statement_for_test(self.sample_cash),
            }
        }

        # Test stdout output
        with patch("sys.stdout", new=StringIO()) as fake_out:
            save_output(data, format="json")
            output = json.loads(fake_out.getvalue())

            # Verify
            self.assertTrue("AAPL" in output)
            self.assertTrue("income_statement" in output["AAPL"])
            self.assertTrue("balance_sheet" in output["AAPL"])
            self.assertTrue("cash_flow" in output["AAPL"])

    def test_save_output_csv(self):
        """Test CSV output format."""
        # Prepare test data - keep as DataFrame until save_output
        data = {
            "AAPL": {
                "income_statement": self._prepare_statement_for_test(
                    self.sample_income
                ),
                "balance_sheet": self._prepare_statement_for_test(self.sample_balance),
                "cash_flow": self._prepare_statement_for_test(self.sample_cash),
            }
        }

        # Test stdout output
        with patch("sys.stdout", new=StringIO()) as fake_out:
            save_output(data, format="csv")
            output = fake_out.getvalue()

            # Verify
            self.assertTrue("symbol" in output.lower())
            self.assertTrue("statement_type" in output.lower())
            self.assertTrue("metric" in output.lower())

    @patch("tools.financial_data_fetcher.fetch_financial_statements")
    def test_command_line_interface(self, mock_fetch):
        """Test command line interface."""
        # Save original argv
        original_argv = sys.argv

        try:
            # Setup mock with proper datetime index
            dates = pd.date_range(start="2023-01-01", periods=1, freq="QE")
            mock_fetch.return_value = {
                "income_statement": pd.DataFrame(
                    {dates[0].strftime("%Y-%m-%d"): [100]}, index=["Revenue"]
                ),
                "balance_sheet": pd.DataFrame(
                    {dates[0].strftime("%Y-%m-%d"): [1000]}, index=["Assets"]
                ),
            }

            # Run main with arguments
            sys.argv = [
                "financial_data_fetcher.py",
                "AAPL",
                "--statements",
                "income",
                "balance",
                "--quarterly",
            ]
            main()

            # Verify fetch was called correctly
            mock_fetch.assert_called_once_with(
                symbol="AAPL", statements=["income", "balance"], quarterly=True
            )
        finally:
            # Restore original argv
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
