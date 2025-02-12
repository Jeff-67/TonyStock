from dataclasses import dataclass
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@dataclass
class MarketAnalyzer:
    """Analyze market data."""
    
    def analyze_margin_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze margin trading data.
        
        Args:
            df: Margin trading DataFrame
            
        Returns:
            Dictionary containing analysis results
        """
        if df.empty:
            return {}
            
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            return {
                "margin_balance": latest["MarginPurchaseTodayBalance"],
                "margin_change": latest["MarginPurchaseTodayBalance"] - prev["MarginPurchaseTodayBalance"],
                "short_balance": latest["ShortSaleTodayBalance"],
                "short_change": latest["ShortSaleTodayBalance"] - prev["ShortSaleTodayBalance"]
            }
        except Exception as e:
            logger.error(f"Error analyzing margin data: {str(e)}")
            return {}
            
    def analyze_institutional_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze institutional investor data.
        
        Args:
            df: Institutional investor DataFrame
            
        Returns:
            Dictionary containing analysis results
        """
        if df.empty:
            return {}
            
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            return {
                "foreign_buy_sell": latest["Foreign_Investor"],
                "foreign_change": latest["Foreign_Investor"] - prev["Foreign_Investor"],
                "trust_buy_sell": latest["Investment_Trust"],
                "trust_change": latest["Investment_Trust"] - prev["Investment_Trust"],
                "dealer_buy_sell": latest["Dealer"],
                "dealer_change": latest["Dealer"] - prev["Dealer"]
            }
        except Exception as e:
            logger.error(f"Error analyzing institutional data: {str(e)}")
            return {}
            
    def analyze_shareholding_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze shareholding data.
        
        Args:
            df: Shareholding DataFrame
            
        Returns:
            Dictionary containing analysis results
        """
        if df.empty:
            return {}
            
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            return {
                "foreign_ratio": latest["ForeignInvestmentSharesRatio"],
                "foreign_ratio_change": latest["ForeignInvestmentSharesRatio"] - prev["ForeignInvestmentSharesRatio"],
                "foreign_shares": latest["ForeignInvestmentShares"],
                "foreign_shares_change": latest["ForeignInvestmentShares"] - prev["ForeignInvestmentShares"]
            }
        except Exception as e:
            logger.error(f"Error analyzing shareholding data: {str(e)}")
            return {}
            
    def analyze_price_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price data.
        
        Args:
            df: Price DataFrame
            
        Returns:
            Dictionary containing analysis results
        """
        if df.empty:
            return {}
            
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            return {
                "close": latest["close"],
                "change": latest["close"] - prev["close"],
                "volume": latest["Trading_Volume"],
                "volume_change": latest["Trading_Volume"] - prev["Trading_Volume"]
            }
        except Exception as e:
            logger.error(f"Error analyzing price data: {str(e)}")
            return {}

class DataProcessor:
    """Process market data for analysis."""
    
    def __init__(self, analyzer: MarketAnalyzer):
        """Initialize processor.
        
        Args:
            analyzer: Market data analyzer
        """
        self.analyzer = analyzer
        
    def prepare_analysis_data(self, market_data: Dict[str, pd.DataFrame], stock_id: str) -> Dict[str, Any]:
        """Prepare data for analysis.
        
        Args:
            market_data: Dictionary containing market data
            stock_id: Stock ID
            
        Returns:
            Dictionary containing processed data
        """
        try:
            analysis = {
                "stock_id": stock_id,
                "margin": self.analyzer.analyze_margin_data(market_data.get("margin", pd.DataFrame())),
                "institutional": self.analyzer.analyze_institutional_data(market_data.get("institutional", pd.DataFrame())),
                "shareholding": self.analyzer.analyze_shareholding_data(market_data.get("shareholding", pd.DataFrame())),
                "price": self.analyzer.analyze_price_data(market_data.get("price", pd.DataFrame()))
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error preparing analysis data: {str(e)}")
            return {
                "stock_id": stock_id,
                "error": str(e)
            } 