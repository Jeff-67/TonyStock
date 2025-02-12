"""Market data utilities module."""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class MarketMetrics:
    """Common market metrics."""
    price: float = 0.0
    volume: int = 0
    price_change: float = 0.0
    price_change_percent: float = 0.0
    market_value: float = 0.0
    turnover_rate: float = 0.0

class DataFormatter:
    """Utility class for data formatting."""
    
    @staticmethod
    def format_stock_number(symbol: str) -> str:
        """Format stock number to standard format."""
        return ''.join(filter(str.isdigit, symbol)).zfill(4)
    
    @staticmethod
    def format_date(date_obj: Optional[datetime] = None) -> str:
        """Format date to YYYYMMDD format."""
        if date_obj is None:
            date_obj = datetime.now()
        while date_obj.weekday() > 4:  # Adjust for weekends
            date_obj -= timedelta(days=1)
        return date_obj.strftime("%Y%m%d")
    
    @staticmethod
    def calculate_change_percent(current: float, previous: float) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 0.0
        return ((current - previous) / abs(previous)) * 100

class DataValidator:
    """Utility class for data validation."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, name: str) -> bool:
        """Validate DataFrame for NaN values and log issues."""
        if df.empty:
            logger.warning(f"{name} DataFrame is empty")
            return False
            
        nan_cols = df.columns[df.isna().any()].tolist()
        if nan_cols:
            logger.warning(f"Found NaN values in {name} columns: {nan_cols}")
            logger.warning(f"NaN counts: {df[nan_cols].isna().sum().to_dict()}")
            return False
        return True
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Convert value to float safely, handling NaN and None."""
        try:
            if pd.isna(value) or value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """Convert value to int safely, handling NaN and None."""
        try:
            if pd.isna(value) or value is None:
                return default
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """Validate date range."""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return start <= end
        except ValueError:
            return False

class MarketDataProcessor:
    """Process market data with common calculations."""
    
    def __init__(self):
        self.validator = DataValidator()
        self.formatter = DataFormatter()
    
    def process_raw_data(
        self,
        data: Dict[str, pd.DataFrame],
        required_columns: Dict[str, List[str]]
    ) -> Dict[str, pd.DataFrame]:
        """Process and validate raw data."""
        processed_data = {}
        
        for key, df in data.items():
            if key not in required_columns:
                continue
                
            if not isinstance(df, pd.DataFrame):
                logger.warning(f"Invalid data type for {key}: {type(df)}")
                continue
                
            if df.empty:
                logger.warning(f"Empty DataFrame for {key}")
                continue
                
            # Validate required columns
            missing_cols = set(required_columns[key]) - set(df.columns)
            if missing_cols:
                logger.warning(f"Missing columns in {key}: {missing_cols}")
                continue
                
            # Validate data quality
            if not self.validator.validate_dataframe(df, key):
                # Basic cleaning
                df = df.fillna(method='ffill').fillna(method='bfill')
                logger.info(f"Cleaned {key} data of NaN values")
                
            processed_data[key] = df
            
        return processed_data
    
    def prepare_market_metrics(
        self,
        price_data: pd.DataFrame,
        volume_data: Optional[pd.DataFrame] = None
    ) -> MarketMetrics:
        """Prepare common market metrics."""
        try:
            if price_data.empty:
                return MarketMetrics()
                
            latest = price_data.iloc[-1]
            previous = price_data.iloc[-2] if len(price_data) > 1 else latest
            
            price = self.validator.safe_float(latest.get('close'))
            prev_price = self.validator.safe_float(previous.get('close'))
            volume = self.validator.safe_int(latest.get('volume'))
            
            return MarketMetrics(
                price=price,
                volume=volume,
                price_change=price - prev_price,
                price_change_percent=self.formatter.calculate_change_percent(price, prev_price),
                market_value=price * volume if volume else 0.0,
                turnover_rate=self.calculate_turnover_rate(
                    volume,
                    self.validator.safe_int(latest.get('shares_outstanding', 0))
                )
            )
        except Exception as e:
            logger.error(f"Error preparing market metrics: {e}")
            return MarketMetrics()
    
    @staticmethod
    def calculate_moving_average(data: pd.Series, window: int) -> pd.Series:
        """Calculate moving average."""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def calculate_volatility(data: pd.Series, window: int) -> pd.Series:
        """Calculate rolling volatility."""
        return data.pct_change().rolling(window=window).std()
    
    @staticmethod
    def calculate_turnover_rate(volume: int, shares_outstanding: int) -> float:
        """Calculate turnover rate."""
        if shares_outstanding == 0:
            return 0.0
        return (volume / shares_outstanding) * 100
    
    def get_analysis_summary(self, metrics: MarketMetrics, content: str = "") -> str:
        """Generate analysis summary."""
        summary = [
            f"價格: {metrics.price:.2f}",
            f"漲跌: {metrics.price_change:+.2f} ({metrics.price_change_percent:+.2f}%)",
            f"成交量: {metrics.volume:,}",
            f"週轉率: {metrics.turnover_rate:.2f}%"
        ]
        
        if content:
            summary.append("\n分析結果:")
            summary.append(content)
            
        return "\n".join(summary) 