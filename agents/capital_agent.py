"""Capital analysis agent module.

This module implements agents for performing capital analysis on stock data.
It provides analysis of institutional investors, margin trading, and market data.
"""

import logging
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
from datetime import datetime, timedelta
import statistics
import pandas as pd
import sys
from opik import track
import numpy as np
# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from tools.capital_data_fetcher import fetch_market_data, DataLoader
from tools.llm_api import aquery_llm, Message
from prompts.agents.capital_prompt import (
    CapitalPromptGenerator,
    MarketData,
    InstitutionalData,
    MarginData,
    AnalysisData
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFormatter:
    """Utility class for data formatting."""
    
    @staticmethod
    def format_stock_number(symbol: str) -> str:
        """Format stock number to TWSE format."""
        return ''.join(filter(str.isdigit, symbol)).zfill(4)
    
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
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility."""
        if len(prices) < 2:
            return 0
        returns = [(b - a) / a for a, b in zip(prices[:-1], prices[1:])]
        return statistics.stdev(returns) if returns else 0
    
    def calculate_trend(self, prices: List[float]) -> float:
        """Calculate price trend."""
        if not prices:
            return 0
        avg_price = sum(prices) / len(prices)
        return (prices[-1] - prices[0]) / avg_price if avg_price else 0
    
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

class DataProcessor:
    """Processes and structures market data."""
    
    def __init__(self, market_analyzer: MarketAnalyzer):
        self.market_analyzer = market_analyzer
    
    def extract_latest_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract latest market data."""
        price_data = market_data.get("price", pd.DataFrame())
        margin_data = market_data.get("margin", pd.DataFrame())
        
        if price_data.empty or margin_data.empty:
            logger.warning("Price or margin data is empty")
            return {}
            
        try:
            # Get latest data from each DataFrame
            latest_price = price_data.sort_values("date").iloc[-1]
            latest_margin = margin_data.sort_values("date").iloc[-1]
            
            # Log the data for debugging
            logger.info(f"Latest price data: {latest_price.to_dict()}")
            logger.info(f"Latest margin data: {latest_margin.to_dict()}")
            
            # Combine the data with correct column names
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
    
    def calculate_institutional_sums(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate institutional trading sums."""
        if data.empty:
            logger.warning("Institutional data is empty")
            return {"foreign_net": 0.0, "trust_net": 0.0, "dealer_net": 0.0}
            
        try:
            # Get last 5 days of data
            recent_data = data.sort_values("date").tail(5)
            logger.info(f"Processing recent institutional data: {recent_data.to_dict('records')}")
            
            # Initialize net positions
            net_positions = {
                "foreign_net": 0.0,
                "trust_net": 0.0,
                "dealer_net": 0.0
            }
            
            # Track if we have any data for each type
            has_data = {
                "foreign_net": False,
                "trust_net": False,
                "dealer_net": False
            }
            
            # Process each row
            for _, row in recent_data.iterrows():
                buy = safe_float(row.get('buy'))
                sell = safe_float(row.get('sell'))
                name = row.get('name', '')
                
                # Calculate net position (buy - sell)
                net = buy - sell
                logger.debug(f"Processing row - name: {name}, buy: {buy}, sell: {sell}, net: {net}")
                
                # Aggregate based on investor type
                if 'Foreign' in name and 'Trust' not in name:
                    net_positions["foreign_net"] += net
                    has_data["foreign_net"] = True
                elif 'Investment_Trust' in name:
                    net_positions["trust_net"] += net
                    has_data["trust_net"] = True
                elif 'Dealer' in name:
                    net_positions["dealer_net"] += net
                    has_data["dealer_net"] = True
            
            # Replace zeros with defaults where we have no data
            for key in net_positions:
                if not has_data[key]:
                    net_positions[key] = 0.0
            
            logger.info(f"Calculated institutional sums: {net_positions}")
            return net_positions
            
        except Exception as e:
            logger.error(f"Error calculating institutional sums: {str(e)}")
            return {"foreign_net": 0.0, "trust_net": 0.0, "dealer_net": 0.0}
    
    def prepare_analysis_data(self, market_data: Dict[str, Any], symbol: str) -> AnalysisData:
        """Prepare structured analysis data from raw market data."""
        try:
            latest_data = self.extract_latest_data(market_data)
            institutional_data = market_data.get("institutional", pd.DataFrame())
            shareholding_data = market_data.get("shareholding", pd.DataFrame())
            price_data = market_data.get("price", pd.DataFrame())
            
            # Log data availability and content
            logger.info(f"Data availability for {symbol}:")
            logger.info(f"Price data: {not price_data.empty}")
            logger.info(f"Institutional data: {not institutional_data.empty}")
            logger.info(f"Shareholding data: {not shareholding_data.empty}")
            
            if not price_data.empty:
                logger.info(f"Latest price data: {price_data.sort_values('date').iloc[-1].to_dict()}")
            
            # Prepare market data
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
            
            # Calculate institutional sums
            inst_sums = self.calculate_institutional_sums(institutional_data)
            
            # Get latest shareholding data
            latest_shareholding = {}
            if not shareholding_data.empty:
                latest_shareholding = shareholding_data.sort_values("date").iloc[-1].to_dict()
                logger.info(f"Latest shareholding data: {latest_shareholding}")
            
            # Get foreign holding ratio and ensure it's properly formatted
            foreign_holding = safe_float(latest_shareholding.get("ForeignInvestmentSharesRatio", 
                latest_shareholding.get("foreign_holding_ratio")))
            
            # Log the foreign holding ratio for debugging
            logger.info(f"Raw foreign holding ratio: {foreign_holding}")
            
            # Prepare institutional data
            institutional = InstitutionalData(
                foreign_net=safe_float(inst_sums["foreign_net"]),
                trust_net=safe_float(inst_sums["trust_net"]),
                dealer_net=safe_float(inst_sums["dealer_net"]),
                foreign_holding=foreign_holding,  # Already properly formatted as percentage
                trust_holding=0.0,  # Not available in current data
                dealer_holding=0.0  # Not available in current data
            )
            
            # Prepare margin data
            margin = MarginData(
                margin_balance=safe_int(latest_data.get("margin_balance")),
                short_balance=safe_int(latest_data.get("short_balance"))
            )
            
            logger.info(f"Prepared analysis data: {market.__dict__}, {institutional.__dict__}, {margin.__dict__}")
            return AnalysisData(market=market, institutional=institutional, margin=margin)
            
        except Exception as e:
            logger.error(f"Error preparing analysis data: {str(e)}")
            raise

def validate_dataframe(df: pd.DataFrame, name: str) -> bool:
    """Validate DataFrame for NaN values and log issues."""
    if df.empty:
        logger.warning(f"{name} DataFrame is empty")
        return False
        
    nan_cols = df.columns[df.isna().any()].tolist()
    if nan_cols:
        logger.warning(f"Found NaN values in {name} columns: {nan_cols}")
        logger.warning(f"NaN counts: {df[nan_cols].isna().sum().to_dict()}")
        return False
    return True

class ChipsAnalysisAgent:
    """Agent for performing chips analysis."""
    
    def __init__(self):
        self.market_analyzer = MarketAnalyzer()
        self.data_processor = DataProcessor(self.market_analyzer)
    
    @track()
    async def analyze(self, symbol: str) -> Dict[str, Any]:
        """Analyze stock chips data using LLM."""
        try:
            # Use the initialized API from tools package
            api = DataLoader()
            api.login_by_token(api_token=os.getenv("FINMIND_API_KEY"))
            
            # Calculate date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            
            # Fetch and process data
            formatted_symbol = DataFormatter.format_stock_number(symbol)
            logger.info(f"Fetching data for symbol {formatted_symbol} from {start_date} to {end_date}")
            
            market_data = fetch_market_data(
                api=api,
                symbol=formatted_symbol,
                data_types=["margin", "institutional", "shareholding", "price"],
                start_date=start_date,
                end_date=end_date
            )
            
            if not market_data or formatted_symbol not in market_data:
                logger.error(f"No data available for symbol {formatted_symbol}")
                return {"error": "No data available"}
                
            market_data = market_data[formatted_symbol]
            
            # Validate and clean data
            data_valid = True
            for data_type, data in market_data.items():
                if isinstance(data, pd.DataFrame):
                    logger.info(f"{data_type} data shape: {data.shape}")
                    if not data.empty:
                        logger.info(f"{data_type} data columns: {data.columns.tolist()}")
                        logger.info(f"{data_type} first row: {data.iloc[0].to_dict()}")
                        
                        # Validate data
                        if not validate_dataframe(data, data_type):
                            data_valid = False
                            # Clean NaN values based on data type
                            if data_type == "price":
                                market_data[data_type] = data.fillna(method='ffill').fillna(method='bfill')
                            elif data_type == "institutional":
                                market_data[data_type] = data.fillna(0)
                            elif data_type == "shareholding":
                                market_data[data_type] = data.fillna(method='ffill')
                            elif data_type == "margin":
                                market_data[data_type] = data.fillna(0)
                            
                            logger.info(f"Cleaned {data_type} data of NaN values")
            
            if not data_valid:
                logger.warning("Some data contained NaN values and was cleaned")
            
            # Prepare analysis data
            analysis_data = self.data_processor.prepare_analysis_data(market_data, symbol)
            
            # Validate analysis data
            for field_name, field_value in analysis_data.__dict__.items():
                if isinstance(field_value, (float, int)) and pd.isna(field_value):
                    logger.error(f"Found NaN in analysis_data.{field_name}")
                    return {"error": f"Invalid data: NaN found in {field_name}"}
            
            # Generate analysis
            system_prompt = CapitalPromptGenerator.generate_system_prompt(analysis_data)
            user_prompt = CapitalPromptGenerator.get_user_prompt(symbol)
            
            analysis_result = await aquery_llm(messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt)
            ])
            
            # Return results
            return {
                "symbol": symbol,
                "market_condition": analysis_data.market.market_condition,
                "data": market_data.get("price", pd.DataFrame()).to_dict('records'),
                "metrics": {
                    "price": market_data.get("price", pd.DataFrame()).to_dict('records'),
                    "institutional": market_data.get("institutional", pd.DataFrame()).to_dict('records'),
                    "shareholding": market_data.get("shareholding", pd.DataFrame()).to_dict('records'),
                    "margin": market_data.get("margin", pd.DataFrame()).to_dict('records')
                },
                "institutional_data": market_data.get("institutional", pd.DataFrame()).to_dict('records'),
                "shareholding_data": market_data.get("shareholding", pd.DataFrame()).to_dict('records'),
                "llm_analysis": analysis_result,
                "analysis_data": analysis_data.__dict__
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {"error": str(e)}

async def main():
    """Test function."""
    symbol = "2330"
    
    try:
        # Run analysis
        agent = ChipsAnalysisAgent()
        result = await agent.analyze(symbol)
        
        if "error" in result:
            logger.error(f"Analysis error: {result['error']}")
            return
        
        # Print results
        logger.info("\nCapital Analysis Summary")
        logger.info("=" * 50)
        logger.info(f"\nMarket Condition: {result['market_condition']}")
        
        if result.get("llm_analysis"):
            logger.info("\nAnalysis Report:")
            logger.info("-" * 30)
            logger.info(result["llm_analysis"])
        
        logger.info("\n" + "=" * 50)
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 