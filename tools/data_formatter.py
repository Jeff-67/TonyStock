import re
from typing import Dict

class DataFormatter:
    """Format data for analysis."""
    
    COMPANY_TO_STOCK = {
        "京鼎": "3413.TW",
        "文曄": "3036.TW",
        "群聯": "8299.TW"
    }
    
    def format_stock_number(self, company: str) -> str:
        """Format company name to stock number.
        
        Args:
            company: Company name in Chinese
            
        Returns:
            Formatted stock number (e.g. "3413.TW")
            
        Raises:
            ValueError: If company not found
        """
        if company in self.COMPANY_TO_STOCK:
            return self.COMPANY_TO_STOCK[company]
            
        # Try to extract stock number if already in correct format
        if re.match(r'^\d{4}\.TW$', company):
            return company
            
        raise ValueError(f"Unknown company: {company}") 