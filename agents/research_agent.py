"""Research agent module for comprehensive online research."""

import asyncio
import logging
from typing import Any, Dict, List
from dataclasses import dataclass
from datetime import datetime

from litellm import Message
from opik import track

from .base import BaseAgent, AnalysisResult, BaseAnalysisData
from .research.search_framework_agent import SearchFrameworkAgent
from .research.online_search_agents import OnlineSearchAgent, SearchResult
from prompts.agents.research import ResearchPromptGenerator, ResearchData

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class ResearchAnalysisData(BaseAnalysisData):
    """Structure for research analysis data."""
    company: str
    query: str
    framework_queries: int = 0
    total_results: int = 0
    search_results: List[Dict[str, Any]] = None
    timestamp: datetime = None
    
    @classmethod
    def from_research_results(cls, company: str, query: str, framework: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> 'ResearchAnalysisData':
        """Create instance from research results."""
        return cls(
            symbol=company,
            date=datetime.now().strftime("%Y%m%d"),
            company=company,
            query=query,
            framework_queries=len(framework),
            total_results=sum(len(r["search_results"]) for r in results),
            search_results=results,
            timestamp=datetime.now()
        )

class ResearchAgent(BaseAgent):
    """Agent for comprehensive research analysis."""
    
    def __init__(self, provider: str = "anthropic", model_name: str = "claude-3-sonnet-20240229"):
        """Initialize the research agent."""
        super().__init__(
            provider=provider, 
            model_name=model_name, 
            system_prompt=ResearchPromptGenerator.generate_system_prompt()
        )
        self.framework_agent = SearchFrameworkAgent(provider, model_name)
        self.search_agent = OnlineSearchAgent(provider, model_name)
    @track()
    async def _execute_search_tasks(self, framework: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute search tasks based on framework."""
        try:
            tasks = [self.search_agent.search_keyword(item["query"]) for item in framework]
            search_results = await asyncio.gather(*tasks)
            
            # Convert SearchResult objects to dictionaries
            processed_results = []
            for query_item, results in zip(framework, search_results):
                search_dicts = []
                for result in results:
                    if isinstance(result, SearchResult):
                        search_dict = {
                            "url": result.url,
                            "title": result.title,
                            "content": result.content,
                            "error": result.error
                        }
                        search_dicts.append(search_dict)
                processed_results.append({
                    "query": query_item,
                    "search_results": search_dicts
                })
            return processed_results
            
        except Exception as e:
            logger.error(f"Error executing search tasks: {str(e)}")
            raise
    
    @track()
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Perform comprehensive research analysis.
        
        Args:
            query: User's research query
            **kwargs: Additional arguments including company name
            
        Returns:
            AnalysisResult containing the analysis
        """
        try:
            company = kwargs.get('company')
            if not company:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Company name required for research"
                )
                
            # Generate framework and execute search
            framework_result = await self.framework_agent.analyze(query, company_name=company)
            if not framework_result.success:
                return framework_result
                
            framework = framework_result.analysis_data.queries
            research_results = await self._execute_search_tasks(framework)
            
            # Prepare analysis data
            research_data = ResearchData(
                company=company,
                query=query,
                framework_queries=len(framework),
                total_results=sum(len(r["search_results"]) for r in research_results),
                search_results=research_results,
                timestamp=datetime.now()
            )

            # Generate analysis
            messages = [
                Message(role="system", content=ResearchPromptGenerator.generate_system_prompt()),
                Message(role="user", content=ResearchPromptGenerator.get_user_prompt(company, research_data))
            ]
            
            response = await self.call_model(messages=messages)
            analysis_content = response[0].choices[0].message.content if isinstance(response, tuple) else response.choices[0].message.content

            return AnalysisResult(
                success=True,
                content=analysis_content,
                metadata={
                    "company": company,
                    "analysis_type": "research",
                    "framework_queries": len(framework),
                    "total_results": research_data.total_results
                },
                analysis_data=ResearchAnalysisData.from_research_results(
                    company=company,
                    query=query,
                    framework=framework,
                    results=research_results
                )
            )
            
        except Exception as e:
            logger.error(f"Research error: {str(e)}")
            return self.format_error_response(e)

if __name__ == "__main__":
    async def main():
        """Test function for the research agent."""
        company = "群聯"
        message = "Please research recent news about AI and their market strategy"

        logger.info(f"Starting comprehensive research for: {company}")
        try:
            agent = ResearchAgent()
            result = await agent.analyze(message, company=company)
            
            if result.success:
                logger.info("\nResearch Analysis:")
                logger.info(f"Company: {company}")
                logger.info(f"Query: {message}")
                logger.info("\nFindings:")
                logger.info(result.content)
            else:
                print(f"\nError: {result.error}")
                
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise

    asyncio.run(main())
