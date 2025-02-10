"""Technical analysis agent module.

This module implements agents for performing technical analysis on stock data.
It provides various technical indicators and analysis methods for market data.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
import math

import pandas as pd
import numpy as np
import talib
from opik import track

from tools.core.tool_protocol import Tool
from tools.market_data_fetcher import fetch_market_data
from tools.financial_data import utils
from settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
settings = Settings()


def safe_float(value: Union[float, np.float64, None]) -> Optional[float]:
    """安全地處理浮點數值，處理 NaN 和無限值。

    Args:
        value: 要處理的數值

    Returns:
        處理後的浮點數或 None
    """
    if value is None:
        return None
    if isinstance(value, (float, np.float64)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    return None


@dataclass
class TechnicalIndicator:
    """Technical indicator result with metadata.

    Attributes:
        name: Name of the indicator
        value: Calculated indicator value
        signal: Trading signal (buy, sell, hold)
        metadata: Additional indicator-specific data
    """
    name: str
    value: Optional[float]
    signal: str
    metadata: Dict[str, Any] = None


class TechnicalAnalysisAgent:
    """Agent for performing technical analysis on stock data."""

    def __init__(self, symbol: str):
        """Initialize the technical analysis agent.

        Args:
            symbol: Stock symbol to analyze
        """
        self.symbol = symbol
        self._data: Optional[pd.DataFrame] = None
        self.indicators: Dict[str, TechnicalIndicator] = {}

    async def fetch_data(self, interval: str = "1d", days: int = settings.default_days) -> bool:
        """Fetch market data for analysis.

        Args:
            interval: Data interval (1d, 1wk, 1mo)
            days: Number of days of historical data

        Returns:
            bool: True if data fetch was successful
        """
        try:
            # 確保天數不少於最小需求
            if days < settings.min_days_for_analysis:
                logger.warning(f"Days parameter {days} is too small, using minimum {settings.min_days_for_analysis} days")
                days = settings.min_days_for_analysis

            self._data = fetch_market_data(self.symbol, interval, days)
            
            # 檢查獲取的數據是否足夠
            if self._data is not None and len(self._data) < settings.min_days_for_analysis:
                logger.warning(f"Fetched data ({len(self._data)} days) is less than minimum required ({settings.min_days_for_analysis} days)")
                return False
                
            return self._data is not None
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return False

    def calculate_ma(self, period: int = 20) -> Optional[TechnicalIndicator]:
        """Calculate Moving Average.

        Args:
            period: MA period

        Returns:
            TechnicalIndicator with MA data
        """
        if self._data is None or len(self._data) < period:
            return None

        try:
            ma = talib.MA(self._data["Close"].values, timeperiod=period)
            current_ma = safe_float(ma[-1])
            current_price = safe_float(self._data["Close"].iloc[-1])
            
            if current_ma is None or current_price is None:
                return None

            signal = "hold"
            if current_price > current_ma:
                signal = "buy"
            elif current_price < current_ma:
                signal = "sell"

            return TechnicalIndicator(
                name=f"MA{period}",
                value=current_ma,
                signal=signal,
                metadata={
                    "period": period,
                    "current_price": current_price
                }
            )
        except Exception as e:
            logger.error(f"Error calculating MA: {str(e)}")
            return None

    def calculate_rsi(self, period: int = 14) -> Optional[TechnicalIndicator]:
        """Calculate Relative Strength Index.

        Args:
            period: RSI period

        Returns:
            TechnicalIndicator with RSI data
        """
        if self._data is None or len(self._data) < period:
            return None

        try:
            rsi = talib.RSI(self._data["Close"].values, timeperiod=period)
            current_rsi = safe_float(rsi[-1])
            
            if current_rsi is None:
                return None

            signal = "hold"
            if current_rsi > 70:
                signal = "sell"
            elif current_rsi < 30:
                signal = "buy"

            return TechnicalIndicator(
                name="RSI",
                value=current_rsi,
                signal=signal,
                metadata={
                    "period": period,
                    "overbought": 70,
                    "oversold": 30
                }
            )
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return None

    def calculate_macd(self) -> Optional[TechnicalIndicator]:
        """Calculate MACD indicator.

        Returns:
            TechnicalIndicator with MACD data
        """
        if self._data is None or len(self._data) < 26:
            return None

        try:
            macd, signal, hist = talib.MACD(
                self._data["Close"].values,
                fastperiod=12,
                slowperiod=26,
                signalperiod=9
            )
            
            current_macd = safe_float(macd[-1])
            current_signal = safe_float(signal[-1])
            current_hist = safe_float(hist[-1])
            prev_hist = safe_float(hist[-2]) if len(hist) > 1 else None
            
            if any(v is None for v in [current_macd, current_signal, current_hist, prev_hist]):
                return None

            signal_type = "hold"
            if current_hist > 0 and prev_hist <= 0:
                signal_type = "buy"
            elif current_hist < 0 and prev_hist >= 0:
                signal_type = "sell"

            return TechnicalIndicator(
                name="MACD",
                value=current_macd,
                signal=signal_type,
                metadata={
                    "signal_line": current_signal,
                    "histogram": current_hist
                }
            )
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return None

    def calculate_dmi(self) -> Optional[TechnicalIndicator]:
        """Calculate DMI (Directional Movement Index).

        Returns:
            TechnicalIndicator with DMI data
        """
        if self._data is None or len(self._data) < 14:
            return None

        try:
            plus_di = talib.PLUS_DI(self._data["High"].values, self._data["Low"].values, self._data["Close"].values, timeperiod=14)
            minus_di = talib.MINUS_DI(self._data["High"].values, self._data["Low"].values, self._data["Close"].values, timeperiod=14)
            adx = talib.ADX(self._data["High"].values, self._data["Low"].values, self._data["Close"].values, timeperiod=14)
            
            current_plus_di = safe_float(plus_di[-1])
            current_minus_di = safe_float(minus_di[-1])
            current_adx = safe_float(adx[-1])
            
            if any(v is None for v in [current_plus_di, current_minus_di, current_adx]):
                return None

            signal = "hold"
            if current_plus_di > current_minus_di and current_adx > 25:
                signal = "buy"
            elif current_minus_di > current_plus_di and current_adx > 25:
                signal = "sell"

            return TechnicalIndicator(
                name="DMI",
                value=current_adx,
                signal=signal,
                metadata={
                    "plus_di": current_plus_di,
                    "minus_di": current_minus_di,
                    "adx": current_adx
                }
            )
        except Exception as e:
            logger.error(f"Error calculating DMI: {str(e)}")
            return None

    def calculate_willr(self) -> Optional[TechnicalIndicator]:
        """Calculate Williams %R.

        Returns:
            TechnicalIndicator with Williams %R data
        """
        if self._data is None or len(self._data) < 14:
            return None

        try:
            willr = talib.WILLR(self._data["High"].values, self._data["Low"].values, self._data["Close"].values, timeperiod=14)
            current_willr = safe_float(willr[-1])
            
            if current_willr is None:
                return None

            signal = "hold"
            if current_willr > -20:
                signal = "sell"
            elif current_willr < -80:
                signal = "buy"

            return TechnicalIndicator(
                name="WILLR",
                value=current_willr,
                signal=signal,
                metadata={
                    "overbought": -20,
                    "oversold": -80
                }
            )
        except Exception as e:
            logger.error(f"Error calculating Williams %R: {str(e)}")
            return None

    def calculate_volume_indicators(self) -> Dict[str, Optional[TechnicalIndicator]]:
        """Calculate volume-based indicators.

        Returns:
            Dict of volume indicators
        """
        if self._data is None or len(self._data) < 12:
            return {}

        try:
            volume_indicators = {}
            
            # Volume Rate of Change (VROC)
            volume = self._data["Volume"].values
            volume_series = pd.Series(volume)
            vroc = volume_series.pct_change(periods=12) * 100
            current_vroc = safe_float(vroc.iloc[-1])
            
            if current_vroc is not None:
                volume_indicators["VROC"] = TechnicalIndicator(
                    name="VROC",
                    value=current_vroc,
                    signal="hold",  # VROC typically used as confirmation
                    metadata={
                        "period": 12
                    }
                )
            
            # Price Volume Trend (PVT)
            close = self._data["Close"].values
            close_series = pd.Series(close)
            price_change = close_series.pct_change()
            pvt_series = (price_change * volume).cumsum()
            current_pvt = safe_float(pvt_series.iloc[-1])
            prev_pvt = safe_float(pvt_series.iloc[-2]) if len(pvt_series) > 1 else None
            
            if current_pvt is not None and prev_pvt is not None:
                signal = "hold"
                if current_pvt > prev_pvt:
                    signal = "buy"
                elif current_pvt < prev_pvt:
                    signal = "sell"
                    
                volume_indicators["PVT"] = TechnicalIndicator(
                    name="PVT",
                    value=current_pvt,
                    signal=signal,
                    metadata={
                        "previous_value": prev_pvt
                    }
                )
            
            return volume_indicators
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {str(e)}")
            return {}

    async def analyze(self) -> Dict[str, TechnicalIndicator]:
        """Perform technical analysis.

        Returns:
            Dict of technical indicators
        """
        if not await self.fetch_data():
            return {}

        # Calculate indicators
        self.indicators["MA5"] = self.calculate_ma(5)
        self.indicators["MA10"] = self.calculate_ma(10)
        self.indicators["MA20"] = self.calculate_ma(20)
        self.indicators["MA60"] = self.calculate_ma(60)
        self.indicators["RSI5"] = self.calculate_rsi(5)
        self.indicators["RSI14"] = self.calculate_rsi(14)
        self.indicators["MACD"] = self.calculate_macd()
        self.indicators["DMI"] = self.calculate_dmi()
        self.indicators["WILLR"] = self.calculate_willr()
        
        # Add volume indicators
        volume_indicators = self.calculate_volume_indicators()
        self.indicators.update(volume_indicators)

        return self.indicators

    def get_analysis_summary(self) -> str:
        """Get summary of technical analysis results.

        Returns:
            Summary string
        """
        if not self.indicators:
            return "No analysis results available"

        summary = []
        summary.append(f"Technical Analysis Summary for {self.symbol}")
        summary.append("-" * 50)

        for name, indicator in self.indicators.items():
            if indicator:
                summary.append(f"{name}:")
                summary.append(f"  Value: {indicator.value:.2f}")
                summary.append(f"  Signal: {indicator.signal.upper()}")
                if indicator.metadata:
                    for key, value in indicator.metadata.items():
                        if isinstance(value, float):
                            summary.append(f"  {key}: {value:.2f}")
                        else:
                            summary.append(f"  {key}: {value}")
                summary.append("")

        return "\n".join(summary)


class TechnicalAnalysisTool(Tool):
    """Tool for performing technical analysis."""

    def __init__(self):
        """Initialize the technical analysis tool."""
        super().__init__()
        self.agents: Dict[str, TechnicalAnalysisAgent] = {}

    async def execute(self, params: Dict[str, Any]) -> str:
        """Execute technical analysis.

        Args:
            params: Parameters including symbol

        Returns:
            Analysis summary
        """
        symbol = params.get("symbol")
        if not symbol:
            raise ValueError("Symbol is required")

        if not utils.is_valid_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")

        if symbol not in self.agents:
            self.agents[symbol] = TechnicalAnalysisAgent(symbol)

        await self.agents[symbol].analyze()
        return self.agents[symbol].get_analysis_summary() 