"""Chip analysis agent module.

This module implements agents for performing chip analysis on stock data.
It provides various chip indicators and analysis methods for market data.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
import math

import pandas as pd
import numpy as np
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
class ChipIndicator:
    """Chip indicator result with metadata.

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


class ChipAnalysisAgent:
    """Agent for performing chip analysis on stock data."""

    def __init__(self, symbol: str):
        """Initialize the chip analysis agent.

        Args:
            symbol: Stock symbol to analyze
        """
        self.symbol = symbol
        self._data: Optional[pd.DataFrame] = None
        self.indicators: Dict[str, ChipIndicator] = {}

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

    def calculate_volume_ratio(self, period: int = 5) -> Optional[ChipIndicator]:
        """Calculate Volume Ratio (成交量比率).

        Args:
            period: Period for volume ratio calculation

        Returns:
            ChipIndicator with volume ratio data
        """
        if self._data is None or len(self._data) < period:
            return None

        try:
            volume = self._data["Volume"].values
            avg_volume = np.mean(volume[-period:])
            current_volume = volume[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            signal = "hold"
            if volume_ratio > 2.0:
                signal = "buy"
            elif volume_ratio < 0.5:
                signal = "sell"

            return ChipIndicator(
                name="Volume Ratio",
                value=volume_ratio,
                signal=signal,
                metadata={
                    "period": period,
                    "current_volume": current_volume,
                    "average_volume": avg_volume
                }
            )
        except Exception as e:
            logger.error(f"Error calculating volume ratio: {str(e)}")
            return None

    def calculate_concentration_ratio(self, period: int = 5) -> Optional[ChipIndicator]:
        """Calculate Concentration Ratio (集中度).

        Args:
            period: Period for concentration calculation

        Returns:
            ChipIndicator with concentration data
        """
        if self._data is None or len(self._data) < period:
            return None

        try:
            volume = self._data["Volume"].values[-period:]
            price = self._data["Close"].values[-period:]
            
            # 計算成交金額
            turnover = volume * price
            
            # 計算集中度 (最大成交金額 / 平均成交金額)
            max_turnover = np.max(turnover)
            avg_turnover = np.mean(turnover)
            concentration = max_turnover / avg_turnover if avg_turnover > 0 else 0
            
            signal = "hold"
            if concentration > 2.0:
                signal = "buy"
            elif concentration < 0.5:
                signal = "sell"

            return ChipIndicator(
                name="Concentration",
                value=concentration,
                signal=signal,
                metadata={
                    "period": period,
                    "max_turnover": max_turnover,
                    "avg_turnover": avg_turnover
                }
            )
        except Exception as e:
            logger.error(f"Error calculating concentration ratio: {str(e)}")
            return None

    def calculate_turnover_rate(self, period: int = 5) -> Optional[ChipIndicator]:
        """Calculate Turnover Rate (周轉率).

        Args:
            period: Period for turnover rate calculation

        Returns:
            ChipIndicator with turnover rate data
        """
        if self._data is None or len(self._data) < period:
            return None

        try:
            volume = self._data["Volume"].values[-period:]
            total_shares = 100000000  # 假設總股數，實際應從其他來源獲取
            
            # 計算周轉率
            turnover_rate = np.sum(volume) / total_shares * 100
            
            signal = "hold"
            if turnover_rate > 15:
                signal = "buy"
            elif turnover_rate < 5:
                signal = "sell"

            return ChipIndicator(
                name="Turnover Rate",
                value=turnover_rate,
                signal=signal,
                metadata={
                    "period": period,
                    "total_volume": np.sum(volume),
                    "total_shares": total_shares
                }
            )
        except Exception as e:
            logger.error(f"Error calculating turnover rate: {str(e)}")
            return None

    def calculate_institutional_ratio(self) -> Optional[ChipIndicator]:
        """Calculate Institutional Ratio (法人比率).

        Returns:
            ChipIndicator with institutional ratio data
        """
        if self._data is None:
            return None

        try:
            # 這裡需要額外的法人資料，目前使用模擬數據
            inst_volume = self._data["Volume"].values[-1] * 0.4  # 假設40%是法人
            total_volume = self._data["Volume"].values[-1]
            
            inst_ratio = inst_volume / total_volume if total_volume > 0 else 0
            
            signal = "hold"
            if inst_ratio > 0.6:
                signal = "buy"
            elif inst_ratio < 0.2:
                signal = "sell"

            return ChipIndicator(
                name="Institutional Ratio",
                value=inst_ratio,
                signal=signal,
                metadata={
                    "inst_volume": inst_volume,
                    "total_volume": total_volume
                }
            )
        except Exception as e:
            logger.error(f"Error calculating institutional ratio: {str(e)}")
            return None

    async def analyze(self) -> Dict[str, ChipIndicator]:
        """Perform chip analysis.

        Returns:
            Dict of chip indicators
        """
        if not await self.fetch_data():
            return {}

        # Calculate indicators
        self.indicators["VolumeRatio"] = self.calculate_volume_ratio(5)
        self.indicators["Concentration"] = self.calculate_concentration_ratio(5)
        self.indicators["TurnoverRate"] = self.calculate_turnover_rate(5)
        self.indicators["InstitutionalRatio"] = self.calculate_institutional_ratio()

        return self.indicators

    def get_analysis_summary(self) -> str:
        """Get summary of chip analysis results.

        Returns:
            Summary string
        """
        if not self.indicators:
            return "No analysis results available"

        summary = []
        summary.append(f"Chip Analysis Summary for {self.symbol}")
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


class ChipAnalysisTool(Tool):
    """Tool for performing chip analysis."""

    def __init__(self):
        """Initialize the chip analysis tool."""
        super().__init__()
        self.agents: Dict[str, ChipAnalysisAgent] = {}

    async def execute(self, params: Dict[str, Any]) -> str:
        """Execute chip analysis.

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
            self.agents[symbol] = ChipAnalysisAgent(symbol)

        await self.agents[symbol].analyze()
        return self.agents[symbol].get_analysis_summary() 