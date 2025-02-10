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


def technical_analysis_prompt() -> str:
    """Generate technical analysis framework prompt.

    Creates a comprehensive prompt for technical analysis using TA-Lib,
    including detailed instructions for chart analysis, indicator usage,
    and trading recommendations.

    Returns:
        Formatted prompt string containing the technical analysis framework
    """
    with open("prompts/TA_instruction.md", "r", encoding="utf-8") as file:
        instruction = file.read()
    return instruction


def chip_agent_prompt() -> str:
    """Generate chip agent prompt for semiconductor industry analysis.

    Creates a specialized prompt for analyzing semiconductor industry news
    and information, including detailed instructions for industry chain

    Returns:
        Formatted prompt string containing the chip analysis framework
    """
    with open("prompts/chip_instruction.md", "r", encoding="utf-8") as file:
        instruction = file.read()
    return instruction
