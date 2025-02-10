"""Chips analysis agent module.

This module implements agents for performing chips analysis on stock data.
It provides various chips indicators and analysis methods for market data.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import os
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd
import yfinance as yf
from tools.llm_api import aquery_llm, Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChipsIndicator:
    """Chips indicator result with metadata."""
    name: str
    value: float
    signal: str  # buy, sell, or hold
    metadata: Dict[str, Any]

class MarketDataFetcher:
    """Handles fetching and processing market data."""
    
    @staticmethod
    def _calculate_basic_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate basic price and volume metrics."""
        df['PriceChange'] = df['Close'].pct_change()
        df['VolumeChange'] = df['Volume'].pct_change()
        
        # Moving averages
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['VMA5'] = df['Volume'].rolling(5).mean()
        df['VMA20'] = df['Volume'].rolling(20).mean()
        
        return df
    
    @staticmethod
    async def fetch_data(symbol: str) -> Optional[pd.DataFrame]:
        """Fetch market data for analysis."""
        try:
            stock = yf.Ticker(f"{symbol}.TW")
            df = stock.history(period="60d")
            if df.empty:
                logger.warning(f"No data found for symbol {symbol}")
                return None
                
            return MarketDataFetcher._calculate_basic_metrics(df)
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None

class ChipsAnalysisAgent:
    """Agent for performing chips analysis on stock data."""

    def __init__(self, symbol: str, model_name: str = "gpt-4o"):
        self.symbol = symbol
        self._data: Optional[pd.DataFrame] = None
        self.model_name = model_name
        self.system_prompt = self._load_system_prompt()
        self.indicators: Dict[str, ChipsIndicator] = {}

    def _load_system_prompt(self) -> Optional[str]:
        """Load the system prompt from file."""
        try:
            prompt_path = os.path.join("prompts", "chip_instruction.md")
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load chips analysis framework: {str(e)}")
            return None

    def calculate_volume_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate volume-based indicator."""
        if self._data is None:
            return None

        avg_volume_5d = self._data['VMA5'].iloc[-1]
        avg_volume_20d = self._data['VMA20'].iloc[-1]
        
        # Determine volume trend
        if avg_volume_5d > avg_volume_20d * 1.1:
            trend = "Increasing"
            signal = "buy"
        elif avg_volume_5d < avg_volume_20d * 0.9:
            trend = "Decreasing"
            signal = "sell"
        else:
            trend = "Stable"
            signal = "hold"

        return ChipsIndicator(
            name="Volume",
            value=avg_volume_5d / avg_volume_20d,
            signal=signal,
            metadata={
                "avg_volume_5d": avg_volume_5d,
                "avg_volume_20d": avg_volume_20d,
                "trend": trend
            }
        )

    def calculate_price_volume_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate price-volume correlation indicator."""
        if self._data is None:
            return None

        corr_5d = self._data['PriceChange'].tail(5).corr(self._data['VolumeChange'].tail(5))
        
        # Determine signal based on correlation
        if corr_5d > 0.5:
            signal = "buy"
        elif corr_5d < -0.5:
            signal = "sell"
        else:
            signal = "hold"

        return ChipsIndicator(
            name="PriceVolume",
            value=corr_5d,
            signal=signal,
            metadata={
                "correlation_5d": corr_5d,
                "correlation_20d": self._data['PriceChange'].tail(20).corr(self._data['VolumeChange'].tail(20))
            }
        )

    async def analyze(self) -> Dict[str, ChipsIndicator]:
        """Perform chips analysis."""
        try:
            # Fetch market data
            self._data = await MarketDataFetcher.fetch_data(self.symbol)
            if self._data is None:
                return {}

            # Calculate indicators
            self.indicators = {
                "volume": self.calculate_volume_indicator(),
                "price_volume": self.calculate_price_volume_indicator()
            }

            # Get LLM analysis if system prompt is available
            if self.system_prompt:
                llm_analysis = await self._get_llm_analysis(self.indicators)
                self.indicators.update(llm_analysis)

            return {k: v for k, v in self.indicators.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {}

    async def _get_llm_analysis(self, indicators: Dict[str, ChipsIndicator]) -> Dict[str, ChipsIndicator]:
        """Get LLM analysis of the indicators."""
        try:
            # Prepare data for LLM
            data = {
                "symbol": self.symbol,
                "date": self._data.index[-1].strftime("%Y-%m-%d"),
                "indicators": {
                    name: {
                        "value": ind.value,
                        "signal": ind.signal,
                        "metadata": ind.metadata
                    } for name, ind in indicators.items()
                },
                "price_data": {
                    "current": float(self._data["Close"].iloc[-1]),
                    "change": float(self._data["Close"].iloc[-1] - self._data["Close"].iloc[-2]),
                    "volume": float(self._data["Volume"].iloc[-1])
                }
            }
            
            # Get LLM response
            _, llm_result = await aquery_llm(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Analyze this data: {json.dumps(data)}"}
                ],
                model=self.model_name,
                json_mode=True
            )
            
            # Create indicator from LLM analysis
            analysis = json.loads(llm_result["content"])
            return {
                "overall": ChipsIndicator(
                    name="overall",
                    value=analysis["confidence"],
                    signal=analysis["signal"],
                    metadata={"analysis": analysis["analysis"]}
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting LLM analysis: {str(e)}")
            return {}

    def get_analysis_summary(self) -> str:
        """Generate a readable summary of the analysis."""
        if not self.indicators:
            return "No analysis data available"

        summary = []
        
        # Add volume analysis
        if vol := self.indicators.get("volume"):
            summary.append(
                f"Volume Analysis: {vol.signal.upper()}\n"
                f"- 5-Day Average: {vol.metadata['avg_volume_5d']:,.0f}\n"
                f"- 20-Day Average: {vol.metadata['avg_volume_20d']:,.0f}\n"
                f"- Trend: {vol.metadata['trend']}"
            )
        
        # Add price-volume analysis
        if pv := self.indicators.get("price_volume"):
            summary.append(
                f"\nPrice-Volume Analysis: {pv.signal.upper()}\n"
                f"- 5-Day Correlation: {pv.metadata['correlation_5d']:.2f}\n"
                f"- 20-Day Correlation: {pv.metadata['correlation_20d']:.2f}"
            )
        
        # Add overall assessment
        if overall := self.indicators.get("overall"):
            summary.extend([
                f"\nOverall Assessment: {overall.signal.upper()}\n"
                f"Confidence: {overall.value:.2f}\n"
                f"Analysis: {overall.metadata['analysis']}"
            ])
            
        return "\n".join(summary)


async def main():
    """Test function."""
    symbol = "2330"
    
    try:
        agent = ChipsAnalysisAgent(symbol)
        indicators = await agent.analyze()
        
        if indicators:
            logger.info("\nAnalysis Summary:")
            logger.info("=" * 50)
            logger.info(agent.get_analysis_summary())
        else:
            logger.warning("No analysis data available.")
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 