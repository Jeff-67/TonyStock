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
from tools.twse_service import TwseService
import argparse
from tools.utils import company_to_ticker
import asyncio
from opik import track

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
    @track()
    async def _fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch market data from TWSE."""
        try:
            # Get stock day all data for all stocks
            data = await TwseService.get_stock_day_all()
            if not data["success"]:
                raise ValueError(f"Failed to fetch data: {data['message']}")
                
            # Try different formats of the stock code
            stock_data = None
            tried_codes = []
            
            # Original code
            tried_codes.append(symbol)
            stock_data = [d for d in data["data"] if d["Code"] == symbol]
            
            # Without leading zeros
            if not stock_data:
                no_zeros = symbol.lstrip('0')
                tried_codes.append(no_zeros)
                stock_data = [d for d in data["data"] if d["Code"] == no_zeros]
                
            # With exactly 4 digits
            if not stock_data:
                four_digits = symbol.zfill(4)
                tried_codes.append(four_digits)
                stock_data = [d for d in data["data"] if d["Code"] == four_digits]
                
            if not stock_data:
                # Log available codes for debugging
                sample_codes = sorted(set(d["Code"] for d in data["data"]))[:10]
                logger.info(f"Sample of available codes: {sample_codes}")
                raise ValueError(f"No data found for stock codes tried: {tried_codes}")
                
            # Get current date and adjust for business days
            current_date = datetime.now()
            while current_date.weekday() > 4:  # Adjust if current day is weekend
                current_date -= timedelta(days=1)
                
            # Convert to DataFrame with proper data type conversion
            df = pd.DataFrame([{
                'Date': current_date.strftime('%Y-%m-%d'),  # Current business day
                'Open': float(d['OpeningPrice'].replace(',', '') if d['OpeningPrice'] != '--' else 0),
                'High': float(d['HighestPrice'].replace(',', '') if d['HighestPrice'] != '--' else 0),
                'Low': float(d['LowestPrice'].replace(',', '') if d['LowestPrice'] != '--' else 0),
                'Close': float(d['ClosingPrice'].replace(',', '') if d['ClosingPrice'] != '--' else 0),
                'Volume': int(d['TradeVolume'].replace(',', '') if d['TradeVolume'] != '--' else 0)
            } for d in stock_data])
            
            # Sort by date
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            # Convert columns to numpy arrays of type float64
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = df[col].astype('float64')
            
            return df
            
        except Exception as e:
            logger.error(f"Data fetch error for {symbol}: {e}")
            raise
    
    @track()
    def _calculate_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Calculate technical indicators using TA-Lib."""
        try:
            close = df["Close"].values
            high = df["High"].values
            low = df["Low"].values
            volume = df["Volume"].values

            # Calculate Moving Averages
            ma5 = talib.SMA(close, timeperiod=5)[-1]
            ma20 = talib.SMA(close, timeperiod=20)[-1]
            ma60 = talib.SMA(close, timeperiod=60)[-1]

            # Calculate RSI
            rsi = talib.RSI(close, timeperiod=14)[-1]

            # Calculate MACD
            macd, macd_signal, _ = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            macd = macd[-1]
            macd_signal = macd_signal[-1]

            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close,
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2,
                matype=0
            )
            bb_upper = bb_upper[-1]
            bb_middle = bb_middle[-1]
            bb_lower = bb_lower[-1]

            # Calculate On Balance Volume
            obv = talib.OBV(close, volume)[-1]

            return TechnicalIndicators(
                ma5=ma5,
                ma20=ma20,
                ma60=ma60,
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                bb_upper=bb_upper,
                bb_middle=bb_middle,
                bb_lower=bb_lower,
                obv=obv,
                current_price=close[-1]
            )
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            raise
    @track()
    async def analyze(self, company: str) -> AnalysisResult:
        """Perform technical analysis."""
        try:
            # Convert company name to stock symbol if needed
            if not company.isdigit():
                ticker = company_to_ticker(company)
                if ticker is None:
                    raise ValueError(f"Could not find ticker for company: {company}")
            else:
                ticker = company
                
            # Try to fetch data
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