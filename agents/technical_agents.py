"""Technical analysis agent module.

This module implements agents for performing technical analysis on stock data.
It provides various technical indicators and analysis methods for market data.
"""

import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import talib
import yfinance as yf
import numpy as np
from agents.base import BaseAgent, BaseAnalysisData, AnalysisResult
from tools.market_data_utils import MarketDataProcessor, MarketMetrics
from tools.llm_api import aquery_llm
import argparse

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
    indicators: TechnicalIndicators = field(default_factory=TechnicalIndicators)
    market_metrics: Optional[MarketMetrics] = None
    period: str = "1y"
    last_update: datetime = field(default_factory=datetime.now)

class TechnicalAgent(BaseAgent):
    """Agent specialized in technical analysis."""
    
    def __init__(
        self,
        provider: str = "openai",
        model_name: str = "gpt-4o",
        system_prompt: Optional[str] = None
    ):
        """Initialize the technical agent.
        
        Args:
            provider: LLM provider (default: openai)
            model_name: Model name (default: gpt-4o)
            system_prompt: Optional custom system prompt
        """
        default_prompt = """You are a professional technical analysis expert. Please provide a comprehensive market analysis based on the provided technical indicators, including:

        1. Trend Analysis
        - Use moving averages (MA5, MA20, MA60) to determine short, medium, and long-term trends
        - Analyze price relationships with moving averages
        - Identify potential trend reversal points

        2. Momentum Analysis
        - Interpret RSI overbought/oversold signals
        - Analyze MACD trends and divergences
        - Evaluate momentum strength

        3. Volatility Analysis
        - Use Bollinger Bands to assess price volatility
        - Analyze if price is near support or resistance levels
        - Evaluate current volatility levels

        4. Volume Analysis
        - Interpret OBV indicator changes
        - Evaluate volume-price relationship
        - Assess market participation

        Please provide:
        1. Detailed analysis of each indicator
        2. Current market position assessment
        3. Important technical signals to watch
        4. Potential support and resistance levels
        5. Risk warnings

        In your analysis:
        - Provide specific data support
        - Explain reasoning
        - Point out important technical patterns
        - Include risk warnings

        Your analysis will serve as an important reference for investment decisions, please be thorough and professional."""
            
        super().__init__(
            provider=provider,
            model_name=model_name,
            system_prompt=system_prompt or default_prompt
        )
        self.market_processor = MarketDataProcessor()
            
    async def _fetch_data(self, symbol: str) -> pd.DataFrame:
        """Fetch market data for technical analysis.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame with market data
        """
        try:
            # Add .TW suffix for Taiwan stocks if not present
            if not symbol.endswith('.TW'):
                symbol = f"{symbol}.TW"
            
            # Fetch data using yfinance
            stock = yf.Ticker(symbol)
            df = stock.history(period="1y")
            
            if df.empty:
                raise ValueError(f"No data found for symbol {symbol}")
                
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
            
    def _calculate_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Calculate technical indicators.
        
        Args:
            df: DataFrame with market data
            
        Returns:
            Technical indicators
        """
        try:
            # Moving Averages
            ma5 = pd.Series(talib.SMA(df["Close"], timeperiod=5)).iloc[-1]
            ma20 = pd.Series(talib.SMA(df["Close"], timeperiod=20)).iloc[-1]
            ma60 = pd.Series(talib.SMA(df["Close"], timeperiod=60)).iloc[-1]
            
            # RSI
            rsi = pd.Series(talib.RSI(df["Close"], timeperiod=14)).iloc[-1]
            
            # MACD
            macd, signal, _ = talib.MACD(df["Close"])
            macd = pd.Series(macd).iloc[-1]
            macd_signal = pd.Series(signal).iloc[-1]
            
            # Bollinger Bands
            upper, middle, lower = talib.BBANDS(df["Close"])
            bb_upper = pd.Series(upper).iloc[-1]
            bb_middle = pd.Series(middle).iloc[-1]
            bb_lower = pd.Series(lower).iloc[-1]
            
            # Volume Indicators
            obv = pd.Series(talib.OBV(df["Close"], df["Volume"])).iloc[-1]
            
            # Current Price
            current_price = df["Close"].iloc[-1]
            
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
                current_price=current_price
            )
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise
    
    def _format_analysis_message(self, indicators: TechnicalIndicators) -> str:
        """Format technical analysis data for model input."""
        return f"""Please analyze the following technical indicators and provide a comprehensive market analysis:

        Technical Indicators Data:

        1. Price and Moving Averages
        - Current Price: {indicators.current_price:.2f}
        - MA5: {indicators.ma5:.2f}
        - MA20: {indicators.ma20:.2f}
        - MA60: {indicators.ma60:.2f}

        2. Momentum Indicators
        - RSI(14): {indicators.rsi:.2f}
        - MACD: {indicators.macd:.2f}
        - MACD Signal: {indicators.macd_signal:.2f}

        3. Volatility (Bollinger Bands)
        - Upper Band: {indicators.bb_upper:.2f}
        - Middle Band: {indicators.bb_middle:.2f}
        - Lower Band: {indicators.bb_lower:.2f}

        4. Volume
        - On-Balance Volume (OBV): {indicators.obv:.0f}

        Based on these indicators, please provide:
        1. A detailed trend analysis using moving averages
        2. Momentum analysis using RSI and MACD
        3. Volatility assessment using Bollinger Bands
        4. Volume analysis using OBV
        5. Key support and resistance levels
        6. Important technical signals to watch
        7. Risk assessment

        Please be specific and thorough in your analysis."""
        
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
                
            logger.info(f"Starting technical analysis for {company}")
            
            # Fetch and analyze data
            logger.info("Fetching market data...")
            df = await self._fetch_data(company)
            
            logger.info("Calculating technical indicators...")
            indicators = self._calculate_indicators(df)
            
            # Format analysis message
            analysis_msg = self._format_analysis_message(indicators)
            
            # Create messages for the model
            messages = [
                {
                    "role": "system",
                    "content": self.message_history[0]["content"]
                },
                {
                    "role": "user",
                    "content": f"Please analyze the technical indicators for {company}:\n\n{analysis_msg}"
                }
            ]
            
            logger.info("Calling LLM for analysis...")
            # Get analysis from model
            response = await aquery_llm(
                messages=messages,
                model=self.model_name,
                provider=self.provider
            )
            
            logger.debug(f"Raw model response: {response}")
            
            # Extract content from response
            try:
                if isinstance(response, tuple):
                    response = response[0]
                
                if isinstance(response, dict) and 'choices' in response:
                    analysis = response['choices'][0]['message']['content']
                elif hasattr(response, 'choices') and response.choices:
                    message = response.choices[0].message
                    if hasattr(message, 'content'):
                        analysis = message.content
                    elif hasattr(message, 'function_call'):
                        analysis = message.function_call.get('arguments', '{}')
                    else:
                        logger.warning("No content or function call in message")
                        analysis = self._format_default_analysis(indicators)
                else:
                    logger.warning("Unexpected response format")
                    analysis = self._format_default_analysis(indicators)
            except Exception as e:
                logger.error(f"Error extracting content: {e}")
                analysis = self._format_default_analysis(indicators)
            
            logger.debug(f"Extracted analysis: {analysis}")
            
            if not analysis:
                logger.warning("No analysis content extracted")
                analysis = self._format_default_analysis(indicators)
            
            # Prepare market metrics
            logger.info("Preparing market metrics...")
            market_metrics = self.market_processor.prepare_market_metrics(df)
            
            # Create analysis data
            analysis_data = TechnicalAnalysisData(
                symbol=company,
                date=datetime.now().strftime("%Y%m%d"),
                indicators=indicators,
                market_metrics=market_metrics
            )
            
            logger.info("Analysis completed successfully")
            return AnalysisResult(
                success=True,
                content=analysis,
                metadata={
                    "company": company,
                    "analysis_type": "technical",
                    "period": "1y"
                },
                analysis_data=analysis_data
            )
            
        except Exception as e:
            logger.error(f"Technical analysis error: {str(e)}")
            return self.format_error_response(e)

    def _format_default_analysis(self, indicators: TechnicalIndicators) -> str:
        """Format default analysis when LLM response fails."""
        return f"""
