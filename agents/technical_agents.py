"""Technical analysis agent module.

This module implements agents for performing technical analysis on stock data.
It provides various technical indicators and analysis methods for market data.
"""

import logging
from typing import Any, Dict, Optional
import pandas as pd
import talib
import yfinance as yf

from .base import BaseAgent, AnalysisResult

logger = logging.getLogger(__name__)

class TechnicalAgent(BaseAgent):
    """Agent specialized in technical analysis."""
    
    def __init__(self, provider: str, model_name: str):
        with open("prompts/technical_analysis_prompt.txt", "r") as file:
            system_prompt = file.read()
        super().__init__(provider, model_name, system_prompt)
        
    async def _fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch market data for technical analysis.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame with market data
        """
        # Add .TW suffix for Taiwan stocks
        symbol = f"{symbol}.TW"
        
        try:
            # Fetch data using yfinance
            stock = yf.Ticker(symbol)
            df = stock.history(period="1y")
            
            if df.empty:
                raise ValueError(f"No data found for symbol {symbol}")
                
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
            
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators.
        
        Args:
            df: DataFrame with market data
            
        Returns:
            Dictionary of calculated indicators
        """
        try:
            indicators = {}
            
            # Moving Averages
            sma_series = pd.Series(talib.SMA(df["Close"], timeperiod=5))
            indicators["MA5"] = sma_series.iloc[-1]
            
            sma_series = pd.Series(talib.SMA(df["Close"], timeperiod=20))
            indicators["MA20"] = sma_series.iloc[-1]
            
            sma_series = pd.Series(talib.SMA(df["Close"], timeperiod=60))
            indicators["MA60"] = sma_series.iloc[-1]
            
            # RSI
            rsi_series = pd.Series(talib.RSI(df["Close"], timeperiod=14))
            indicators["RSI"] = rsi_series.iloc[-1]
            
            # MACD
            macd, signal, _ = talib.MACD(df["Close"])
            indicators["MACD"] = pd.Series(macd).iloc[-1]
            indicators["MACD_Signal"] = pd.Series(signal).iloc[-1]
            
            # Bollinger Bands
            upper, middle, lower = talib.BBANDS(df["Close"])
            indicators["BB_Upper"] = pd.Series(upper).iloc[-1]
            indicators["BB_Middle"] = pd.Series(middle).iloc[-1]
            indicators["BB_Lower"] = pd.Series(lower).iloc[-1]
            
            # Volume Indicators
            obv_series = pd.Series(talib.OBV(df["Close"], df["Volume"]))
            indicators["OBV"] = obv_series.iloc[-1]
            
            # Current Price
            indicators["Current_Price"] = df["Close"].iloc[-1]
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise
        
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Perform technical analysis.
        
        Args:
            query: User query
            **kwargs: Additional arguments including company name
            
        Returns:
            Analysis result
        """
        try:
            company = kwargs.get('company')
            if not company:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Company name required for technical analysis"
                )
                
            # Clear previous conversation
            self.clear_history()
            
            # Add user query first
            self.add_message(
                "user",
                f"Analyze technical aspects of {company}: {query}"
            )
            
            # Fetch and analyze data
            df = await self._fetch_data(company)
            indicators = self._calculate_indicators(df)
            
            # Format analysis message
            analysis_msg = f"""
Technical Analysis Data:

Current Price: {indicators['Current_Price']:.2f}

Moving Averages:
- MA5: {indicators['MA5']:.2f}
- MA20: {indicators['MA20']:.2f}
- MA60: {indicators['MA60']:.2f}

Momentum:
- RSI (14): {indicators['RSI']:.2f}
- MACD: {indicators['MACD']:.2f}
- MACD Signal: {indicators['MACD_Signal']:.2f}

Volatility:
- Bollinger Bands:
  * Upper: {indicators['BB_Upper']:.2f}
  * Middle: {indicators['BB_Middle']:.2f}
  * Lower: {indicators['BB_Lower']:.2f}

Volume:
- OBV: {indicators['OBV']:.0f}
"""
            
            # Add analysis to conversation
            self.add_message(
                "user",
                "Based on the technical data below, provide a clear and comprehensive technical analysis. "
                "Focus on price trends, key indicators, and chart patterns. "
                "Highlight any significant signals or potential reversal points. "
                "Provide specific levels and values where relevant.\n\n" + analysis_msg
            )
            
            # Get interpretation from model
            response, _ = await self.call_model()
            
            return AnalysisResult(
                success=True,
                content=response.choices[0].message.content,
                metadata={
                    "company": company,
                    "analysis_type": "technical",
                    "indicators": indicators
                }
            )
            
        except Exception as e:
            logger.error(f"Technical analysis error: {str(e)}")
            return AnalysisResult(
                success=False,
                content="",
                error=str(e)
            ) 