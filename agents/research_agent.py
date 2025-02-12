"""Research agent module.

This module implements an agent for performing comprehensive online research
by combining search framework generation and online search execution.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from opik import track
from .base import BaseAgent, AnalysisResult, BaseAnalysisData
from .research_agents.search_framework_agent import generate_search_framework
from .research_agents.online_search_agents import search_keyword

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class ResearchData(BaseAnalysisData):
    """Structure for research analysis data."""
    company: str
    query: str
    framework_queries: int = 0
    total_results: int = 0
    search_results: List[Dict[str, Any]] = None
    timestamp: datetime = None
    
    @classmethod
    def from_research_results(cls, company: str, query: str, framework: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> 'ResearchData':
        """Create instance from research results."""
        return cls(
            symbol=company,  # Using company as symbol for compatibility
            date=datetime.now().strftime("%Y%m%d"),
            company=company,
            query=query,
            framework_queries=len(framework),
            total_results=sum(len(r["search_results"]) for r in results),
            search_results=results,
            timestamp=datetime.now()
        )

class ResearchAgent(BaseAgent):
    """Agent specialized in online research and information gathering."""
    
    def __init__(self, provider: str, model_name: str):
        system_prompt = """You are an expert research analyst. Focus on:
    1. Research Strategy
    - Comprehensive coverage
    - Systematic search approach
    - Source credibility
    - Information validation
    - Data organization

    2. Information Sources
    - News articles
    - Company announcements
    - Industry reports
    - Market analysis
    - Expert insights

    3. Research Components
    - Company background
    - Industry trends
    - Market position
    - Competitive analysis
    - Future outlook

    4. Data Analysis
    - Information synthesis
    - Pattern recognition
    - Trend identification
    - Impact assessment
    - Risk evaluation

    5. Quality Standards
    - Source verification
    - Data accuracy
    - Comprehensive coverage
    - Balanced reporting
    - Clear attribution

    Always ensure:
    - Multiple source verification
    - Recent and relevant information
    - Proper source attribution
    - Balanced perspective
    - Clear organization of findings
"""
        super().__init__(provider, model_name, system_prompt)
        
    async def _execute_search_tasks(self, framework: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute search tasks based on framework.
        
        Args:
            framework: List of search queries and contexts
            
        Returns:
            List of search results
        """
        try:
            # Create tasks for concurrent execution
            tasks = []
            for query_item in framework:
                query = query_item["query"]
                logger.info(f"Creating research task for query: {query}")
                tasks.append(search_keyword(query))

            # Execute all research tasks concurrently
            search_results = await asyncio.gather(*tasks)

            # Combine results with their corresponding queries
            research_results = [
                {"query": query_item, "search_results": results}
                for query_item, results in zip(framework, search_results)
            ]

            return research_results
            
        except Exception as e:
            logger.error(f"Error executing search tasks: {str(e)}")
            raise
            
    def _format_research_results(self, results: List[Dict[str, Any]]) -> str:
        """Format research results into readable content.
        
        Args:
            results: List of research results
            
        Returns:
            Formatted research content
        """
        formatted = []
        
        for result in results:
            query_item = result["query"]
            formatted.append(f"\n## {query_item.get('context', 'Research Results')}")
            formatted.append(f"Query: {query_item['query']}\n")
            
            for search_result in result["search_results"]:
                if search_result.get("error"):
                    continue
                    
                formatted.append(f"### {search_result.get('title', 'No Title')}")
                formatted.append(f"Source: {search_result.get('url', 'No URL')}\n")
                content = search_result.get("content", "").strip()
                if content:
                    formatted.append(content)
                formatted.append("---\n")
                
        return "\n".join(formatted)
        
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Perform comprehensive research analysis.
        
        Args:
            query: User query
            **kwargs: Additional arguments including company name
            
        Returns:
            Analysis result with research findings
        """
        try:
            company = kwargs.get('company')
            if not company:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Company name required for research"
                )
                
            # Clear previous conversation
            self.clear_history()
            
            # Generate search framework
            logger.info(f"Generating search framework for: {company}")
            framework = await generate_search_framework(company, query)
            
            # Execute search tasks
            logger.info("Executing search tasks")
            research_results = await self._execute_search_tasks(framework)
            
            # Create research data
            research_data = ResearchData.from_research_results(
                company=company,
                query=query,
                framework=framework,
                results=research_results
            )
            
            # Format results
            formatted_content = self._format_research_results(research_results)
            
            # Add research results to conversation
            self.add_message(
                "user",
                f"Analyze and summarize the following research results for {company}:\n\n{formatted_content}"
            )
            
            # Get analysis from model
            response, _ = await self.call_model()
            analysis = response.choices[0].message.content
            
            return AnalysisResult(
                success=True,
                content=analysis,
                metadata={
                    "company": company,
                    "analysis_type": "research",
                    "framework_queries": research_data.framework_queries,
                    "total_results": research_data.total_results
                },
                analysis_data=research_data
            )
            
        except Exception as e:
            logger.error(f"Research error: {str(e)}")
            return self.format_error_response(e)

@track()
async def analyze(
    company_name: str, user_message: str
) -> List[Dict[str, Any]]:
    """Perform comprehensive research by combining search framework and online research.

    Args:
        company_name: Name of the company to research
        user_message: User's specific research request or focus

    Returns:
        Dict containing:
        {
            "framework": str,  # The generated search framework
            "research_results": List[Dict]  # Results from online research
        }
    """
    try:
        # Step 1: Generate search framework
        logger.info(f"Generating search framework for: {company_name}")
        framework = await generate_search_framework(company_name, user_message)

        # Step 2: Create tasks for concurrent execution
        tasks = []
        for query_item in framework:
            query = query_item["query"]
            logger.info(f"Creating research task for query: {query}")
            tasks.append(search_keyword(query))

        # Step 3: Execute all research tasks concurrently
        search_results = await asyncio.gather(*tasks)

        # Step 4: Combine results with their corresponding queries
        research_results = [
            {"query": query_item, "search_results": results}
            for query_item, results in zip(framework, search_results)
        ]

        return research_results

    except Exception as e:
        logger.error(f"Error in perform_research: {str(e)}")
        raise


async def main():
    """Test function for the research agent."""
    test_company = "群聯"
    test_message = "Please research recent news about AI and their market strategy"

    logger.info(f"Starting comprehensive research for: {test_company}")
    try:
        research_results = await analyze(test_company, test_message)

        # Print results
        print("\nResearch Results:")
        for i, result in enumerate(research_results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Query Item: {result['query']}")
            for search_result in result["search_results"]:
                print("\nSearch Result:")
                print(f"Title: {search_result.get('title', 'No title')}")
                print(f"URL: {search_result.get('url', 'No URL')}")
                if search_result.get("error"):
                    print(f"Error: {search_result['error']}")
                else:
                    content = search_result.get("content", "")
                    content_preview = f"{content[:200]}..." if content else "No content"
                    print(f"Content preview: {content_preview}")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise  # Add raise to propagate the error for better debugging


if __name__ == "__main__":
    asyncio.run(main())
