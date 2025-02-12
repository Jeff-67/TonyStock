"""Planning report agent module.

This module implements an agent for generating comprehensive analysis plans
and coordinating different types of analysis for companies.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from ..base import BaseAgent, AnalysisResult
from prompts.agents.knowledge import (
    finance_agent_prompt,
    capital_agent_prompt,
    technical_agent_prompt
)
from prompts.agents.main import planning_prompt, writing_planning_prompt
from utils.stock_utils import stock_name_to_id

logger = logging.getLogger(__name__)

class PlanningAgent(BaseAgent):
    """Agent specialized in planning and coordinating analysis."""
    
    def __init__(self, provider: str, model_name: str):
        system_prompt = """You are a strategic analysis planning expert. Focus on:
            1. Analysis Framework
            - Comprehensive coverage
            - Logical analysis flow
            - Priority assessment
            - Resource allocation
            - Timeline planning

            2. Information Sources
            - News and announcements
            - Financial reports
            - Market data
            - Industry research
            - Expert opinions

            3. Analysis Components
            - Technical analysis needs
            - Fundamental analysis areas
            - Chips analysis focus
            - Market sentiment tracking
            - Risk assessment

            4. Integration Strategy
            - Data correlation
            - Cross-validation
            - Conflict resolution
            - Synthesis methods
            - Consistency checks

            5. Output Requirements
            - Clear objectives
            - Measurable goals
            - Quality standards
            - Delivery format
            - Review criteria

            Always ensure:
            - Complete coverage of key areas
            - Clear prioritization of tasks
            - Efficient resource allocation
            - Proper sequencing of analysis
            - Quality control measures
            """
        super().__init__(provider, model_name, system_prompt)
        
    def _get_planning_prompt(self, company_news: str, stock_id: str, user_message: str) -> str:
        """Generate comprehensive planning prompt.
        
        Args:
            company_news: Collected news data
            stock_id: Company stock ID
            user_message: User's query
            
        Returns:
            Complete planning prompt
        """
        company_instruction = finance_agent_prompt(stock_id=stock_id)
        chip_instruction = capital_agent_prompt()
        technical_instruction = technical_agent_prompt()
        writing_instruction = writing_planning_prompt()
        
        return planning_prompt(
            company_news=company_news,
            company_instruction=company_instruction,
            chip_instruction=chip_instruction,
            technical_analysis_instruction=technical_instruction,
            writing_instruction=writing_instruction,
            user_message=user_message
        )
        
    def _parse_company_info(self, query: str) -> Tuple[str, str]:
        """Extract company name and ID from query.
        
        Args:
            query: User query
            
        Returns:
            Tuple of (company_name, stock_id)
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
        
        Args:
            query: User query
            **kwargs: Additional arguments including news data
            
        Returns:
            Analysis result with planning report
        """
        try:
            # Parse company info
            company_name, stock_id = self._parse_company_info(query)
            
            # Get news data
            news_data = kwargs.get('news_data', {})
            
            # Clear previous conversation
            self.clear_history()
            
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
