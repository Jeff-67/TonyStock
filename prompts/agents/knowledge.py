"""Module containing prompt generation functions for financial analysis agents."""


def finance_agent_prompt(stock_id: str | None = None) -> str:
    """Generate finance agent prompt for stock analysis.

    Creates a specialized prompt for analyzing financial information and news
    related to a specific stock identified by its ID. The prompt includes
    guidance for comprehensive market analysis and news evaluation.

    Args:
        stock_id: The stock identifier to analyze

    Returns:
        Formatted prompt string for the finance agent
    """
    if not stock_id:
        return ""
    with open(
        f"prompts/company_knowledge/{stock_id}_background.md", "r", encoding="utf-8"
    ) as file:
        instruction = file.read()
    return instruction


def technical_agent_prompt() -> str:
    """Generate technical analysis framework prompt.

    Creates a comprehensive prompt for technical analysis using TA-Lib,
    including detailed instructions for chart analysis, indicator usage,
    and trading recommendations.

    Returns:
        Formatted prompt string containing the technical analysis framework
    """
    return """You are a professional technical analysis expert. Please provide a comprehensive market analysis based on the provided technical indicators, including:

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


def capital_agent_prompt() -> str:
    """Generate capital agent prompt for capital industry analysis.

    Creates a specialized prompt for analyzing semiconductor industry news
    and information, including detailed instructions for industry chain

    Returns:
        Formatted prompt string containing the chip analysis framework
    """
    with open("prompts/capital_instruction.md", "r", encoding="utf-8") as file:
        instruction = file.read()
    return instruction
