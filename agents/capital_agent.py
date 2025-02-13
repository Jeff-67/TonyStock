"""Capital analysis agent module.

This module implements agents for performing capital analysis on stock data.
It provides analysis of institutional investors, margin trading, and market data.
"""

import logging
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import sys
from opik import track
# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from tools.llm_api import Message
from tools.utils import company_to_ticker
from prompts.agents.capital import CapitalPromptGenerator
from agents.base import BaseAgent, BaseAnalysisData, AnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Market data structure."""
    symbol: str
    date: str
    price: float
    price_change: float
    volume: int
    market_condition: str

@dataclass
class InstitutionalData:
    """Institutional investors data structure."""
    foreign_net: float
    trust_net: float
    dealer_net: float
    foreign_holding: float

@dataclass
class MarginData:
    """Margin trading data structure."""
    margin_balance: int
    short_balance: int

@dataclass
class CapitalAnalysisData(BaseAnalysisData):
    """Structure for capital analysis data."""
    market: MarketData
    institutional: InstitutionalData
    margin: MarginData
    last_update: datetime = field(default_factory=datetime.now)

class CapitalAgent(BaseAgent):
    """Agent for performing capital analysis."""
    
    def __init__(
        self,
        provider: str = "openai",
        model_name: str = "gpt-4o",
        system_prompt: Optional[str] = None
    ):
        """Initialize the capital agent."""
        super().__init__(provider=provider, model_name=model_name, system_prompt=system_prompt)
        self.market_analyzer = MarketAnalyzer()
        self.data_processor = DataProcessor(self.market_analyzer)
    @track()
    async def analyze(self, company: str) -> AnalysisResult:
        """Analyze stock chips data using LLM.
        
        Args:
            query: User query
            **kwargs: Additional arguments including company name
            
        Returns:
            AnalysisResult with analysis data and LLM response
        """
        try:
            symbol = company_to_ticker(company)
            formatted_symbol = DataFormatter.format_stock_number(symbol)
            
            if not formatted_symbol:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Invalid stock symbol"
                )
            
            logger.info(f"Analyzing company: {company} (Symbol: {formatted_symbol})")
            
            # Use the initialized API from tools package
            market_data = await self.data_processor.fetch_data(symbol)
            analysis_data = self.data_processor.prepare_analysis_data(market_data, symbol)
            
            # Generate analysis
            system_prompt = CapitalPromptGenerator.generate_system_prompt()
            user_prompt = CapitalPromptGenerator.get_user_prompt(company, analysis_data)
            
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
                metadata={
                    "company": company,
                    "symbol": symbol,
                    "analysis_type": "capital",
                    "period": "60d"
                },
                analysis_data=analysis_data
            )
            
        except Exception as e:
            return self.format_error_response(e)
        
class DataFormatter:
    """Utility class for data formatting."""
    
    @staticmethod
    def format_stock_number(symbol: str) -> str:
        """Format stock number to TWSE format."""
        if not symbol:
            return ""
        digits = ''.join(filter(str.isdigit, str(symbol)))
        return digits.zfill(4) if digits else ""
    
    @staticmethod
    def format_date(date_obj: Optional[datetime] = None) -> str:
        """Format date to YYYYMMDD format, adjusting for weekends."""
        if date_obj is None:
            date_obj = datetime.now()
        while date_obj.weekday() > 4:  # Adjust for weekends
            date_obj -= timedelta(days=1)
        return date_obj.strftime("%Y%m%d")

class MarketAnalyzer:
    """Analyzes market conditions and trends."""
    
    def __init__(self, volatility_window: int = 20):
        self.volatility_window = volatility_window
    @track()
    def calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility."""
        if len(prices) < 2:
            return 0
        returns = [(b - a) / a for a, b in zip(prices[:-1], prices[1:])]
        return statistics.stdev(returns) if returns else 0
    @track()
    def calculate_trend(self, prices: List[float]) -> float:
        """Calculate price trend."""
        if not prices:
            return 0
        avg_price = sum(prices) / len(prices)
        return (prices[-1] - prices[0]) / avg_price if avg_price else 0
    @track()
    def analyze_market_condition(self, data: List[Dict[str, Any]]) -> str:
        """Determine market condition based on volatility and trend."""
        if not data or len(data) < self.volatility_window:
            return "normal"
            
        prices = [float(item.get('close', 0)) for item in data[-self.volatility_window:]]
        volatility = self.calculate_volatility(prices)
        trend = self.calculate_trend(prices)
        
        if volatility > self.calculate_volatility(prices[:-5]) * 1.5:
            return "volatile"
        elif abs(trend) > volatility * 2:
            return "trending"
        return "normal"

