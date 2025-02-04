"""Module for generating comprehensive analysis reports for companies using LLM."""

import logging
from typing import Dict

from opik import track

from prompts.agents.knowledge import finance_agent_prompt
from prompts.agents.main import analysis_report_prompt
from prompts.agents.planning import writing_planning_prompt
from tools.llm_api import query_llm
from utils.stock_utils import stock_name_to_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_analysis_report_prompt(
    company_news: str, stock_id: str | None, user_message: str
) -> str:
    """Generate prompt for search framework analysis."""
    company_instruction = finance_agent_prompt(stock_id=stock_id)
    writing_instruction = writing_planning_prompt()

    return analysis_report_prompt(
        company_news, company_instruction, writing_instruction, user_message
    )


@track()
async def generate_analysis_report(
    company_news: Dict[str, str], company_name: str, user_message: str
) -> str:
    """Generate comprehensive search framework using LLM.

    Args:
        company_name: Name of the company to analyze
        user_message: User message
    Returns:
        Dict containing industry analysis and structured search queries
    """
    stock_id = stock_name_to_id(company_name)
    prompt = get_analysis_report_prompt(str(company_news), stock_id, user_message)

    try:
        messages = [{"role": "user", "content": prompt}]
        response, _ = query_llm(
            messages=messages,
            model="claude-3-5-sonnet-latest",
            provider="anthropic",
        )

        if not response.choices[0].message.content:
            raise ValueError("No response from LLM")

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error generating analysis report: {str(e)}")
        raise