Technical Indicator Analysis:

1. Price Trends
- Current Price: {indicators.current_price:.2f}
- MA5: {indicators.ma5:.2f}
- MA20: {indicators.ma20:.2f}
- MA60: {indicators.ma60:.2f}

2. Momentum Indicators
- RSI(14): {indicators.rsi:.2f}
- MACD: {indicators.macd:.2f}
- MACD Signal: {indicators.macd_signal:.2f}

3. Volatility Indicators
- Bollinger Upper: {indicators.bb_upper:.2f}
- Bollinger Middle: {indicators.bb_middle:.2f}
- Bollinger Lower: {indicators.bb_lower:.2f}

4. Volume
- OBV: {indicators.obv:.0f}

Note: This is a system-generated basic analysis. Please consider other factors for investment decisions.
"""

if __name__ == "__main__":
    import asyncio
    import argparse
    
    async def main():
        # Set up command line arguments
        parser = argparse.ArgumentParser(description='Technical Analysis Agent')
        parser.add_argument('query', type=str, help='Analysis query')
        parser.add_argument('--company', type=str, required=True, help='Stock symbol')
        parser.add_argument('--log-level', type=str, default='INFO', 
                          choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                          help='Logging level')
        
        args = parser.parse_args()
        
        # Set logging level
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Run analysis
        agent = TechnicalAgent()
        result = await agent.analyze(args.query, company=args.company)
        
        # Output results
        if result.success:
            print("\n=== Technical Analysis Results ===")
            print(result.content)
            print("\n=== Analysis Complete ===")
        else:
            print(f"Error: {result.error}")
    
    asyncio.run(main()) 