"""
Configuration settings for financial data tools.
"""

# Market data settings
MARKET_DATA_COLUMNS = [
    'date', 'open', 'high', 'low', 'close', 'volume'
]

# Financial statement settings
STATEMENT_TYPES = {
    'income': 'income_statement',
    'balance': 'balance_sheet',
    'cash': 'cash_flow'
}

# Date format settings
DATE_FORMAT = '%Y-%m-%d'

# API settings
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 5  # seconds

# Output settings
DEFAULT_OUTPUT_FORMAT = 'json'
CSV_SEPARATOR = ','
JSON_INDENT = 2 