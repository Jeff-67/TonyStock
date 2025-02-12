"""Tools package for stock analysis and data collection."""

import os
import logging
import time
from typing import Optional
from FinMind.data import DataLoader
from settings import Settings

settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_api(max_retries: int = 3, retry_delay: int = 2) -> Optional[DataLoader]:
    """Initialize and return FinMind API instance with retry mechanism.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        DataLoader instance if successful, None otherwise
    """
    for attempt in range(max_retries):
        try:
            api = DataLoader()
            api_token = settings.finmind_api_key
            
            if not api_token:
                logger.error("FINMIND_API_KEY environment variable not set")
                return None
                
            # Login with token
            api.login_by_token(api_token=api_token)
            
            # Verify login by attempting to fetch some basic data
            try:
                # Test fetch some basic data
                test_data = api.taiwan_stock_info()
                if test_data is not None and not test_data.empty:
                    logger.info("FinMind API initialized successfully")
                    return api
                else:
                    logger.error("API initialization failed: Test data fetch returned empty result")
            except Exception as e:
                logger.error(f"API test fetch failed: {str(e)}")
                
            if attempt < max_retries - 1:
                logger.warning(f"Retrying API initialization (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                
        except Exception as e:
            logger.error(f"Error initializing FinMind API: {str(e)}")
            if attempt < max_retries - 1:
                logger.warning(f"Retrying API initialization (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.error("All retry attempts failed")
                raise
    
    return None

# Initialize API instance with retry mechanism
api = get_api()
if api is None:
    logger.error("Failed to initialize FinMind API. Please check your API key and connection.")
