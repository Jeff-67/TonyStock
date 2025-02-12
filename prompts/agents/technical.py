"""Technical analysis prompt templates and generators.

This module contains prompt templates and generators for technical analysis.
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class TechnicalData:
    """Technical analysis data."""
    symbol: str
    date: str
    current_price: float
    ma5: float
    ma20: float
    ma60: float
    rsi: float
    macd: float
    macd_signal: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    obv: float

class TechnicalPromptGenerator:
    """Generator for technical analysis prompts."""
    
    @staticmethod
    def format_number(number: float, precision: int = 2) -> str:
        """Format number for display."""
        return f"{number:,.{precision}f}"

    @classmethod
    def format_sections(cls, data: TechnicalData) -> Dict[str, List[str]]:
        """Format all data sections."""
        return {
            "Price & Moving Averages": [
                f"Current Price: {cls.format_number(data.current_price)}",
                f"MA5: {cls.format_number(data.ma5)}",
                f"MA20: {cls.format_number(data.ma20)}",
                f"MA60: {cls.format_number(data.ma60)}"
            ],
            "Momentum Indicators": [
                f"RSI(14): {cls.format_number(data.rsi)}",
                f"MACD: {cls.format_number(data.macd)}",
                f"MACD Signal: {cls.format_number(data.macd_signal)}"
            ],
            "Volatility (Bollinger Bands)": [
                f"Upper Band: {cls.format_number(data.bb_upper)}",
                f"Middle Band: {cls.format_number(data.bb_middle)}",
                f"Lower Band: {cls.format_number(data.bb_lower)}"
            ],
            "Volume": [
                f"On-Balance Volume (OBV): {cls.format_number(data.obv, 0)}"
            ]
        }

    @staticmethod
    def generate_system_prompt() -> str:
        """Generate system prompt for technical analysis."""
        with open("prompts/technical_instruction.md", "r") as file:
            prompt = file.read()
        return prompt
    
    @classmethod
    def get_user_prompt(cls, company: str, data: TechnicalData) -> str:
        """Generate user prompt with formatted technical data.
        
        Args:
            company: Company stock symbol
            data: Technical analysis data containing indicators
            
        Returns:
            Formatted prompt string with technical data and analysis request
        """
        prompt_parts = [
            f"# Technical Analysis Request for {company}",
            "\nPlease analyze the following technical indicators and provide a comprehensive technical analysis report.\n"
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
            "1. Trend Analysis",
            "   - Current trend direction and strength",
            "   - Moving average relationships",
            "   - Potential trend reversal signals",
            "",
            "2. Momentum Analysis",
            "   - RSI overbought/oversold conditions",
            "   - MACD trend and signal line crossovers",
            "   - Overall momentum strength",
            "",
            "3. Volatility Analysis",
            "   - Price position relative to Bollinger Bands",
            "   - Volatility expansion/contraction",
            "   - Support and resistance levels",
            "",
            "4. Volume Analysis",
            "   - OBV trend analysis",
            "   - Volume-price relationships",
            "   - Market participation assessment",
            "",
            "5. Risk Assessment",
            "   - Key technical risk factors",
            "   - Important levels to monitor",
            "   - Position management considerations"
        ])
        
        return "\n".join(prompt_parts)
