"""Technical Analysis Tool using TA-Lib.

This module implements technical analysis functionality using TA-Lib,
following the framework defined in TA_instruction.md.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import talib
from tools.core.tool_protocol import Tool
from tools.market_data_fetcher import fetch_market_data

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TechnicalAnalysis:
    """Technical analysis results container."""
    
    # Trend Analysis
    trend: str
    sma_50: float
    sma_200: float
    ema_20: float
    
    # Momentum Indicators
    rsi: float
    macd: tuple[float, float, float]  # macd, signal, hist
    stoch: tuple[float, float]  # slowk, slowd
    
    # Volatility Indicators
    atr: float
    bbands: tuple[float, float, float]  # upper, middle, lower
    
    # Volume Indicators
    obv: float
    
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

    async def analyze_stock(self, symbol: str, days: int = 200) -> Optional[TechnicalAnalysis]:
        """Perform technical analysis on a stock.
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data to analyze
            
        Returns:
            TechnicalAnalysis object containing the analysis results,
            or None if data is not available
        """
        try:
            # Fetch historical data
            df = await fetch_market_data(symbol, days=days)
            
            if df is None:
                logger.error(f"No market data available for {symbol}")
                return None
                
            # Convert to numpy arrays for TA-Lib
            close = df['close'].astype(float).to_numpy()
            high = df['high'].astype(float).to_numpy()
            low = df['low'].astype(float).to_numpy()
            volume = df['volume'].astype(float).to_numpy()
            open = df['open'].astype(float).to_numpy()
            
            # Calculate moving averages
            sma_50 = talib.SMA(close, timeperiod=50)[-1]
            sma_200 = talib.SMA(close, timeperiod=200)[-1]
            ema_20 = talib.EMA(close, timeperiod=20)[-1]
            
            # Determine trend
            trend = "Uptrend" if sma_50 > sma_200 else "Downtrend"
            if abs(sma_50 - sma_200) / sma_200 < 0.02:
                trend = "Sideways"
            
            # Calculate momentum indicators
            rsi = talib.RSI(close, timeperiod=14)[-1]
            macd, signal, hist = talib.MACD(close)
            macd_vals = (macd[-1], signal[-1], hist[-1])
            slowk, slowd = talib.STOCH(high, low, close)
            stoch_vals = (slowk[-1], slowd[-1])
            
            # Calculate volatility indicators
            atr = talib.ATR(high, low, close, timeperiod=14)[-1]
            upper, middle, lower = talib.BBANDS(close)
            bband_vals = (upper[-1], middle[-1], lower[-1])
            
            # Calculate volume indicators
            obv = talib.OBV(close, volume)[-1]
            
            # Pattern recognition
            patterns = []
            pattern_functions = [
                (talib.CDLENGULFING, "Engulfing"),
                (talib.CDLDOJI, "Doji"),
                (talib.CDLHAMMER, "Hammer"),
                (talib.CDLHARAMI, "Harami")
            ]
            
            for func, name in pattern_functions:
                result = func(open, high, low, close)
                if result[-1] != 0:
                    patterns.append(f"{name} {'Bullish' if result[-1] > 0 else 'Bearish'}")
            
            # Calculate support/resistance levels using recent lows/highs
            window = 20
            support_levels = sorted(list(set([round(x, 2) for x in 
                                            pd.Series(low).rolling(window).min().dropna().tail(3)])))
            resistance_levels = sorted(list(set([round(x, 2) for x in 
                                               pd.Series(high).rolling(window).max().dropna().tail(3)])))
            
            return TechnicalAnalysis(
                trend=trend,
                sma_50=sma_50,
                sma_200=sma_200,
                ema_20=ema_20,
                rsi=rsi,
                macd=macd_vals,
                stoch=stoch_vals,
                atr=atr,
                bbands=bband_vals,
                obv=obv,
                patterns=patterns,
                support_levels=support_levels,
                resistance_levels=resistance_levels
            )
            
        except Exception as e:
            logger.error(f"Error performing technical analysis: {str(e)}")
            return None

    async def execute(self, input_data: Dict) -> Dict:
        """Execute the technical analysis tool.
        
        Args:
            input_data: Dictionary containing:
                - symbol: Stock symbol to analyze
                - days: Optional number of days of historical data
                
        Returns:
            Dictionary containing the technical analysis results
            or error message if analysis fails
        """
        try:
            symbol = input_data.get("symbol")
            days = input_data.get("days", 200)
            
            if not symbol:
                return {"error": "Stock symbol is required"}
                
            analysis = await self.analyze_stock(symbol, days)
            
            if analysis is None:
                return {
                    "error": f"Could not perform technical analysis for {symbol}. "
                            "The stock symbol may be invalid or data may not be available."
                }
            
            # Format the results
            return {
                "trend_analysis": {
                    "overall_trend": analysis.trend,
                    "moving_averages": {
                        "SMA_50": round(analysis.sma_50, 2),
                        "SMA_200": round(analysis.sma_200, 2),
                        "EMA_20": round(analysis.ema_20, 2)
                    }
                },
                "momentum_indicators": {
                    "RSI": round(analysis.rsi, 2),
                    "MACD": {
                        "macd": round(analysis.macd[0], 2),
                        "signal": round(analysis.macd[1], 2),
                        "histogram": round(analysis.macd[2], 2)
                    },
                    "Stochastic": {
                        "slowK": round(analysis.stoch[0], 2),
                        "slowD": round(analysis.stoch[1], 2)
                    }
                },
                "volatility_indicators": {
                    "ATR": round(analysis.atr, 2),
                    "Bollinger_Bands": {
                        "upper": round(analysis.bbands[0], 2),
                        "middle": round(analysis.bbands[1], 2),
                        "lower": round(analysis.bbands[2], 2)
                    }
                },
                "volume_indicators": {
                    "OBV": analysis.obv
                },
                "patterns": analysis.patterns,
                "support_resistance": {
                    "support_levels": analysis.support_levels,
                    "resistance_levels": analysis.resistance_levels
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing technical analysis tool: {str(e)}")
            return {"error": f"Technical analysis failed: {str(e)}"} 