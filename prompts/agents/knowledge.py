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