class DataProcessor:
    """Processes and structures market data."""
    
    def __init__(self, market_analyzer: MarketAnalyzer):
        self.market_analyzer = market_analyzer
    @track()
    async def fetch_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch market data for a specific symbol."""
        from tools import get_api
        api = get_api()
        if api is None:
            raise ValueError("Failed to initialize FinMind API")
        # Calculate date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        try:
            market_data = {}
            
            # Fetch market data
            margin_df = api.taiwan_stock_margin_purchase_short_sale(
                stock_id=symbol,
                start_date=start_date,
                end_date=end_date
            )
            market_data["margin"] = margin_df if not margin_df.empty else pd.DataFrame()
            
            inst_df = api.taiwan_stock_institutional_investors(
                stock_id=symbol,
                start_date=start_date,
                end_date=end_date
            )
            market_data["institutional"] = inst_df if not inst_df.empty else pd.DataFrame()
            
            share_df = api.taiwan_stock_shareholding(
                stock_id=symbol,  
                start_date=start_date,
                end_date=end_date
            )
            market_data["shareholding"] = share_df if not share_df.empty else pd.DataFrame()
            
            price_df = api.taiwan_stock_daily(
                stock_id=symbol,
                start_date=start_date,
                end_date=end_date
            )
            market_data["price"] = price_df if not price_df.empty else pd.DataFrame()
            
            if all(df.empty for df in market_data.values()):
                return AnalysisResult(
                    success=False,
                    content="",
                    error="No data available"
                )
                
        except Exception as e:
            return AnalysisResult(
                success=False,
                content="",
                error=f"Failed to fetch market data: {str(e)}"
            )
        
        # Fill missing values
        for data_type, data in market_data.items():
            if data_type in ['price', 'volume']:
                market_data[data_type] = data.ffill().bfill()
            else:
                market_data[data_type] = data.ffill()
            
        return market_data
    @track()
    def extract_latest_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract latest market data."""
        price_data = market_data.get("price", pd.DataFrame())
        margin_data = market_data.get("margin", pd.DataFrame())
        
        if price_data.empty or margin_data.empty:
            logger.warning("Price or margin data is empty")
            return {}
            
        try:
            latest_price = price_data.sort_values("date").iloc[-1]
            latest_margin = margin_data.sort_values("date").iloc[-1]
            
            return {
                "date": latest_price.get("date", ""),
                "close": safe_float(latest_price.get("close")),
                "open": safe_float(latest_price.get("open")),
                "volume": safe_int(latest_price.get("volume", latest_price.get("Trading_Volume"))),
                "margin_balance": safe_int(latest_margin.get("margin_balance", latest_margin.get("MarginPurchaseTodayBalance"))),
                "short_balance": safe_int(latest_margin.get("short_balance", latest_margin.get("ShortSaleTodayBalance")))
            }
        except Exception as e:
            logger.error(f"Error extracting latest data: {str(e)}")
            return {}
    @track()
    def calculate_institutional_sums(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate institutional trading sums for the last 5 days."""
        if data.empty:
            logger.warning("Institutional data is empty")
            return {"foreign_net": 0.0, "trust_net": 0.0, "dealer_net": 0.0}
            
        try:
            recent_data = data.sort_values("date").tail(5)
            net_positions = {"foreign_net": 0.0, "trust_net": 0.0, "dealer_net": 0.0}
            
            for _, row in recent_data.iterrows():
                buy = safe_float(row.get('buy'))
                sell = safe_float(row.get('sell'))
                name = row.get('name', '')
                net = buy - sell
                
                if 'Foreign' in name and 'Trust' not in name:
                    net_positions["foreign_net"] += net
                elif 'Investment_Trust' in name:
                    net_positions["trust_net"] += net
                elif 'Dealer' in name:
                    net_positions["dealer_net"] += net
            
            return net_positions
            
        except Exception as e:
            logger.error(f"Error calculating institutional sums: {str(e)}")
            return {"foreign_net": 0.0, "trust_net": 0.0, "dealer_net": 0.0}
    @track()
    def prepare_analysis_data(self, market_data: Dict[str, Any], symbol: str) -> CapitalAnalysisData:
        """Prepare structured analysis data from raw market data."""
        try:
            latest_data = self.extract_latest_data(market_data)
            institutional_data = market_data.get("institutional", pd.DataFrame())
            shareholding_data = market_data.get("shareholding", pd.DataFrame())
            price_data = market_data.get("price", pd.DataFrame())
            
            market = MarketData(
                symbol=symbol,
                date=latest_data.get("date", ""),
                price=safe_float(latest_data.get("close")),
                price_change=safe_float(latest_data.get("close")) - safe_float(latest_data.get("open")),
                volume=safe_int(latest_data.get("volume")),
                market_condition=self.market_analyzer.analyze_market_condition(
                    price_data.to_dict('records') if not price_data.empty else []
                )
            )
            
            inst_sums = self.calculate_institutional_sums(institutional_data)
            
            latest_shareholding = {}
            if not shareholding_data.empty:
                latest_shareholding = shareholding_data.sort_values("date").iloc[-1].to_dict()
            
            foreign_holding = safe_float(latest_shareholding.get("ForeignInvestmentSharesRatio", 
                latest_shareholding.get("foreign_holding_ratio")))
            
            institutional = InstitutionalData(
                foreign_net=safe_float(inst_sums["foreign_net"]),
                trust_net=safe_float(inst_sums["trust_net"]),
                dealer_net=safe_float(inst_sums["dealer_net"]),
                foreign_holding=foreign_holding,
            )
            
            margin = MarginData(
                margin_balance=safe_int(latest_data.get("margin_balance")),
                short_balance=safe_int(latest_data.get("short_balance"))
            )
            
            return CapitalAnalysisData(
                symbol=symbol,
                date=latest_data.get("date", ""),
                market=market,
                institutional=institutional,
                margin=margin
            )
            
        except Exception as e:
            logger.error(f"Error preparing analysis data: {str(e)}")
            raise


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float safely, handling NaN and None."""
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int safely, handling NaN and None."""
    try:
        if pd.isna(value) or value is None:
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

async def main():
    """Test function."""
    company = "京鼎"
    
    try:
        agent = CapitalAgent()
        result = await agent.analyze(company)
        
        if not result.success:
            logger.error(f"Analysis error: {result.error}")
            return
        
        logger.info("\nCapital Analysis Summary")
        logger.info("=" * 50)
        logger.info(f"\nMarket Condition: {result.analysis_data.market.market_condition}")
        logger.info("\nAnalysis Report:")
        logger.info("-" * 30)
        logger.info(result.content)
        logger.info("\n" + "=" * 50)
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 