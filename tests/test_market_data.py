"""
Test script for market data fetcher functionality.
"""
import unittest
import json
import pandas as pd
from io import StringIO
from unittest.mock import patch, MagicMock

from tools.market_data_fetcher import fetch_market_data, save_output

class TestMarketDataFetcher(unittest.TestCase):
    """Test cases for market data fetcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data
        self.sample_data = pd.DataFrame({
            'Date': pd.date_range(start='2024-01-01', periods=5),
            'Open': [100, 101, 102, 103, 104],
            'High': [105, 106, 107, 108, 109],
            'Low': [95, 96, 97, 98, 99],
            'Close': [102, 103, 104, 105, 106],
            'Volume': [1000, 1100, 1200, 1300, 1400]
        })
        self.sample_data.set_index('Date', inplace=True)
    
    @patch('yfinance.Ticker')
    def test_fetch_market_data_success(self, mock_ticker):
        """Test successful market data fetching."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.history.return_value = self.sample_data
        mock_ticker.return_value = mock_instance
        
        # Test
        result = fetch_market_data('AAPL', interval='1d', days=5)
        
        # Verify
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 5)
        self.assertTrue('date' in result.columns)
        self.assertTrue('open' in result.columns)
        self.assertTrue('close' in result.columns)
        
    @patch('yfinance.Ticker')
    def test_fetch_market_data_empty(self, mock_ticker):
        """Test handling of empty data."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance
        
        # Test
        result = fetch_market_data('INVALID', interval='1d', days=5)
        
        # Verify
        self.assertIsNone(result)
    
    def test_save_output_json(self):
        """Test JSON output format."""
        # Prepare test data - keep as DataFrame until save_output
        data = {'AAPL': self.sample_data.reset_index()}
        data['AAPL']['Date'] = data['AAPL']['Date'].dt.strftime('%Y-%m-%d')
        
        # Test stdout output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            save_output(data, format='json')
            output = json.loads(fake_out.getvalue())
            
            # Verify
            self.assertTrue('AAPL' in output)
            self.assertEqual(len(output['AAPL']), 5)
    
    def test_save_output_csv(self):
        """Test CSV output format."""
        # Prepare test data
        data = {'AAPL': self.sample_data.reset_index()}
        data['AAPL']['Date'] = data['AAPL']['Date'].dt.strftime('%Y-%m-%d')
        
        # Test stdout output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            save_output(data, format='csv')
            output = fake_out.getvalue()
            
            # Verify
            self.assertTrue('date' in output.lower())
            self.assertTrue('open' in output.lower())
            self.assertTrue('close' in output.lower())
    
    def test_command_line_interface(self):
        """Test command line interface."""
        test_args = ['market_data_fetcher.py', 'AAPL', '--interval', '1d', '--days', '5']
        
        with patch('sys.argv', test_args):
            with patch('tools.market_data_fetcher.fetch_market_data') as mock_fetch:
                # Prepare mock data - return DataFrame
                mock_data = self.sample_data.reset_index()
                mock_data['Date'] = mock_data['Date'].dt.strftime('%Y-%m-%d')
                mock_fetch.return_value = mock_data
                
                # Import main only when needed to avoid early parsing of sys.argv
                from tools.market_data_fetcher import main
                
                # Test
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    output = fake_out.getvalue()
                    
                    # Verify
                    self.assertTrue(len(output) > 0)
                    mock_fetch.assert_called_once_with(
                        symbol='AAPL',
                        interval='1d',
                        days=5
                    )

if __name__ == '__main__':
    unittest.main() 