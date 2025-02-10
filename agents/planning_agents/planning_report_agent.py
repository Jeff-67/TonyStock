"""Module for generating comprehensive analysis reports for companies using LLM."""

import logging
import asyncio
from typing import Dict

from opik import track

from prompts.agents.knowledge import finance_agent_prompt, chip_agent_prompt, technical_analysis_prompt
from prompts.agents.main import planning_prompt, writing_planning_prompt
from tools.llm_api import aquery_llm
from utils.stock_utils import stock_name_to_id

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_planning_report_prompt(
    company_news: str, stock_id: str | None, user_message: str
) -> str:
    """Generate prompt for search framework analysis."""
    company_instruction = finance_agent_prompt(stock_id=stock_id)
    chip_instruction = chip_agent_prompt()
    technical_analysis_instruction = technical_analysis_prompt()
    writing_instruction = writing_planning_prompt()

    return planning_prompt(
        company_news=company_news,
        company_instruction=company_instruction,
        chip_instruction=chip_instruction,
        technical_analysis_instruction=technical_analysis_instruction,
        writing_instruction=writing_instruction,
        user_message=user_message
    )


@track()
async def generate_planning_report(
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
    prompt = get_planning_report_prompt(str(company_news), stock_id, user_message)

    try:
        messages = [{"role": "user", "content": prompt}]
        response, _ = await aquery_llm(
            messages=messages,
            model="claude-3-5-sonnet-latest",
            provider="anthropic",
        )

        if not response.choices[0].message.content:
            raise ValueError("No response from LLM")

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error generating planning report: {str(e)}")
        raise


async def main(company_name: str, user_message: str, news_data: Dict[str, str] | None = None):
    """Main execution function for planning report generation.
    
    Args:
        company_name: Name of the company to analyze
        user_message: User's query or request
        news_data: Optional pre-collected news data. If None, empty dict will be used.
    """
    try:
        logger.info(f"Generating planning report for {company_name}")
        
        # Use empty dict if no news data provided
        news_data = news_data or {}
        
        # Generate the planning report
        report = await generate_planning_report(
            company_news=news_data,
            company_name=company_name,
            user_message=user_message
        )
        
        logger.info("Successfully generated planning report")
        print("\nPlanning Report:")
        print("=" * 80)
        print(report)
        print("=" * 80)
        
        return report
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main(
        company_name="京鼎",
        user_message="請分析京鼎(3413)近期走勢"
    ))
