"""Capital analysis prompt templates and generators.

This module contains prompt templates and generators for capital analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

class AnalysisSection(Enum):
    """Analysis sections for chip analysis."""
    INSTITUTIONAL = "institutional"
    MAJOR_PLAYERS = "major_players"
    MARGIN_TRADING = "margin_trading"
    VOLUME = "volume"
    SPECIAL_SITUATIONS = "special_situations"
    RISK_MONITORING = "risk_monitoring"

@dataclass
class InstitutionalAnalysis:
    """Institutional investors analysis structure."""
    
    @staticmethod
    def foreign_investors() -> Dict[str, List[str]]:
        return {
            "daily_movement": [
                "買賣超金額",
                "連續買賣天數",
                "總持股變化"
            ],
            "position_analysis": [
                "總持股比例",
                "歷史持股區間",
                "成本分布分析"
            ],
            "trading_patterns": [
                "大額交易分析",
                "程式交易模式",
                "選擇權部位關聯"
            ]
        }
        
    @staticmethod
    def investment_trust() -> Dict[str, List[str]]:
        return {
            "position_changes": [
                "買賣超模式",
                "基金規模影響",
                "作帳行為分析"
            ],
            "fund_flow": [
                "新基金發行",
                "基金贖回壓力",
                "產業輪動模式"
            ]
        }
        
    @staticmethod
    def proprietary_traders() -> Dict[str, List[str]]:
        return {
            "trading_analysis": [
                "趨勢交易vs避險",
                "選擇權造市行為",
                "程式交易活動"
            ],
            "risk_indicators": [
                "買賣權比變化",
                "波動率交易",
                "避險部位變化"
            ]
        }

class CapitalPromptGenerator:
    """Generator for capital analysis prompts."""
    
    @staticmethod
    def format_number(number: float, use_percentage: bool = False) -> str:
        """Format number for display."""
        if use_percentage:
            return f"{number:.2%}"
        return f"{number:,.0f}"
    
    @staticmethod
    def get_data_sections(symbol: str, analysis_data: Dict[str, Any], market_condition: str) -> Dict[str, List[str]]:
        """Get formatted data sections."""
        return {
            "基本資訊": [
                f"股票代號: {symbol}",
                f"日期: {analysis_data['date']}",
                f"收盤價: {CapitalPromptGenerator.format_number(analysis_data['price']['close'])}",
                f"漲跌: {CapitalPromptGenerator.format_number(analysis_data['price']['change'])}",
                f"成交量: {CapitalPromptGenerator.format_number(analysis_data['price']['volume'])}",
                f"市場狀態: {market_condition}"
            ],
            "三大法人買賣超 (近5日)": [
                f"外資: {CapitalPromptGenerator.format_number(analysis_data['institutional']['foreign'])}",
                f"投信: {CapitalPromptGenerator.format_number(analysis_data['institutional']['trust'])}",
                f"自營商: {CapitalPromptGenerator.format_number(analysis_data['institutional']['dealer'])}"
            ],
            "信用交易": [
                f"融資餘額: {CapitalPromptGenerator.format_number(analysis_data['margin']['margin_balance'])}",
                f"融券餘額: {CapitalPromptGenerator.format_number(analysis_data['margin']['short_balance'])}"
            ],
            "持股比例": [
                f"外資持股: {CapitalPromptGenerator.format_number(analysis_data['shareholding']['foreign_holding'], True)}",
                f"投信持股: {CapitalPromptGenerator.format_number(analysis_data['shareholding']['trust_holding'], True)}",
                f"自營商持股: {CapitalPromptGenerator.format_number(analysis_data['shareholding']['dealer_holding'], True)}"
            ]
        }
    
    @staticmethod
    def get_analysis_framework() -> str:
        """Get analysis framework template."""
        return """
## 分析重點

1. 三大法人動向分析
   - 外資動向與意涵
   - 投信操作策略
   - 自營商避險部位

2. 主力籌碼分析
   - 券商分點變化
   - 大額交易特徵
   - 持股結構變化

3. 信用交易分析
   - 融資餘額變化
   - 融券餘額變化
   - 資券比分析

4. 成交量分析
   - 價量配合度
   - 分盤特徵
   - 主力成本

5. 風險監控
   - 籌碼集中度風險
   - 市場結構風險
   - 流動性風險

## 分析要求

請針對以上資料，提供以下分析：

1. 主力籌碼動向與意涵
2. 信用交易壓力與風險
3. 籌碼分布與集中度
4. 關鍵風險因素

注意事項：
- 分析需量化數據支持
- 關注異常變化
- 提供具體觀察重點
- 評估風險程度
"""
    
    @classmethod
    def generate_system_prompt(cls, symbol: str, analysis_data: Dict[str, Any], market_condition: str) -> str:
        """Generate complete system prompt."""
        # Start with header
        prompt = f"""# {symbol} 籌碼分析框架

您是一位專業的台股籌碼分析師，請根據以下資料進行深入分析。

## 市場資料
"""
        # Add data sections
        data_sections = cls.get_data_sections(symbol, analysis_data, market_condition)
        for section, items in data_sections.items():
            prompt += f"\n### {section}\n"
            prompt += "\n".join(f"- {item}" for item in items)
            prompt += "\n"
        
        # Add analysis framework
        prompt += cls.get_analysis_framework()
        
        return prompt
    
    @staticmethod
    def get_user_prompt(symbol: str) -> str:
        """Get user prompt template."""
        return f"請根據上述資料，為 {symbol} 提供完整的籌碼分析報告。" 