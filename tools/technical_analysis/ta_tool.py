"""Technical Analysis Tool using TA-Lib.

This module implements technical analysis functionality using TA-Lib,
following the framework defined in TA_instruction.md.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any

import numpy as np
import pandas as pd
import talib
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
class TechnicalAnalysis:
    """Technical analysis results container."""
    
    # Trend Analysis
    trend: str
    sma_5: Optional[float]
    sma_10: Optional[float]
    sma_20: Optional[float]
    sma_60: Optional[float]
    sma_120: Optional[float]
    sma_240: Optional[float]
    tema_20: Optional[float]
    
    # Momentum Indicators
    rsi_5: Optional[float]
    rsi_14: Optional[float]
    macd: tuple[Optional[float], Optional[float], Optional[float]]  # macd, signal, hist
    stoch: tuple[Optional[float], Optional[float]]  # slowk, slowd
    willr: Optional[float]  # Williams %R
    
    # Trend Direction
    dmi: tuple[Optional[float], Optional[float], Optional[float]]  # plus_di, minus_di, adx
    
    # Volatility Indicators
    bbands: tuple[Optional[float], Optional[float], Optional[float]]  # upper, middle, lower
    
    # Volume Indicators
    obv: Optional[float]
    vroc: Optional[float]  # Volume Rate of Change
    pvt: Optional[float]  # Price Volume Trend
    
    # Pattern Recognition
    patterns: List[str]
    
    # Support/Resistance
    support_levels: List[float]
    resistance_levels: List[float]


class TATool(Tool):
    """Technical Analysis tool implementation."""

    def __init__(self):
        """Initialize the TA tool."""
        super().__init__()

    async def analyze_stock(self, symbol: str, days: int = 60) -> Optional[TechnicalAnalysis]:
        """Perform technical analysis on a stock.
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data to analyze
            
        Returns:
            TechnicalAnalysis object containing the analysis results,
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

            # Convert to numpy arrays for TA-Lib
            close = df['close'].astype(float).to_numpy()
            high = df['high'].astype(float).to_numpy()
            low = df['low'].astype(float).to_numpy()
            volume = df['volume'].astype(float).to_numpy()
            open = df['open'].astype(float).to_numpy()
            
            # Calculate moving averages
            sma_5 = safe_float(talib.SMA(close, timeperiod=5)[-1])
            sma_10 = safe_float(talib.SMA(close, timeperiod=10)[-1])
            sma_20 = safe_float(talib.SMA(close, timeperiod=20)[-1])
            sma_60 = safe_float(talib.SMA(close, timeperiod=60)[-1])
            sma_120 = safe_float(talib.SMA(close, timeperiod=120)[-1])
            sma_240 = safe_float(talib.SMA(close, timeperiod=240)[-1])
            tema_20 = safe_float(talib.TEMA(close, timeperiod=20)[-1])
            
            # Determine trend using multiple MAs
            trend = "Sideways"
            if sma_20 is not None and sma_60 is not None:
                if abs(sma_20 - sma_60) / sma_60 < 0.02:
                    trend = "Sideways"
                else:
                    trend = "Uptrend" if sma_20 > sma_60 else "Downtrend"
            
            # Calculate momentum indicators
            rsi_5 = safe_float(talib.RSI(close, timeperiod=5)[-1])
            rsi_14 = safe_float(talib.RSI(close, timeperiod=14)[-1])
            macd, signal, hist = talib.MACD(close)
            macd_vals = (safe_float(macd[-1]), safe_float(signal[-1]), safe_float(hist[-1]))
            slowk, slowd = talib.STOCH(high, low, close)
            stoch_vals = (safe_float(slowk[-1]), safe_float(slowd[-1]))
            willr = safe_float(talib.WILLR(high, low, close, timeperiod=14)[-1])
            
            # Calculate DMI
            plus_di = safe_float(talib.PLUS_DI(high, low, close, timeperiod=14)[-1])
            minus_di = safe_float(talib.MINUS_DI(high, low, close, timeperiod=14)[-1])
            adx = safe_float(talib.ADX(high, low, close, timeperiod=14)[-1])
            dmi_vals = (plus_di, minus_di, adx)
            
            # Calculate volatility indicators
            upper, middle, lower = talib.BBANDS(close)
            bband_vals = (safe_float(upper[-1]), safe_float(middle[-1]), safe_float(lower[-1]))
            
            # Calculate volume indicators
            obv = safe_float(talib.OBV(close, volume)[-1])
            
            # Calculate VROC (Volume Rate of Change)
            volume_roc = pd.Series(volume).pct_change(periods=12) * 100
            vroc = safe_float(volume_roc.iloc[-1])
            
            # Calculate PVT (Price Volume Trend)
            close_series = pd.Series(close)
            price_change = close_series.pct_change()
            pvt_series = (price_change * volume).cumsum()
            pvt = safe_float(pvt_series.iloc[-1])
            
            # Pattern recognition
            patterns = []
            pattern_functions = [
                (talib.CDLENGULFING, "Engulfing"),
                (talib.CDLDOJI, "Doji"),
                (talib.CDLHAMMER, "Hammer"),
                (talib.CDLMORNINGSTAR, "Morning Star"),
                (talib.CDLEVENINGSTAR, "Evening Star")
            ]
            
            for func, name in pattern_functions:
                result = func(open, high, low, close)
                if result[-1] != 0:
                    patterns.append(f"{name} {'Bullish' if result[-1] > 0 else 'Bearish'}")
            
            # Calculate support/resistance levels
            window = 20
            support_levels = []
            resistance_levels = []
            
            try:
                support_levels = sorted(list(set([
                    round(x, 2) for x in pd.Series(low).rolling(window).min().dropna().tail(3)
                    if not math.isnan(x) and not math.isinf(x)
                ])))
                resistance_levels = sorted(list(set([
                    round(x, 2) for x in pd.Series(high).rolling(window).max().dropna().tail(3)
                    if not math.isnan(x) and not math.isinf(x)
                ])))
            except Exception as e:
                logger.warning(f"Error calculating support/resistance levels: {str(e)}")
            
            return TechnicalAnalysis(
                trend=trend,
                sma_5=sma_5,
                sma_10=sma_10,
                sma_20=sma_20,
                sma_60=sma_60,
                sma_120=sma_120,
                sma_240=sma_240,
                tema_20=tema_20,
                rsi_5=rsi_5,
                rsi_14=rsi_14,
                macd=macd_vals,
                stoch=stoch_vals,
                willr=willr,
                dmi=dmi_vals,
                bbands=bband_vals,
                obv=obv,
                vroc=vroc,
                pvt=pvt,
                patterns=patterns,
                support_levels=support_levels,
                resistance_levels=resistance_levels
            )
            
        except Exception as e:
            logger.error(f"Error performing technical analysis: {str(e)}")
            return None

    def safe_format_result(self, analysis: TechnicalAnalysis) -> Dict[str, Any]:
        """Safely format the analysis results.

        Args:
            analysis: Technical analysis results

        Returns:
            Formatted result dictionary
        """
        return {
            "trend_analysis": {
                "overall_trend": analysis.trend,
                "moving_averages": {
                    "SMA_5": safe_round(analysis.sma_5),
                    "SMA_10": safe_round(analysis.sma_10),
                    "SMA_20": safe_round(analysis.sma_20),
                    "SMA_60": safe_round(analysis.sma_60),
                    "SMA_120": safe_round(analysis.sma_120),
                    "SMA_240": safe_round(analysis.sma_240),
                    "TEMA_20": safe_round(analysis.tema_20)
                }
            },
            "momentum_indicators": {
                "RSI_5": safe_round(analysis.rsi_5),
                "RSI_14": safe_round(analysis.rsi_14),
                "MACD": {
                    "macd": safe_round(analysis.macd[0]),
                    "signal": safe_round(analysis.macd[1]),
                    "histogram": safe_round(analysis.macd[2])
                },
                "Stochastic": {
                    "slowK": safe_round(analysis.stoch[0]),
                    "slowD": safe_round(analysis.stoch[1])
                },
                "Williams_R": safe_round(analysis.willr)
            },
            "trend_direction": {
                "DMI": {
                    "plus_di": safe_round(analysis.dmi[0]),
                    "minus_di": safe_round(analysis.dmi[1]),
                    "adx": safe_round(analysis.dmi[2])
                }
            },
            "volatility_indicators": {
                "Bollinger_Bands": {
                    "upper": safe_round(analysis.bbands[0]),
                    "middle": safe_round(analysis.bbands[1]),
                    "lower": safe_round(analysis.bbands[2])
                }
            },
            "volume_indicators": {
                "OBV": analysis.obv,
                "VROC": analysis.vroc,
                "PVT": analysis.pvt
            },
            "patterns": analysis.patterns,
            "support_resistance": {
                "support_levels": analysis.support_levels,
                "resistance_levels": analysis.resistance_levels
            }
        }

    @track()
    async def execute(self, input_data: Dict) -> Dict:
        """Execute technical analysis.

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

            analysis = await self.analyze_stock(symbol, days)
            
            if analysis is None:
                return {
                    "error": f"Could not perform technical analysis for {symbol}. The stock symbol may be invalid or data may not be available."
                }

            return self.safe_format_result(analysis)

        except Exception as e:
            logger.error(f"Error executing technical analysis: {str(e)}")
            return {"error": f"Technical analysis failed: {str(e)}"} 