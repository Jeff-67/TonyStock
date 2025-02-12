"""Technical analysis agent module.

This module implements agents for performing technical analysis on stock data.
It provides various technical indicators and analysis methods for market data.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from litellm import Message
import pandas as pd
import talib
import numpy as np
from agents.base import BaseAgent, BaseAnalysisData, AnalysisResult
from tools.market_data_utils import MarketDataProcessor
from tools.llm_api import aquery_llm
from prompts.agents.technical import TechnicalData, TechnicalPromptGenerator
import argparse
from tools.utils import company_to_ticker
from tools import get_api

logger = logging.getLogger(__name__)

@dataclass
class TechnicalIndicators:
    """Technical analysis indicators."""
    ma5: float = np.nan
    ma20: float = np.nan
    ma60: float = np.nan
    rsi: float = np.nan
    macd: float = np.nan
    macd_signal: float = np.nan
    bb_upper: float = np.nan
    bb_middle: float = np.nan
    bb_lower: float = np.nan
    obv: float = np.nan
    current_price: float = np.nan

@dataclass
class TechnicalAnalysisData(BaseAnalysisData):
    """Structure for technical analysis data."""
    symbol: str
    date: str
    indicators: TechnicalIndicators
    period: str = "1y"
    last_update: datetime = field(default_factory=datetime.now)

class TechnicalAgent(BaseAgent):
    """Agent specialized in technical analysis."""
    
    def __init__(self, provider: str = "openai", model_name: str = "gpt-4o"):
        """Initialize the technical agent."""
        super().__init__(
            provider=provider,
            model_name=model_name,
            system_prompt=TechnicalPromptGenerator.generate_system_prompt()
        )
        self.market_processor = MarketDataProcessor()
            
    async def _fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch market data from FinMind."""
        try:
            api = get_api()
            if api is None:
                raise ValueError("Failed to initialize FinMind API")
                
            # Calculate date range for 1 year of data
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            df = api.taiwan_stock_daily(
                stock_id=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                raise ValueError(f"No data found for {symbol}")
                
            # Rename columns to match the expected format
            df = df.rename(columns={
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'Trading_Volume': 'Volume'
            })
            
            # Sort by date
            df = df.sort_values('Date')
            
            return df
            
        except Exception as e:
            logger.error(f"Data fetch error for {symbol}: {e}")
            raise
            
    def _calculate_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Calculate technical indicators."""
        try:
            close = df["Close"]
            return TechnicalIndicators(
                ma5=talib.SMA(close, 5).iloc[-1],
                ma20=talib.SMA(close, 20).iloc[-1],
                ma60=talib.SMA(close, 60).iloc[-1],
                rsi=talib.RSI(close, 14).iloc[-1],
                macd=talib.MACD(close)[0].iloc[-1],
                macd_signal=talib.MACD(close)[1].iloc[-1],
                bb_upper=talib.BBANDS(close)[0].iloc[-1],
                bb_middle=talib.BBANDS(close)[1].iloc[-1],
                bb_lower=talib.BBANDS(close)[2].iloc[-1],
                obv=talib.OBV(close, df["Volume"]).iloc[-1],
                current_price=close.iloc[-1]
            )
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            raise
        
    async def analyze(self, company: str) -> AnalysisResult:
        """Perform technical analysis."""
        try:
            ticker = company_to_ticker(company)
            df = await self._fetch_data(ticker)
            indicators = self._calculate_indicators(df)
            
            # Convert indicators to TechnicalData
            technical_data = TechnicalData(
                symbol=company,
                date=datetime.now().strftime("%Y-%m-%d"),
                current_price=indicators.current_price,
                ma5=indicators.ma5,
                ma20=indicators.ma20,
                ma60=indicators.ma60,
                rsi=indicators.rsi,
                macd=indicators.macd,
                macd_signal=indicators.macd_signal,
                bb_upper=indicators.bb_upper,
                bb_middle=indicators.bb_middle,
                bb_lower=indicators.bb_lower,
                obv=indicators.obv
            )
            
            # Generate analysis prompt
            system_prompt = TechnicalPromptGenerator.generate_system_prompt()
            user_prompt = TechnicalPromptGenerator.get_user_prompt(company, technical_data)
            
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt)
            ]
            
            response = await self.call_model(messages=messages)
            
            if isinstance(response, tuple):
                analysis_content = response[0]
            else:
                analysis_content = str(response)
            

            return AnalysisResult(
                success=True,
                content=analysis_content,
                metadata={"company": company, "analysis_type": "technical", "period": "1y"},
                analysis_data=TechnicalAnalysisData(
                    symbol=company,
                    date=datetime.now().strftime("%Y-%m-%d"),
                    indicators=indicators
                )
            )
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return AnalysisResult(success=False, content="", error=str(e))

if __name__ == "__main__":
    import asyncio
    import argparse
    
    async def main():
        parser = argparse.ArgumentParser(description='Technical Analysis Agent')
        parser.add_argument('company', help='Company name or stock symbol')
        args = parser.parse_args()
        
        agent = TechnicalAgent()
        result = await agent.analyze(args.company)
        print(result.content if result.success else f"Error: {result.error}")
    
    asyncio.run(main()) 