"""Capital analysis prompt templates and generators.

This module contains prompt templates and generators for capital analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum

@dataclass
class MarketData:
    """Structure for market data analysis."""
    symbol: str
    date: str
    price: float
    price_change: float
    volume: float
    market_condition: str

@dataclass
class InstitutionalData:
    """Structure for institutional investors data."""
    foreign_net: float
    trust_net: float
    dealer_net: float
    foreign_holding: float
    trust_holding: float
    dealer_holding: float

@dataclass
class MarginData:
    """Structure for margin trading data."""
    margin_balance: float
    short_balance: float

@dataclass
class AnalysisData:
    """Combined structure for all analysis data."""
    market: MarketData
    institutional: InstitutionalData
    margin: MarginData

class AnalysisSection(Enum):
    """Analysis sections for chip analysis."""
    INSTITUTIONAL = "Institutional Investors"
    MAJOR_PLAYERS = "Major Players"
    MARGIN_TRADING = "Margin Trading"
    VOLUME = "Volume Analysis"
    RISK = "Risk Analysis"

class AnalysisTemplate:
    """Templates for analysis sections."""
    
    @staticmethod
    def get_header(symbol: str) -> str:
        """Get analysis header template."""
        return f"""# Stock {symbol} Capital Analysis

You are a professional stock market analyst. Please analyze the following data.

## Market Data"""

    @staticmethod
    def get_analysis_framework() -> str:
        """Get analysis framework template."""
        with open("prompts/capital_instruction.md", "r") as file:
            return file.read()
    
    @staticmethod
    def get_analysis_requirements() -> str:
        """Get analysis requirements template."""
        return """
## Analysis Requirements

Please provide analysis on:
1. Major Players Movement and Implications
2. Margin Trading Pressure and Risks
3. Capital Distribution and Concentration
4. Key Risk Factors

Note:
- Support analysis with quantitative data
- Highlight abnormal changes
- Provide specific monitoring points
- Assess risk levels"""

class CapitalPromptGenerator:
    """Generator for capital analysis prompts."""
    
    @staticmethod
    def format_number(number: float, use_percentage: bool = False) -> str:
        """Format number for display."""
        if use_percentage:
            return f"{number:.2f}%"
        return f"{number:,.0f}"
    
    @classmethod
    def format_market_data(cls, data: MarketData) -> List[str]:
        """Format market data section."""
        return [
            f"Symbol: {data.symbol}",
            f"Date: {data.date}",
            f"Close: {cls.format_number(data.price)}",
            f"Change: {cls.format_number(data.price_change)}",
            f"Volume: {cls.format_number(data.volume)}",
            f"Market Condition: {data.market_condition}"
        ]
    
    @classmethod
    def format_institutional_data(cls, data: InstitutionalData) -> Dict[str, List[str]]:
        """Format institutional data sections."""
        return {
            "Institutional Net (5-day)": [
                f"Foreign: {cls.format_number(data.foreign_net)}",
                f"Trust: {cls.format_number(data.trust_net)}",
                f"Dealer: {cls.format_number(data.dealer_net)}"
            ],
            "Shareholding": [
                f"Foreign: {cls.format_number(data.foreign_holding, True)}",
                f"Trust: {cls.format_number(data.trust_holding, True)}",
                f"Dealer: {cls.format_number(data.dealer_holding, True)}"
            ]
        }
    
    @classmethod
    def format_margin_data(cls, data: MarginData) -> List[str]:
        """Format margin trading data."""
        return [
            f"Margin Balance: {cls.format_number(data.margin_balance)}",
            f"Short Balance: {cls.format_number(data.short_balance)}"
        ]
    
    @classmethod
    def generate_system_prompt(cls, data: AnalysisData) -> str:
        """Generate complete system prompt."""
        # Get templates
        header = AnalysisTemplate.get_header(data.market.symbol)
        framework = AnalysisTemplate.get_analysis_framework()
        requirements = AnalysisTemplate.get_analysis_requirements()
        
        # Format data sections
        market_section = cls.format_market_data(data.market)
        inst_sections = cls.format_institutional_data(data.institutional)
        margin_section = cls.format_margin_data(data.margin)
        
        # Build prompt
        prompt = [header]
        
        # Add market data
        prompt.append("\n### Market Information")
        prompt.extend(f"- {item}" for item in market_section)
        
        # Add institutional data
        for title, items in inst_sections.items():
            prompt.append(f"\n### {title}")
            prompt.extend(f"- {item}" for item in items)
        
        # Add margin data
        prompt.append("\n### Margin Trading")
        prompt.extend(f"- {item}" for item in margin_section)
        
        # Add framework and requirements
        prompt.append(framework)
        prompt.append(requirements)
        
        return "\n".join(prompt)
    
    @staticmethod
    def get_user_prompt(symbol: str) -> str:
        """Get user prompt template."""
        return f"Based on the above data, please provide a comprehensive capital analysis report for stock {symbol}." 