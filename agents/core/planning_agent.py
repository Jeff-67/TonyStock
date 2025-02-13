"""Planning report agent module.

This module implements an agent for generating comprehensive analysis plans
and coordinating different types of analysis for companies.

Example Usage:
    ```python
    # Initialize the planning agent
    agent = PlanningAgent(provider="openai", model_name="gpt-4o")
    
    # Generate analysis plan
    result = await agent.analyze(
        query="Analyze recent developments for 京鼎",
        news_data=news_articles  # Optional news data dictionary
    )
    
    if result.success:
        print(result.content)  # The analysis plan
        print(result.metadata)  # Additional metadata about the analysis
    ```
"""

import logging
from typing import Tuple, Dict, Any, Optional

from ..base import BaseAgent, AnalysisResult
from prompts.agents.knowledge import finance_agent_prompt
from prompts.agents.capital import CapitalPromptGenerator
from prompts.agents.technical import TechnicalPromptGenerator
from prompts.agents.main import planning_prompt, writing_planning_prompt
from prompts.agents.writing import WritingPromptGenerator
from utils.stock_utils import stock_name_to_id

logger = logging.getLogger(__name__)

class PlanningAgent(BaseAgent):
    """Agent specialized in planning and coordinating analysis.
    
    This agent is responsible for:
    1. Analyzing user queries to determine required analysis types
    2. Generating comprehensive analysis plans
    3. Coordinating between different specialized agents
    4. Ensuring complete coverage of relevant analysis aspects
    
    Attributes:
        provider (str): The LLM provider to use (e.g., "openai", "anthropic")
        model_name (str): The specific model to use (e.g., "gpt-4o")
        
    Supported Companies:
        - 京鼎 (3413)
        - 文曄 (3036)
        - 群聯 (8299)
    """
    
    def __init__(self, provider: str, model_name: str):
        """Initialize the planning agent.
        
        Args:
            provider: The LLM provider to use (e.g., "openai", "anthropic")
            model_name: The specific model to use (e.g., "gpt-4o")
        """
        super().__init__(provider, model_name)
        
    def _get_planning_prompt(self, company_news: str, stock_id: str, user_message: str) -> str:
        """Generate comprehensive planning prompt.
        
        Args:
            company_news: Collected news data to analyze
            stock_id: Company stock ID (e.g., "3413" for 京鼎)
            user_message: User's query or request
            
        Returns:
            Complete planning prompt combining all instructions and data
        """
        company_instruction = finance_agent_prompt(stock_id=stock_id)
        chip_instruction = CapitalPromptGenerator.generate_system_prompt()
        technical_instruction = TechnicalPromptGenerator.generate_system_prompt()
        writing_instruction = WritingPromptGenerator.generate_system_prompt()
        planning_instruction = writing_planning_prompt()


        
        return planning_prompt(
            company_news=company_news,
            company_instruction=company_instruction,
            chip_instruction=chip_instruction,
            technical_analysis_instruction=technical_instruction,
            writing_instruction=writing_instruction,
            planning_instruction=planning_instruction,
            user_message=user_message
        )
        
    def _parse_company_info(self, query: str) -> Tuple[str, str]:
        """Extract company name and ID from query.
        
        Args:
            query: User query containing company name
            
        Returns:
            Tuple of (company_name, stock_id)
            
        Raises:
            ValueError: If company name not found in query or stock ID not found
        """
        # Extract company name from query
        company_name = None
        for name in ["京鼎", "文曄", "群聯"]:
            if name in query:
                company_name = name
                break
                
        if not company_name:
            raise ValueError("Company name not found in query")
            
        # Convert to stock ID
        stock_id = stock_name_to_id(company_name)
        if not stock_id:
            raise ValueError(f"Could not find stock ID for {company_name}")
            
        return company_name, stock_id
        
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Generate comprehensive analysis plan.
        
        This method:
        1. Extracts company information from the query
        2. Processes any provided news data
        3. Generates a comprehensive analysis plan
        4. Returns structured results with metadata
        
        Args:
            query: User query containing company name and analysis request
            **kwargs: Additional arguments
                news_data (Dict[str, Any]): Optional dictionary of news articles
                
        Returns:
            AnalysisResult containing:
                - success: Whether analysis was successful
                - content: The generated analysis plan
                - metadata: Additional information including:
                    * company_name: Extracted company name
                    * stock_id: Company stock ID
                    * analysis_type: Always "planning"
                    * news_count: Number of news articles analyzed
                - error: Error message if analysis failed
                
        Raises:
            ValueError: If company name cannot be extracted from query
        """
        try:
            # Parse company info
            company_name, stock_id = self._parse_company_info(query)
            
            # Get news data
            news_data = kwargs.get('news_data', {})
            
            # Generate planning prompt
            prompt = self._get_planning_prompt(
                company_news=str(news_data),
                stock_id=stock_id,
                user_message=query
            )
            
            # Add prompt to conversation
            self.add_message("user", prompt)
            
            # Get planning response from model
            response, _ = await self.call_model()
            plan = response.choices[0].message.content
            
            return AnalysisResult(
                success=True,
                content=plan,
                metadata={
                    "company_name": company_name,
                    "stock_id": stock_id,
                    "analysis_type": "planning",
                    "news_count": len(news_data)
                }
            )
            
        except Exception as e:
            logger.error(f"Planning error: {str(e)}")
            return AnalysisResult(
                success=False,
                content="",
                error=str(e)
            )

if __name__ == "__main__":
    import asyncio
    import argparse
    from datetime import datetime
    
    async def main():
        """Main function to run the planning agent."""
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Planning Agent for Stock Analysis')
        parser.add_argument('--company', '-c', type=str, choices=['京鼎', '文曄', '群聯'],
                          help='Company to analyze (京鼎, 文曄, or 群聯)')
        parser.add_argument('--provider', '-p', type=str, default='anthropic',
                          help='LLM provider (default: anthropic)')
        parser.add_argument('--model', '-m', type=str, default='claude-3-sonnet-20240229',
                          help='Model name (default: claude-3-sonnet-20240229)')
        
        args = parser.parse_args()
        
        if not args.company:
            parser.print_help()
            return
            
        try:
            # Initialize agent
            agent = PlanningAgent(provider=args.provider, model_name=args.model)
            
            # Prepare query
            query = f"請分析{args.company}最近的發展狀況"
            
            # Example news data
            news_data = {
                "recent_news": [
                    {
                        "title": f"{args.company}分析示例",
                        "content": "這是一個測試用的新聞內容",
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                ]
            }
            
            # Generate analysis plan
            print(f"\nGenerating analysis plan for {args.company}...")
            result = await agent.analyze(query=query, news_data=news_data)
            
            if result.success:
                print("\nAnalysis Plan:")
                print("=" * 80)
                print(result.content)
                print("\nMetadata:")
                print("=" * 80)
                for key, value in result.metadata.items():
                    print(f"{key}: {value}")
            else:
                print(f"\nError: {result.error}")
                
        except Exception as e:
            print(f"\nError: {str(e)}")
            raise
    
    # Run the async main function
    asyncio.run(main())
