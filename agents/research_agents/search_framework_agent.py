"""Search framework agent module for generating comprehensive company research queries.

This module implements the first step of the analysis framework by using LLM to:
1. Understand company's industry characteristics and value chain
2. Analyze company's position and competitive advantages
3. Generate comprehensive search queries based on this understanding
"""

import json
import logging
from typing import TypedDict

from opik import track
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential

from prompts.agents.experience import search_experience_prompt
from prompts.agents.knowledge import finance_agent_prompt
from prompts.agents.main import searching_framework_prompt
from tools.llm_api import aquery_llm
from tools.time.time_tool import get_current_time
from utils.stock_utils import stock_name_to_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class QueryModel(TypedDict):
    """Model for structured search queries.

    Attributes:
        query: The actual search query combining company identifiers with keywords
        core_question: Which core question (1-6) this query primarily addresses
        purpose: What specific information we're looking for
        expected_insights: What insights we expect to gain from this query
        reasoning: Why this query is relevant to the user's message
    """

    query: str
    core_question: str
    purpose: str
    expected_insights: str
    reasoning: str


@track()
def validate_framework(content: str) -> tuple[bool, list[QueryModel] | None]:
    """Validate and parse search framework response.

    Args:
        content: Response content from LLM

    Returns:
        tuple[bool, list[QueryModel] | None]: (is_valid, parsed_queries if valid else None)
    """
    try:
        # Parse JSON
        data = json.loads(content)

        # Check if it's an array
        if not isinstance(data, list):
            logger.error("Response must be a JSON array")
            return False, None

        # Get required fields from QueryModel type information
        required_fields = set(QueryModel.__annotations__.keys())

        validated_queries: list[QueryModel] = []

        # Validate each item
        for item in data:
            # Check required fields
            missing_fields = required_fields - set(item.keys())
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return False, None

            # Check if all values are non-empty strings
            for field in required_fields:
                if (
                    not isinstance(item.get(field), str)
                    or not item.get(field, "").strip()
                ):
                    logger.error(f"Field '{field}' must be a non-empty string")
                    return False, None

            # Construct QueryModel with explicit field assignments
            query_model = QueryModel(
                query=item["query"],
                core_question=item["core_question"],
                purpose=item["purpose"],
                expected_insights=item["expected_insights"],
                reasoning=item["reasoning"],
            )
            validated_queries.append(query_model)

        return True, validated_queries

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {str(e)}")
        return False, None
    except Exception as e:
        logger.error(f"Error validating framework: {str(e)}")
        return False, None


@track()
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_result(lambda x: x is None),  # Retry if None returned
    before_sleep=lambda retry_state: logger.warning(
        f"Validation failed, attempt {retry_state.attempt_number}. Retrying..."
    ),
)
async def generate_search_framework(
    company_name: str, user_message: str
) -> list[QueryModel] | None:
    """Generate comprehensive search framework using LLM.

    Args:
        company_name: Name of the company to analyze
        user_message: User's message to guide the search

    Returns:
        list[QueryModel] | None: List of validated search queries or None if validation fails

    Raises:
        ValueError: If response validation fails after max retries
    """
    try:
        # Generate prompt
        stock_id = stock_name_to_id(company_name)
        prompt = searching_framework_prompt(
            company_name=company_name,
            stock_id=stock_id,
            current_time=get_current_time(),
            company_instruction=finance_agent_prompt(stock_id=stock_id),
            searching_instruction=search_experience_prompt(),
            user_message=user_message,
        )

        # Query LLM
        messages = [{"role": "user", "content": prompt}]
        logger.info(f"Querying LLM for search framework generation")
        response, details = await aquery_llm(
            messages=messages,
            model="claude-3-sonnet-20240229",
            provider="anthropic",
            json_mode=True,
        )

        content = details["content"]
        if not content:
            logger.error("LLM returned empty content")
            return None

        logger.info(f"Received response from LLM, validating content")
        
        # Validate and parse response
        is_valid, queries = validate_framework(content)
        if not is_valid or queries is None:
            logger.error(f"Failed to validate framework response: {content[:200]}...")
            return None

        logger.info(f"Successfully validated framework with {len(queries)} queries")
        return queries

    except Exception as e:
        logger.error(f"Error generating search framework: {str(e)}")
        return None


async def main():
    """Test function for the search framework agent."""
    test_company = "群聯"
    logger.info(f"Generating search framework for: {test_company}")

    try:
        framework = await generate_search_framework(
            test_company, "Tell me about their latest products"
        )
        print(json.dumps(framework, ensure_ascii=False, indent=2))

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
