"""Module for generating comprehensive analysis reports for companies using LLM."""

import logging
from typing import Dict

from opik import track

from agents.research_agents.search_framework_agent import stock_name_to_id
from prompts.analysis_prompts import analysis_report_prompt
from prompts.system_prompts import finance_agent_prompt, writing_planning_prompt
from tools.llm_api import query_llm

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_analysis_report_prompt(company_news: str, stock_id: str | None) -> str:
    """Generate prompt for search framework analysis."""
    company_instruction = finance_agent_prompt(stock_id=stock_id)
    writing_instruction = writing_planning_prompt()

    return analysis_report_prompt(
        company_news, company_instruction, writing_instruction
    )


@track()
async def generate_analysis_report(
    company_news: Dict[str, str], company_name: str
) -> str:
    """Generate comprehensive search framework using LLM.

    Args:
        company_name: Name of the company to analyze

    Returns:
        Dict containing industry analysis and structured search queries
    """
    stock_id = stock_name_to_id(company_name)
    prompt = get_analysis_report_prompt(str(company_news), stock_id)

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
