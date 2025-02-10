"""Chips Analysis Tool.

This module implements chips-level analysis functionality,
analyzing institutional and retail investor behaviors.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any

import numpy as np
import pandas as pd
from tools.core.tool_protocol import Tool
from tools.market_data_fetcher import fetch_market_data
from tools.financial_data import utils
import asyncio
from settings import Settings
from opik import track
settings = Settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def safe_float(value: Union[float, np.float64, None]) -> Optional[float]:
    """Safely handle floating-point values.

    Args:
        value: The value to process

    Returns:
        The processed floating-point number or None
    """
    if value is None:
        return None
    if isinstance(value, (float, np.float64)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    return None


def safe_round(value: Optional[float], decimals: int = 2) -> Optional[float]:
    """Safely round a floating-point number.

    Args:
        value: The number to round
        decimals: Number of decimal places

    Returns:
        The rounded number or None
    """
    if value is None:
        return None
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return None


@dataclass
class ChipsAnalysis:
    """Chips analysis results container."""
    
    # Volume Analysis
    avg_volume_5d: Optional[float]
    avg_volume_20d: Optional[float]
    volume_trend: str  # "Increasing", "Decreasing", or "Stable"
    volume_concentration: Optional[float]  # Volume concentration ratio
    
    # Price-Volume Analysis
    price_volume_correlation_5d: Optional[float]
    price_volume_correlation_20d: Optional[float]
    
    # Chips Distribution
    avg_price_volume: Optional[float]  # Volume-weighted average price
    price_distribution: Dict[str, float]  # Price ranges and their volume percentages
    
    # Buying/Selling Pressure
    buying_pressure: Optional[float]  # Ratio of buying volume to total volume
    selling_pressure: Optional[float]  # Ratio of selling volume to total volume
    pressure_trend: str  # "Buying", "Selling", or "Neutral"
    
    # Institutional Analysis
    institutional_holding_ratio: Optional[float]  # Percentage of institutional holdings
    institutional_net_buy_5d: Optional[float]  # Net institutional buying over 5 days
    institutional_net_buy_20d: Optional[float]  # Net institutional buying over 20 days
    
    # Retail Analysis
    retail_concentration: Optional[float]  # Retail investor concentration
    retail_net_buy_5d: Optional[float]  # Net retail buying over 5 days
    retail_net_buy_20d: Optional[float]  # Net retail buying over 20 days
    
    # Chip Concentration
    major_holders_ratio: Optional[float]  # Percentage held by major shareholders
    concentration_index: Optional[float]  # Overall chip concentration index


class ChipsTool(Tool):
    """Chips Analysis tool implementation."""

    def __init__(self):
        """Initialize the Chips tool."""
        super().__init__()

    async def analyze_chips(self, symbol: str, days: int = 60) -> Optional[ChipsAnalysis]:
        """Perform chips-level analysis on a stock.
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data to analyze
            
        Returns:
            ChipsAnalysis object containing the analysis results,
            or None if data is not available
        """
        try:
            # Format Taiwan stock symbol
            if symbol.isdigit() or any(
                symbol.startswith(prefix) for prefix in ["2", "3", "4", "6", "8", "9"]
            ):
                symbol = utils.format_taiwan_symbol(symbol)

            if not utils.is_valid_symbol(symbol):
                logger.error(f"Invalid symbol format: {symbol}")
                return None
                        
            for attempt in range(settings.max_retries):
                try:
                    df = await fetch_market_data(symbol, days=days * 2)
                    
                    if df is not None and len(df) >= days:
                        break
                        
                    if attempt < settings.max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{settings.max_retries} for {symbol}")
                        await asyncio.sleep(settings.retry_delay)
                        settings.retry_delay *= 2  # Exponential backoff
                except Exception as e:
                    if attempt < settings.max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{settings.max_retries} for {symbol} due to error: {str(e)}")
                        await asyncio.sleep(settings.retry_delay)
                        settings.retry_delay *= 2
                    else:
                        raise e

            if df is None:
                logger.error(f"No market data available for {symbol}")
                return None
                
            if len(df) < days:
                logger.error(f"Insufficient market data for {symbol} (got {len(df)} days, need at least {days})")
                return None

            # Convert to numpy arrays and pandas series for analysis
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            
            # Calculate volume metrics
            avg_volume_5d = safe_float(volume.tail(5).mean())
            avg_volume_20d = safe_float(volume.tail(20).mean())
            
            # Determine volume trend
            volume_trend = "Stable"
            if avg_volume_5d and avg_volume_20d:
                if avg_volume_5d > avg_volume_20d * 1.1:
                    volume_trend = "Increasing"
                elif avg_volume_5d < avg_volume_20d * 0.9:
                    volume_trend = "Decreasing"
            
            # Calculate volume concentration
            volume_concentration = safe_float(
                (volume.tail(5).sum() / volume.tail(20).sum()) if len(volume) >= 20 else None
            )
            
            # Calculate price-volume correlation
            price_volume_correlation_5d = safe_float(
                close.tail(5).corr(volume.tail(5))
            )
            price_volume_correlation_20d = safe_float(
                close.tail(20).corr(volume.tail(20))
            )
            
            # Calculate volume-weighted average price
            avg_price_volume = safe_float(
                (close * volume).sum() / volume.sum() if len(volume) > 0 else None
            )
            
            # Calculate price distribution
            price_range = close.max() - close.min()
            bins = 5
            if price_range > 0:
                price_bins = pd.cut(close, bins=bins)
                price_distribution = {
                    f"Range_{i+1}": safe_float(volume[price_bins == interval].sum() / volume.sum())
                    for i, interval in enumerate(price_bins.unique())
                }
            else:
                price_distribution = {f"Range_{i+1}": 0.0 for i in range(bins)}
            
            # Calculate buying/selling pressure
            # Using close price relative to day's range as a proxy
            daily_position = (close - close.shift(1)) / close.shift(1)
            buying_pressure = safe_float(
                len(daily_position[daily_position > 0]) / len(daily_position)
            )
            selling_pressure = safe_float(
                len(daily_position[daily_position < 0]) / len(daily_position)
            )
            
            pressure_trend = "Neutral"
            if buying_pressure and selling_pressure:
                if buying_pressure > selling_pressure * 1.1:
                    pressure_trend = "Buying"
                elif selling_pressure > buying_pressure * 1.1:
                    pressure_trend = "Selling"
            
            # Placeholder for institutional data (would need actual institutional trading data)
            institutional_holding_ratio = None
            institutional_net_buy_5d = None
            institutional_net_buy_20d = None
            
            # Placeholder for retail data (would need actual retail trading data)
            retail_concentration = None
            retail_net_buy_5d = None
            retail_net_buy_20d = None
            
            # Placeholder for concentration data (would need actual shareholding data)
            major_holders_ratio = None
            concentration_index = None
            
            return ChipsAnalysis(
                avg_volume_5d=avg_volume_5d,
                avg_volume_20d=avg_volume_20d,
                volume_trend=volume_trend,
                volume_concentration=volume_concentration,
                price_volume_correlation_5d=price_volume_correlation_5d,
                price_volume_correlation_20d=price_volume_correlation_20d,
                avg_price_volume=avg_price_volume,
                price_distribution=price_distribution,
                buying_pressure=buying_pressure,
                selling_pressure=selling_pressure,
                pressure_trend=pressure_trend,
                institutional_holding_ratio=institutional_holding_ratio,
                institutional_net_buy_5d=institutional_net_buy_5d,
                institutional_net_buy_20d=institutional_net_buy_20d,
                retail_concentration=retail_concentration,
                retail_net_buy_5d=retail_net_buy_5d,
                retail_net_buy_20d=retail_net_buy_20d,
                major_holders_ratio=major_holders_ratio,
                concentration_index=concentration_index
            )
            
        except Exception as e:
            logger.error(f"Error performing chips analysis: {str(e)}")
            return None

    def safe_format_result(self, analysis: ChipsAnalysis) -> Dict[str, Any]:
        """Safely format the analysis results.

        Args:
            analysis: Chips analysis results

        Returns:
            Formatted result dictionary
        """
        return {
            "volume_analysis": {
                "average_volume": {
                    "5_day": safe_round(analysis.avg_volume_5d),
                    "20_day": safe_round(analysis.avg_volume_20d)
                },
                "volume_trend": analysis.volume_trend,
                "volume_concentration": safe_round(analysis.volume_concentration)
            },
            "price_volume_analysis": {
                "correlation": {
                    "5_day": safe_round(analysis.price_volume_correlation_5d),
                    "20_day": safe_round(analysis.price_volume_correlation_20d)
                },
                "avg_price_volume": safe_round(analysis.avg_price_volume),
                "price_distribution": {
                    k: safe_round(v) for k, v in analysis.price_distribution.items()
                }
            },
            "pressure_analysis": {
                "buying_pressure": safe_round(analysis.buying_pressure),
                "selling_pressure": safe_round(analysis.selling_pressure),
                "pressure_trend": analysis.pressure_trend
            },
            "institutional_analysis": {
                "holding_ratio": safe_round(analysis.institutional_holding_ratio),
                "net_buy": {
                    "5_day": safe_round(analysis.institutional_net_buy_5d),
                    "20_day": safe_round(analysis.institutional_net_buy_20d)
                }
            },
            "retail_analysis": {
                "concentration": safe_round(analysis.retail_concentration),
                "net_buy": {
                    "5_day": safe_round(analysis.retail_net_buy_5d),
                    "20_day": safe_round(analysis.retail_net_buy_20d)
                }
            },
            "concentration_analysis": {
                "major_holders_ratio": safe_round(analysis.major_holders_ratio),
                "concentration_index": safe_round(analysis.concentration_index)
            }
        }

    @track()
    async def execute(self, input_data: Dict) -> Dict:
        """Execute chips analysis.

        Args:
            input_data: Dictionary containing:
                - symbol: Stock symbol
                - days: Optional number of days for analysis

        Returns:
            Dictionary containing analysis results or error message
        """
        try:
            symbol = input_data.get("symbol")
            days = input_data.get("days", 60)  # Default to 60 days

            if not symbol:
                return {"error": "Stock symbol is required"}

            analysis = await self.analyze_chips(symbol, days)
            
            if analysis is None:
                return {
                    "error": f"Could not perform chips analysis for {symbol}. The stock symbol may be invalid or data may not be available."
                }

            return self.safe_format_result(analysis)

        except Exception as e:
            logger.error(f"Error executing chips analysis: {str(e)}")
            return {"error": f"Chips analysis failed: {str(e)}"} 