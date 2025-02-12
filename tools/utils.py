import pandas as pd
from typing import Dict, Optional

def load_tse_ticker_mapping() -> Dict[str, str]:
    """
    Load company name to stock ticker mapping from TSE_ticker.csv
    
    Returns:
        Dict[str, str]: Dictionary mapping company names to their stock tickers
    """
    try:
        df = pd.read_csv('static/TSE_ticker.csv', header=None, names=['code', 'name'])
        # Create name to code mapping
        name_to_code = dict(zip(df['name'], df['code']))
        return name_to_code
    except Exception as e:
        print(f"Error loading TSE ticker mapping: {e}")
        return {}

def company_to_ticker(company_name: str) -> Optional[str]:
    """
    Convert company name to stock ticker code
    
    Args:
        company_name (str): Name of the company
        
    Returns:
        Optional[str]: Stock ticker code if found, None otherwise
    """
    mapping = load_tse_ticker_mapping()
    return mapping.get(company_name)
