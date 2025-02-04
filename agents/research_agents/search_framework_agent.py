"""Search framework agent module for generating comprehensive company research queries.

This module implements the first step of the analysis framework by using LLM to:
1. Understand company's industry characteristics and value chain
2. Analyze company's position and competitive advantages
3. Generate comprehensive search queries based on this understanding
"""

import json
import logging

from opik import track

from prompts.agents.knowledge import finance_agent_prompt
from prompts.agents.main import searching_framework_prompt
from prompts.agents.planning import search_planning_prompt
from tools.llm_api import query_llm
from tools.time.time_tool import get_current_time
from utils.stock_utils import stock_name_to_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_search_framework_prompt(company_name: str, stock_id: str | None) -> str:
    """Generate prompt for search framework analysis."""
    company_instruction = finance_agent_prompt(stock_id=stock_id)
    searching_instruction = search_planning_prompt()
    current_time = get_current_time()

    return searching_framework_prompt(
        company_name=company_name,
        stock_id=stock_id,
        current_time=current_time,
        company_instruction=company_instruction,
        searching_instruction=searching_instruction,
    )


@track()
def generate_search_framework(company_name: str) -> str:
    """Generate comprehensive search framework using LLM.

    Args:
        company_name: Name of the company to analyze

    Returns:
        Dict containing industry analysis and structured search queries
    """
    stock_id = stock_name_to_id(company_name)
    prompt = get_search_framework_prompt(company_name, stock_id)

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
        logger.error(f"Error generating search framework: {str(e)}")
        raise


async def main():
    """Test function for the search framework agent."""
    test_company = "群聯"
    logger.info(f"Generating search framework for: {test_company}")

    try:
        framework = generate_search_framework(test_company)
        print(json.dumps(framework, ensure_ascii=False, indent=2))

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
