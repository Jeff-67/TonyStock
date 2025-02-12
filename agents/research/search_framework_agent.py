"""Search framework agent module for generating comprehensive company research queries.

This module implements the first step of the analysis framework by using LLM to:
1. Understand company's industry characteristics and value chain
2. Analyze company's position and competitive advantages
3. Generate comprehensive search queries based on this understanding
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TypedDict

from opik import track
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential

from prompts.agents.experience import search_experience_prompt
from prompts.agents.knowledge import finance_agent_prompt
from prompts.agents.main import searching_framework_prompt
from tools.time.time_tool import get_current_time
from utils.stock_utils import stock_name_to_id
from ..base import BaseAgent, AnalysisResult, BaseAnalysisData

# Configure logging
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


@dataclass
class SearchFrameworkData(BaseAnalysisData):
    """Structure for search framework analysis data."""
    company_name: str
    user_message: str
    queries: List[QueryModel]
    total_queries: int = 0
    
    @classmethod
    def from_framework_results(cls, company_name: str, user_message: str, queries: List[QueryModel]) -> 'SearchFrameworkData':
        """Create instance from framework results."""
        return cls(
            symbol=company_name,  # Using company name as symbol for compatibility
            date=datetime.now().strftime("%Y%m%d"),
            company_name=company_name,
            user_message=user_message,
            queries=queries,
            total_queries=len(queries)
        )


class SearchFrameworkAgent(BaseAgent):
    """Agent specialized in generating search frameworks."""
    
    def __init__(self, provider: str = "anthropic", model_name: str = "claude-3-sonnet-20240229"):
        """Initialize the search framework agent."""
        super().__init__(provider=provider, model_name=model_name)
        
    @track()
    def validate_framework(self, content: str) -> tuple[bool, list[QueryModel] | None]:
        """Validate and parse search framework response.

        Args:
            content: Response content from LLM

        Returns:
            tuple[bool, list[QueryModel] | None]: (is_valid, parsed_queries if valid else None)
        """
        try:
            # Clean up content - remove code block markers if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json prefix
            if content.startswith("```"):
                content = content[3:]  # Remove ``` prefix
            if content.endswith("```"):
                content = content[:-3]  # Remove ``` suffix
            content = content.strip()

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
                # Validate required fields and types
                if missing_fields := required_fields - set(item.keys()):
                    logger.error(f"Missing required fields: {missing_fields}")
                    return False, None

                if not all(isinstance(item.get(field), str) and item.get(field, "").strip() 
                          for field in required_fields):
                    logger.error("All fields must be non-empty strings")
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
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Content causing error: {content[:200]}...")
            return False, None
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False, None

    @track()
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_result(lambda x: x is None)
    )
    async def generate_framework(self, company_name: str, user_message: str) -> Optional[List[QueryModel]]:
        """Generate comprehensive search framework using LLM.

        Args:
            company_name: Name of the company to analyze
            user_message: User's message to guide the search

        Returns:
            Optional[List[QueryModel]]: List of validated search queries or None if validation fails
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
            logger.info("Generating search framework")
            response = await self.call_model(messages=messages)

            if isinstance(response, tuple):
                content = response[0].choices[0].message.content
            else:
                content = response.choices[0].message.content

            if not content:
                logger.error("Empty LLM response")
                return None

            logger.info(f"Received response from LLM, validating content")
            
            # Validate and parse response
            is_valid, queries = self.validate_framework(content)
            if not is_valid or queries is None:
                logger.error(f"Invalid framework response: {content[:200]}...")
                return None

            logger.info(f"Successfully validated framework with {len(queries)} queries")
            return queries

        except Exception as e:
            logger.error(f"Framework generation error: {str(e)}")
            return None
            
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Generate search framework for the given company and query.
        
        Args:
            query: The user's query/message
            **kwargs: Additional arguments including company_name
            
        Returns:
            AnalysisResult containing the generated search framework
        """
        try:
            company_name = kwargs.get('company_name')
            if not company_name:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Company name required for framework generation"
                )
                
            # Generate framework
            framework = await self.generate_framework(company_name, query)
            if not framework:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Failed to generate search framework"
                )
            
            # Prepare analysis data
            analysis_data = SearchFrameworkData.from_framework_results(
                company_name=company_name,
                user_message=query,
                queries=framework
            )
            
            # Format content summary
            content_summary = []
            for query_model in framework:
                content_summary.append(
                    f"Query: {query_model['query']}\n"
                    f"Core Question: {query_model['core_question']}\n"
                    f"Purpose: {query_model['purpose']}\n"
                    f"Expected Insights: {query_model['expected_insights']}\n"
                    f"Reasoning: {query_model['reasoning']}\n"
                )
            
            return AnalysisResult(
                success=True,
                content="\n\n".join(content_summary),
                metadata={
                    "company_name": company_name,
                    "total_queries": len(framework)
                },
                analysis_data=analysis_data
            )
            
        except Exception as e:
            return self.format_error_response(e)


async def main():
    """Test function for the search framework agent."""
    test_company = "群聯"
    logger.info(f"Generating search framework for: {test_company}")

    try:
        agent = SearchFrameworkAgent()
        result = await agent.analyze(
            query="Tell me about their latest products",
            company_name=test_company
        )
        
        if result.success:
            print("\nSearch Framework:")
            print(result.content)
        else:
            print(f"\nError: {result.error}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
