"""Capital analysis prompt templates and generators.

This module contains prompt templates and generators for capital analysis.
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MarketData:
    """Market data for analysis."""
    symbol: str
    date: str
    price: float
    price_change: float
    volume: float
    market_condition: str

@dataclass
class InstitutionalData:
    """Institutional investors data."""
    foreign_net: float
    trust_net: float
    dealer_net: float
    foreign_holding: float

@dataclass
class MarginData:
    """Margin trading data."""
    margin_balance: float
    short_balance: float

@dataclass
class AnalysisData:
    """Combined analysis data."""
    market: MarketData
    institutional: InstitutionalData
    margin: MarginData

class CapitalPromptGenerator:
    """Generator for capital analysis prompts."""
    
    @staticmethod
    def format_number(number: float, use_percentage: bool = False) -> str:
        """Format number for display."""
        return f"{number:.2f}%" if use_percentage else f"{number:,.0f}"

    @classmethod
    def format_sections(cls, data: AnalysisData) -> Dict[str, List[str]]:
        """Format all data sections."""
        return {
            "Market Information": [
                f"Symbol: {data.market.symbol}",
                f"Date: {data.market.date}",
                f"Close: {cls.format_number(data.market.price)}",
                f"Change: {cls.format_number(data.market.price_change)}",
                f"Volume: {cls.format_number(data.market.volume)}",
                f"Market Condition: {data.market.market_condition}"
            ],
            "Institutional Net (5-day)": [
                f"Foreign: {cls.format_number(data.institutional.foreign_net)}",
                f"Trust: {cls.format_number(data.institutional.trust_net)}",
                f"Dealer: {cls.format_number(data.institutional.dealer_net)}",
                f"Foreign Holding: {cls.format_number(data.institutional.foreign_holding, True)}"
            ],
            "Margin Trading": [
                f"Margin Balance: {cls.format_number(data.margin.margin_balance)}",
                f"Short Balance: {cls.format_number(data.margin.short_balance)}"
            ]
        }

    @staticmethod
    def generate_system_prompt() -> str:
        """Generate analysis prompt."""
        with open("prompts/capital_instruction.md", "r") as file:
            prompt = file.read()
        return prompt

    @classmethod
    def get_user_prompt(cls, company: str, data: AnalysisData) -> str:
        """Generate user prompt with formatted market data.
        
        Args:
            data: Analysis data containing market, institutional, and margin information
            company: Company stock symbol
            
        Returns:
            Formatted prompt string with market data and analysis request
        """
        # Start with the base prompt
        prompt_parts = [
            f"# Capital Analysis Request for {company}",
            "\nPlease analyze the following market data and provide a comprehensive capital analysis report.\n"
        ]
        
        # Add formatted data sections
        sections = cls.format_sections(data)
        for title, items in sections.items():
            prompt_parts.append(f"\n## {title}")
            prompt_parts.extend(f"- {item}" for item in items)
            
        # Add analysis focus points
        prompt_parts.extend([
            "\n## Analysis Focus",
            "Please provide detailed analysis on:",
            "1. Market Position and Trend Analysis",
            "   - Current market position and price trend",
            "   - Volume analysis and implications",
            "   - Market condition impact",
            "",
            "2. Institutional Investors Analysis",
            "   - Foreign investors' position and strategy",
            "   - Trust and dealer activities",
            "   - Overall institutional sentiment",
            "",
            "3. Margin Trading Analysis",
            "   - Margin trading pressure",
            "   - Short selling impact",
            "   - Potential risks and opportunities",
            "",
            "4. Comprehensive Risk Assessment",
            "   - Key risk factors",
            "   - Support and resistance levels",
            "   - Monitoring points for position management"
        ])
        
        return "\n".join(prompt_parts)