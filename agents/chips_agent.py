"""Chips analysis agent module.

This module implements agents for performing chips analysis on stock data.
It provides various chips indicators and analysis methods for market data.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import os
import json
import sys
from pathlib import Path
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

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

class MarketConditionAnalyzer:
    """Analyzes current market conditions."""
    
    def __init__(self, volatility_window: int = 20):
        self.volatility_window = volatility_window
        self.market_regime = "normal"  # normal, volatile, trending
        
    def analyze_market_condition(self, data: pd.DataFrame) -> str:
        """Determine current market condition."""
        if data is None or len(data) < self.volatility_window:
            return "normal"
            
        # Calculate volatility
        returns = data['Close'].pct_change()
        current_vol = returns.tail(self.volatility_window).std()
        historical_vol = returns.std()
        
        # Calculate trend strength using numpy's polyfit
        prices = data['Close'].tail(self.volatility_window).values
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        
        # Normalize slope to percentage
        price_trend = slope / prices.mean()
        
        if current_vol > historical_vol * 1.5:
            self.market_regime = "volatile"
        elif abs(price_trend) > historical_vol * 2:
            self.market_regime = "trending"
        else:
            self.market_regime = "normal"
            
        return self.market_regime

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
        # 確保數據類型正確
        df['Close'] = df['Close'].astype(float)
        df['Volume'] = df['Volume'].astype(float)
        
        # 計算價格和成交量變化
        df['PriceChange'] = df['Close'].pct_change().fillna(0)
        df['VolumeChange'] = df['Volume'].pct_change().fillna(0)
        
        # 計算移動平均，使用 min_periods 參數確保有足夠的數據才進行計算
        df['MA5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        df['MA20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        df['VMA5'] = df['Volume'].rolling(window=5, min_periods=1).mean()
        df['VMA20'] = df['Volume'].rolling(window=20, min_periods=1).mean()
        
        # 使用 ffill() 替代 fillna(method='ffill')
        df['MA5'] = df['MA5'].ffill()
        df['MA20'] = df['MA20'].ffill()
        df['VMA5'] = df['VMA5'].ffill()
        df['VMA20'] = df['VMA20'].ffill()
        
        # 如果仍有空值，使用當前值填充
        df['MA5'] = df['MA5'].fillna(df['Close'])
        df['MA20'] = df['MA20'].fillna(df['Close'])
        df['VMA5'] = df['VMA5'].fillna(df['Volume'])
        df['VMA20'] = df['VMA20'].fillna(df['Volume'])
        
        # 添加機構投資者數據
        df['Foreign'] = 0  # 外資買賣超
        df['Trust'] = 0    # 投信買賣超
        df['Dealer'] = 0   # 自營商買賣超
        
        # 添加信用交易數據
        df['MarginBalance'] = 0  # 融資餘額
        df['ShortBalance'] = 0   # 融券餘額
        
        # 添加券商數據
        df['TopBrokerBuy'] = 0  # 主力券商買超
        df['TopBrokerSell'] = 0  # 主力券商賣超
        df['BrokerConcentration'] = 0  # 券商集中度
        
        # 添加持股數據
        df['ForeignHolding'] = 0  # 外資持股比例
        df['DirectorHolding'] = 0  # 董監持股
        df['InstitutionalHolding'] = 0  # 法人持股
        
        # 添加風險指標
        df['Volatility'] = df['Close'].pct_change().rolling(window=20, min_periods=1).std().fillna(0)  # 波動率
        df['TurnoverRate'] = df['Volume'] / 1000000  # 周轉率
        df['BidAskSpread'] = 0  # 買賣價差
        
        return df
    
    @staticmethod
    async def fetch_institutional_data(symbol: str, date: str) -> Dict[str, float]:
        """Fetch institutional investors data."""
        try:
            # TODO: Implement actual API call to get institutional data
            return {
                'foreign_net': 0.0,
                'trust_net': 0.0,
                'dealer_net': 0.0
            }
        except Exception as e:
            logger.error(f"Error fetching institutional data: {str(e)}")
            return {}

    @staticmethod
    async def fetch_margin_data(symbol: str, date: str) -> Dict[str, float]:
        """Fetch margin trading data."""
        try:
            # TODO: Implement actual API call to get margin trading data
            return {
                'margin_balance': 0.0,
                'short_balance': 0.0,
                'margin_change': 0.0,
                'short_change': 0.0
            }
        except Exception as e:
            logger.error(f"Error fetching margin data: {str(e)}")
            return {}

    @staticmethod
    async def fetch_broker_data(symbol: str, date: str) -> Dict[str, Any]:
        """Fetch broker trading data."""
        try:
            # TODO: Implement actual API call to get broker data
            return {
                'top_buyers': [],  # List of top buying brokers
                'top_sellers': [],  # List of top selling brokers
                'concentration': 0.0,  # Broker concentration ratio
                'major_branches': {  # Major branch activities
                    'buy': 0.0,
                    'sell': 0.0,
                    'net': 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error fetching broker data: {str(e)}")
            return {}
            
    @staticmethod
    async def fetch_shareholding_data(symbol: str, date: str) -> Dict[str, Any]:
        """Fetch shareholding structure data."""
        try:
            # TODO: Implement actual API call to get shareholding data
            return {
                'foreign_holding': 0.0,  # Foreign shareholding %
                'director_holding': 0.0,  # Director shareholding %
                'institutional_holding': 0.0,  # Institutional shareholding %
                'distribution': {  # Shareholding distribution
                    'large': 0.0,  # >1000 lots
                    'medium': 0.0,  # 400-1000 lots
                    'small': 0.0  # <400 lots
                }
            }
        except Exception as e:
            logger.error(f"Error fetching shareholding data: {str(e)}")
            return {}
            
    @staticmethod
    async def fetch_market_depth(symbol: str) -> Dict[str, Any]:
        """Fetch market depth data."""
        try:
            # TODO: Implement actual API call to get market depth
            return {
                'bid_ask_spread': 0.0,
                'market_depth': {
                    'bid_levels': [],
                    'ask_levels': []
                },
                'order_book': {
                    'bid_volume': 0,
                    'ask_volume': 0
                }
            }
        except Exception as e:
            logger.error(f"Error fetching market depth: {str(e)}")
            return {}
            
    @staticmethod
    async def fetch_block_trades(symbol: str, date: str) -> List[Dict[str, Any]]:
        """Fetch block trade data."""
        try:
            # TODO: Implement actual API call to get block trades
            return [{
                'time': '',
                'price': 0.0,
                'volume': 0,
                'buyer': '',
                'seller': ''
            }]
        except Exception as e:
            logger.error(f"Error fetching block trades: {str(e)}")
            return []
            
    @staticmethod
    async def fetch_risk_metrics(symbol: str) -> Dict[str, Any]:
        """Fetch risk-related metrics."""
        try:
            # TODO: Implement actual API call to get risk metrics
            return {
                'volatility': 0.0,
                'liquidity_risk': 0.0,
                'concentration_risk': 0.0,
                'market_impact': 0.0
            }
        except Exception as e:
            logger.error(f"Error fetching risk metrics: {str(e)}")
            return {}

    @staticmethod
    async def fetch_data(symbol: str) -> Optional[pd.DataFrame]:
        """Fetch market data for analysis."""
        try:
            logger.info(f"開始獲取 {symbol} 的市場數據...")
            
            # 確保股票代碼格式正確
            if not symbol.isdigit():
                logger.error(f"無效的股票代碼格式: {symbol}")
                return None
                
            # 嘗試獲取台股數據
            stock = yf.Ticker(f"{symbol}.TW")
            logger.info(f"正在從 Yahoo Finance 獲取 {symbol} 的歷史數據...")
            
            # 獲取更長時間的數據以確保計算準確性
            df = stock.history(period="120d")  # 獲取120天數據以確保有足夠的歷史數據計算指標
            
            if df.empty:
                logger.warning(f"未找到股票 {symbol} 的數據")
                return None
                
            if len(df) < 20:  # 至少需要20天的數據來計算基本指標
                logger.warning(f"股票 {symbol} 的數據量不足: {len(df)} 天")
                return None
                
            logger.info(f"成功獲取 {len(df)} 天的歷史數據")
            
            # 檢查必要的列是否存在
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"數據缺少必要的列: {missing_columns}")
                return None
                
            # 檢查是否有空值
            null_counts = df[required_columns].isnull().sum()
            if null_counts.any():
                logger.warning(f"數據中存在空值:\n{null_counts[null_counts > 0]}")
                # 使用前一個有效值填充空值
                df = df.fillna(method='ffill')
                
            # 確保數據類型正確
            df['Volume'] = df['Volume'].astype(float)
            df['Close'] = df['Close'].astype(float)
            
            logger.info("開始計算基本指標...")
            df = MarketDataFetcher._calculate_basic_metrics(df)
            
            # 驗證計算結果
            if df['MA5'].isnull().any() or df['MA20'].isnull().any():
                logger.warning("移動平均計算可能不完整")
                
            if df['VMA5'].isnull().any() or df['VMA20'].isnull().any():
                logger.warning("成交量移動平均計算可能不完整")
                
            logger.info("基本指標計算完成")
            
            # 只返回最近60天的數據用於分析
            df = df.tail(60)
            
            return df
            
        except Exception as e:
            logger.error(f"獲取數據時發生錯誤: {str(e)}")
            import traceback
            logger.error(f"詳細錯誤信息:\n{traceback.format_exc()}")
            return None

class ChipsAnalysisAgent:
    """Agent for performing chips analysis on stock data."""

    def __init__(self, symbol: str, model_name: str = "gpt-4o"):
        self.symbol = symbol
        self._data: Optional[pd.DataFrame] = None
        self.model_name = model_name
        self.system_prompt = self._load_system_prompt()
        self.indicators: Dict[str, ChipsIndicator] = {}
        self.market_analyzer = MarketConditionAnalyzer()

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

    async def calculate_institutional_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate institutional investors indicator."""
        if self._data is None:
            return None
            
        try:
            inst_data = await MarketDataFetcher.fetch_institutional_data(
                self.symbol, 
                self._data.index[-1].strftime("%Y-%m-%d")
            )
            
            if not inst_data:
                return None
                
            # Calculate signal based on institutional behavior
            total_net = sum([
                inst_data['foreign_net'],
                inst_data['trust_net'],
                inst_data['dealer_net']
            ])
            
            if total_net > 0:
                signal = "buy"
            elif total_net < 0:
                signal = "sell"
            else:
                signal = "hold"
                
            return ChipsIndicator(
                name="Institutional",
                value=total_net,
                signal=signal,
                metadata=inst_data
            )
            
        except Exception as e:
            logger.error(f"Error calculating institutional indicator: {str(e)}")
            return None
            
    async def calculate_margin_trading_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate margin trading indicator."""
        if self._data is None:
            return None
            
        try:
            margin_data = await MarketDataFetcher.fetch_margin_data(
                self.symbol, 
                self._data.index[-1].strftime("%Y-%m-%d")
            )
            
            if not margin_data:
                return None
                
            # Calculate signal based on margin trading changes
            margin_ratio = margin_data['margin_change'] / margin_data['short_change'] if margin_data['short_change'] != 0 else 0
            
            if margin_ratio > 1.5:
                signal = "buy"
            elif margin_ratio < 0.5:
                signal = "sell"
            else:
                signal = "hold"
                
            return ChipsIndicator(
                name="MarginTrading",
                value=margin_ratio,
                signal=signal,
                metadata=margin_data
            )
            
        except Exception as e:
            logger.error(f"Error calculating margin trading indicator: {str(e)}")
            return None

    def calculate_concentration_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate volume concentration indicator."""
        if self._data is None:
            return None
            
        try:
            # Calculate volume concentration in different time periods
            volume_data = self._data['Volume'].tail(20)
            total_volume = volume_data.sum()
            
            # Calculate concentration metrics
            concentration = {
                'opening_hour': volume_data.head(5).sum() / total_volume,
                'lunch_break': volume_data[5:10].sum() / total_volume,
                'closing_hour': volume_data[15:].sum() / total_volume
            }
            
            # Determine signal based on closing hour concentration
            if concentration['closing_hour'] > 0.4:
                signal = "buy"
            elif concentration['closing_hour'] < 0.2:
                signal = "sell"
            else:
                signal = "hold"
                
            return ChipsIndicator(
                name="Concentration",
                value=concentration['closing_hour'],
                signal=signal,
                metadata=concentration
            )
            
        except Exception as e:
            logger.error(f"Error calculating concentration indicator: {str(e)}")
            return None

    async def calculate_broker_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate broker activity indicator."""
        if self._data is None:
            return None
            
        try:
            broker_data = await MarketDataFetcher.fetch_broker_data(
                self.symbol,
                self._data.index[-1].strftime("%Y-%m-%d")
            )
            
            if not broker_data:
                return None
                
            # Calculate net broker activity
            net_activity = broker_data['major_branches']['net']
            concentration = broker_data['concentration']
            
            # Determine signal based on broker activity and concentration
            if net_activity > 0 and concentration > 0.3:
                signal = "buy"
            elif net_activity < 0 and concentration > 0.3:
                signal = "sell"
            else:
                signal = "hold"
                
            return ChipsIndicator(
                name="BrokerActivity",
                value=net_activity,
                signal=signal,
                metadata={
                    **broker_data,
                    'activity_concentration': concentration
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating broker indicator: {str(e)}")
            return None

    async def calculate_shareholding_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate shareholding structure indicator."""
        if self._data is None:
            return None
            
        try:
            holding_data = await MarketDataFetcher.fetch_shareholding_data(
                self.symbol,
                self._data.index[-1].strftime("%Y-%m-%d")
            )
            
            if not holding_data:
                return None
                
            # Calculate institutional dominance
            inst_total = (
                holding_data['foreign_holding'] +
                holding_data['institutional_holding']
            )
            
            # Calculate large lot concentration
            large_lot_ratio = holding_data['distribution']['large']
            
            # Determine signal based on institutional holding and concentration
            if inst_total > 60 and large_lot_ratio > 0.5:
                signal = "buy"
            elif inst_total < 40 or large_lot_ratio < 0.3:
                signal = "sell"
            else:
                signal = "hold"
                
            return ChipsIndicator(
                name="Shareholding",
                value=inst_total,
                signal=signal,
                metadata=holding_data
            )
            
        except Exception as e:
            logger.error(f"Error calculating shareholding indicator: {str(e)}")
            return None

    async def calculate_block_trade_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate block trade indicator."""
        if self._data is None:
            return None
            
        try:
            block_trades = await MarketDataFetcher.fetch_block_trades(
                self.symbol,
                self._data.index[-1].strftime("%Y-%m-%d")
            )
            
            if not block_trades:
                return None
                
            # Calculate block trade metrics
            total_volume = sum(trade['volume'] for trade in block_trades)
            avg_price = sum(trade['price'] * trade['volume'] for trade in block_trades) / total_volume if total_volume > 0 else 0
            
            # Compare with current price
            current_price = self._data['Close'].iloc[-1]
            price_diff = (avg_price - current_price) / current_price if current_price > 0 else 0
            
            # Determine signal based on block trade price and volume
            if price_diff > 0.02 and total_volume > self._data['Volume'].mean():
                signal = "buy"
            elif price_diff < -0.02 and total_volume > self._data['Volume'].mean():
                signal = "sell"
            else:
                signal = "hold"
                
            return ChipsIndicator(
                name="BlockTrade",
                value=price_diff,
                signal=signal,
                metadata={
                    'total_volume': total_volume,
                    'average_price': avg_price,
                    'trade_count': len(block_trades),
                    'price_premium': price_diff
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating block trade indicator: {str(e)}")
            return None

    async def calculate_risk_indicator(self) -> Optional[ChipsIndicator]:
        """Calculate comprehensive risk indicator."""
        if self._data is None:
            return None
            
        try:
            risk_data = await MarketDataFetcher.fetch_risk_metrics(self.symbol)
            
            if not risk_data:
                return None
                
            # Calculate composite risk score (0-100)
            risk_score = sum([
                risk_data['volatility'] * 0.3,
                risk_data['liquidity_risk'] * 0.3,
                risk_data['concentration_risk'] * 0.2,
                risk_data['market_impact'] * 0.2
            ])
            
            # Determine signal based on risk score
            if risk_score < 30:
                signal = "buy"
            elif risk_score > 70:
                signal = "sell"
            else:
                signal = "hold"
                
            return ChipsIndicator(
                name="Risk",
                value=risk_score,
                signal=signal,
                metadata=risk_data
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk indicator: {str(e)}")
            return None

    def _calculate_composite_signal(self) -> Tuple[str, Dict[str, Any]]:
        """Calculate composite signal from all indicators."""
        if not self.indicators:
            return "hold", {}
            
        # Count signals
        signal_counts = {"buy": 0, "sell": 0, "hold": 0}
        signal_details = {}
        valid_indicators = 0
        
        for name, indicator in self.indicators.items():
            if name == "overall":
                continue
                
            # 檢查指標是否有有效數據
            has_valid_data = False
            if name == "volume" or name == "price_volume":
                has_valid_data = True
            elif name == "institutional":
                has_valid_data = any(v != 0 for v in indicator.metadata.values())
            elif name == "margin_trading":
                has_valid_data = any(v != 0 for v in indicator.metadata.values())
            elif name == "broker":
                has_valid_data = indicator.metadata['activity_concentration'] > 0
            elif name == "shareholding":
                has_valid_data = indicator.value > 0
            elif name == "block_trade":
                has_valid_data = indicator.metadata['total_volume'] > 0
            elif name == "risk":
                has_valid_data = any(v > 0 for v in indicator.metadata.values())
                
            if has_valid_data:
                signal_counts[indicator.signal] += 1
                valid_indicators += 1
                
            signal_details[name] = {
                "signal": indicator.signal,
                "valid_data": has_valid_data
            }
            
        # 如果有效指標太少，返回 hold
        if valid_indicators < 3:  # 至少需要3個有效指標
            return "hold", signal_details
            
        # Determine final signal
        max_count = max(signal_counts.values())
        final_signals = [signal for signal, count in signal_counts.items() if count == max_count]
        
        if len(final_signals) > 1:
            final_signal = "hold"  # If tie, be conservative
        else:
            final_signal = final_signals[0]
            
        return final_signal, signal_details

    async def analyze(self) -> Dict[str, ChipsIndicator]:
        """Perform chips analysis."""
        try:
            # Fetch market data
            self._data = await MarketDataFetcher.fetch_data(self.symbol)
            if self._data is None:
                return {}

            # Analyze market condition
            market_condition = self.market_analyzer.analyze_market_condition(self._data)
            logger.info(f"Current market condition: {market_condition}")

            # Calculate all indicators
            self.indicators = {}
            
            # Volume indicator
            if vol_ind := self.calculate_volume_indicator():
                self.indicators["volume"] = vol_ind
            
            # Price-volume indicator
            if pv_ind := self.calculate_price_volume_indicator():
                self.indicators["price_volume"] = pv_ind
            
            # Institutional indicator
            if inst_ind := await self.calculate_institutional_indicator():
                self.indicators["institutional"] = inst_ind
            
            # Margin trading indicator
            if margin_ind := await self.calculate_margin_trading_indicator():
                self.indicators["margin_trading"] = margin_ind
            
            # Concentration indicator
            if conc_ind := self.calculate_concentration_indicator():
                self.indicators["concentration"] = conc_ind
            
            # Broker indicator
            if broker_ind := await self.calculate_broker_indicator():
                self.indicators["broker"] = broker_ind
            
            # Shareholding indicator
            if holding_ind := await self.calculate_shareholding_indicator():
                self.indicators["shareholding"] = holding_ind
            
            # Block trade indicator
            if block_ind := await self.calculate_block_trade_indicator():
                self.indicators["block_trade"] = block_ind
            
            # Risk indicator
            if risk_ind := await self.calculate_risk_indicator():
                self.indicators["risk"] = risk_ind

            # 準備 LLM 分析所需的數據
            analysis_data = {
                "symbol": self.symbol,
                "market_condition": market_condition,
                "institutional_investors": {
                    "foreign": self.indicators.get("institutional", {}).metadata.get("foreign_net", 0),
                    "trust": self.indicators.get("institutional", {}).metadata.get("trust_net", 0),
                    "dealer": self.indicators.get("institutional", {}).metadata.get("dealer_net", 0)
                },
                "margin_trading": {
                    "margin_balance": self.indicators.get("margin_trading", {}).metadata.get("margin_balance", 0),
                    "short_balance": self.indicators.get("margin_trading", {}).metadata.get("short_balance", 0),
                    "margin_ratio": self.indicators.get("margin_trading", {}).value if "margin_trading" in self.indicators else 0
                },
                "volume_analysis": {
                    "5d_avg": self.indicators.get("volume", {}).metadata.get("avg_volume_5d", 0),
                    "20d_avg": self.indicators.get("volume", {}).metadata.get("avg_volume_20d", 0),
                    "trend": self.indicators.get("volume", {}).metadata.get("trend", "Stable")
                },
                "broker_analysis": {
                    "net_activity": self.indicators.get("broker", {}).value if "broker" in self.indicators else 0,
                    "concentration": self.indicators.get("broker", {}).metadata.get("activity_concentration", 0)
                },
                "shareholding": {
                    "institutional_total": self.indicators.get("shareholding", {}).value if "shareholding" in self.indicators else 0,
                    "large_lot_ratio": self.indicators.get("shareholding", {}).metadata.get("distribution", {}).get("large", 0)
                },
                "block_trades": {
                    "count": self.indicators.get("block_trade", {}).metadata.get("trade_count", 0),
                    "volume": self.indicators.get("block_trade", {}).metadata.get("total_volume", 0),
                    "price_premium": self.indicators.get("block_trade", {}).metadata.get("price_premium", 0)
                },
                "risk_metrics": {
                    "risk_score": self.indicators.get("risk", {}).value if "risk" in self.indicators else 0,
                    "volatility": self.indicators.get("risk", {}).metadata.get("volatility", 0),
                    "liquidity_risk": self.indicators.get("risk", {}).metadata.get("liquidity_risk", 0)
                }
            }

            # 使用 LLM 進行分析
            messages = [
                Message(role="system", content=self.system_prompt),
                Message(role="user", content=f"請根據以下數據，對 {self.symbol} 進行籌碼分析：\n{json.dumps(analysis_data, indent=2, ensure_ascii=False)}")
            ]
            
            llm_analysis = await aquery_llm(
                messages=messages,
                model=self.model_name
            )
            
            # Calculate composite signal
            final_signal, signal_details = self._calculate_composite_signal()
            
            # Add overall assessment with LLM analysis
            self.indicators["overall"] = ChipsIndicator(
                name="overall",
                value=0.0,
                signal=final_signal,
                metadata={
                    "analysis": f"Market condition: {market_condition}",
                    "signal_details": signal_details,
                    "llm_analysis": llm_analysis
                }
            )

            return {k: v for k, v in self.indicators.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {}

    def get_analysis_summary(self) -> str:
        """Generate a readable summary of the analysis."""
        if not self.indicators:
            return "No analysis data available"

        summary = []
        
        # Add market condition and LLM analysis
        if overall := self.indicators.get("overall"):
            market_condition = overall.metadata["analysis"].split(": ")[1]
            summary.append(f"市場狀態: {market_condition}")
            
            # Add LLM analysis if available
            if llm_analysis := overall.metadata.get("llm_analysis"):
                summary.append(f"\nLLM 籌碼分析:\n{llm_analysis}")
        
        # Add volume analysis
        if vol := self.indicators.get("volume"):
            summary.append(
                f"\n成交量分析: {vol.signal.upper()}\n"
                f"- 5日均量: {vol.metadata['avg_volume_5d']:,.0f}\n"
                f"- 20日均量: {vol.metadata['avg_volume_20d']:,.0f}\n"
                f"- 趨勢: {vol.metadata['trend']}"
            )
        
        # Add price-volume analysis
        if pv := self.indicators.get("price_volume"):
            summary.append(
                f"\n價量分析: {pv.signal.upper()}\n"
                f"- 5日相關性: {pv.metadata['correlation_5d']:.2f}\n"
                f"- 20日相關性: {pv.metadata['correlation_20d']:.2f}"
            )
            
        # Add institutional analysis
        if inst := self.indicators.get("institutional"):
            summary.append(
                f"\n法人分析: {inst.signal.upper()}\n"
                f"- 外資: {inst.metadata['foreign_net']:,.0f}\n"
                f"- 投信: {inst.metadata['trust_net']:,.0f}\n"
                f"- 自營商: {inst.metadata['dealer_net']:,.0f}"
            )
            
        # Add margin trading analysis
        if margin := indicators.get("margin_trading"):
            summary.append(
                f"\n信用交易分析: {margin.signal.upper()}\n"
                f"- 融資餘額: {margin.metadata['margin_balance']:,.0f}\n"
                f"- 融券餘額: {margin.metadata['short_balance']:,.0f}\n"
                f"- 融資/融券比: {margin.value:.2f}"
            )
            
        # Add concentration analysis
        if conc := self.indicators.get("concentration"):
            summary.append(
                f"\n量能集中度分析: {conc.signal.upper()}\n"
                f"- 開盤時段: {conc.metadata['opening_hour']:.1%}\n"
                f"- 午盤時段: {conc.metadata['lunch_break']:.1%}\n"
                f"- 尾盤時段: {conc.metadata['closing_hour']:.1%}"
            )
        
        # Add broker analysis
        if broker := self.indicators.get("broker"):
            summary.append(
                f"\n券商動向分析: {broker.signal.upper()}\n"
                f"- 買賣超: {broker.value:,.0f}\n"
                f"- 集中度: {broker.metadata['activity_concentration']:.1%}\n"
                f"- 分點買賣超: {broker.metadata['major_branches']['net']:,.0f}"
            )
            
        # Add shareholding analysis
        if holding := self.indicators.get("shareholding"):
            summary.append(
                f"\n持股結構分析: {holding.signal.upper()}\n"
                f"- 法人持股: {holding.value:.1%}\n"
                f"- 大戶持股: {holding.metadata['distribution']['large']:.1%}\n"
                f"- 董監持股: {holding.metadata['director_holding']:.1%}"
            )
            
        # Add block trade analysis
        if block := self.indicators.get("block_trade"):
            summary.append(
                f"\n大額交易分析: {block.signal.upper()}\n"
                f"- 交易次數: {block.metadata['trade_count']}\n"
                f"- 總成交量: {block.metadata['total_volume']:,.0f}\n"
                f"- 溢價率: {block.metadata['price_premium']:.1%}"
            )
            
        # Add risk analysis
        if risk := self.indicators.get("risk"):
            summary.append(
                f"\n風險評估: {risk.signal.upper()}\n"
                f"- 風險分數: {risk.value:.1f}\n"
                f"- 波動度: {risk.metadata['volatility']:.1%}\n"
                f"- 流動性風險: {risk.metadata['liquidity_risk']:.1f}"
            )
        
        return "\n".join(summary)

async def main():
    """Test function."""
    symbol = "2330"
    
    try:
        agent = ChipsAnalysisAgent(symbol)
        
        # Run real-time analysis
        indicators = await agent.analyze()
        
        if indicators:
            logger.info("\n籌碼分析摘要:")
            logger.info("=" * 50)
            
            # 市場狀態
            if overall := indicators.get("overall"):
                market_condition = overall.metadata["analysis"].split(": ")[1]
                logger.info(f"市場狀態: {market_condition}")
                logger.info(f"綜合建議: {overall.signal.upper()}")
            
            logger.info("\n籌碼指標分析:")
            logger.info("-" * 30)
            
            # 機構投資者動向
            if inst := indicators.get("institutional"):
                logger.info("\n1. 法人籌碼:")
                logger.info(f"- 外資: {inst.metadata['foreign_net']:,.0f}")
                logger.info(f"- 投信: {inst.metadata['trust_net']:,.0f}")
                logger.info(f"- 自營商: {inst.metadata['dealer_net']:,.0f}")
                logger.info(f"- 建議: {inst.signal.upper()}")
            
            # 融資融券
            if margin := indicators.get("margin_trading"):
                logger.info("\n2. 信用交易:")
                logger.info(f"- 融資餘額: {margin.metadata['margin_balance']:,.0f}")
                logger.info(f"- 融券餘額: {margin.metadata['short_balance']:,.0f}")
                logger.info(f"- 建議: {margin.signal.upper()}")
            
            # 券商動向
            if broker := indicators.get("broker"):
                logger.info("\n3. 券商動向:")
                logger.info(f"- 主力買賣超: {broker.value:,.0f}")
                logger.info(f"- 集中度: {broker.metadata['activity_concentration']:.1%}")
                logger.info(f"- 分點買賣超: {broker.metadata['major_branches']['net']:,.0f}")
                logger.info(f"- 建議: {broker.signal.upper()}")
            
            # 持股分布
            if holding := indicators.get("shareholding"):
                logger.info("\n4. 持股分布:")
                logger.info(f"- 法人持股: {holding.value:.1%}")
                logger.info(f"- 大戶持股: {holding.metadata['distribution']['large']:.1%}")
                logger.info(f"- 董監持股: {holding.metadata['director_holding']:.1%}")
                logger.info(f"- 建議: {holding.signal.upper()}")
            
            # 大額交易
            if block := indicators.get("block_trade"):
                logger.info("\n5. 大額交易:")
                logger.info(f"- 交易次數: {block.metadata['trade_count']}")
                logger.info(f"- 總成交量: {block.metadata['total_volume']:,.0f}")
                logger.info(f"- 溢價率: {block.metadata['price_premium']:.1%}")
                logger.info(f"- 建議: {block.signal.upper()}")
            
            # 風險指標
            if risk := indicators.get("risk"):
                logger.info("\n6. 風險評估:")
                logger.info(f"- 風險分數: {risk.value:.1f}")
                logger.info(f"- 波動度: {risk.metadata['volatility']:.1%}")
                logger.info(f"- 流動性風險: {risk.metadata['liquidity_risk']:.1f}")
                logger.info(f"- 建議: {risk.signal.upper()}")
            
            logger.info("\n" + "=" * 50)
            
    except Exception as e:
        logger.error(f"分析錯誤: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 