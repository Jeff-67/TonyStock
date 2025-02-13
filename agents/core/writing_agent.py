"""Writing agent module.

This module implements an agent for writing and formatting analysis reports.
It provides structured report generation with consistent formatting and style.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime

from ..base import BaseAgent, AnalysisResult, BaseAnalysisData
from prompts.agents.writing import WritingPromptGenerator
from tools.orchestrator import Message
logger = logging.getLogger(__name__)

@dataclass
class WritingAnalysisData(BaseAnalysisData):
    """Structure for writing analysis data."""
    company: str
    raw_content: str
    analysis_type: str = "writing"
    timestamp: datetime = datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WritingAnalysisData':
        """Create instance from dictionary."""
        return cls(**{
            k: v for k, v in data.items() 
            if k in cls.__dataclass_fields__
        })

class WritingAgent(BaseAgent):
    """Agent specialized in writing and formatting analysis reports."""
    
    def __init__(
        self,
        provider: str = "anthropic",
        model_name: str = "claude-3-sonnet-20240229"
    ):

        super().__init__(provider, model_name)
        
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Write and format analysis report.
        
        Args:
            query: User query or raw analysis content
            **kwargs: Additional arguments including:
                - company: Company name
                - analysis_data: Raw analysis content
                - symbol: Stock symbol
                - date: Analysis date
            
        Returns:
            AnalysisResult with formatted report
        """
        try:
            # Validate required parameters
            company = kwargs.get('company')
            raw_content = kwargs.get('analysis_data')
            symbol = kwargs.get('symbol')
            date = kwargs.get('date', datetime.now().strftime('%Y-%m-%d'))

            system_prompt = WritingPromptGenerator.generate_system_prompt()
            user_prompt = WritingPromptGenerator.get_user_prompt(company, raw_content)  
            
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt)
            ]
            
            response = await self.call_model(messages=messages)
            formatted_content = response.choices[0].message.content if isinstance(response, tuple) else str(response)       
            
            if not all([company, raw_content, symbol]):
                missing = [k for k, v in {
                    'company': company,
                    'analysis_data': raw_content,
                    'symbol': symbol
                }.items() if not v]
                return AnalysisResult(
                    success=False,
                    content="",
                    error=f"Missing required parameters: {', '.join(missing)}"
                )
            
            # Create analysis data structure
            analysis_data = WritingAnalysisData(
                symbol=symbol,
                date=date,
                company=company,
                raw_content=raw_content
            )
            
            # Clear previous conversation
            self.clear_history()
            
            # Add writing request
            self.add_message(
                "user",
                f"Format and enhance the following analysis for {company}:\n\n{raw_content}"
            )
            
            # Get formatted content using tool
            formatted_content = await self.tool.execute({
                "company": company,
                "content": raw_content,
                "query": query
            })
            
            # Add tool result to conversation
            self.add_message(
                "assistant",
                f"Draft report prepared:\n{formatted_content}"
            )
            
            # Get final polished version from model
            self.add_message(
                "user",
                "Review the draft report above and provide a final polished version. "
                "Ensure professional formatting, clear structure, and proper citation of data. "
                "Maintain a balanced perspective and provide actionable insights."
            )
            
            response, _ = await self.call_model()
            final_report = response.choices[0].message.content
            
            return AnalysisResult(
                success=True,
                content=final_report,
                metadata={
                    "company": company,
                    "analysis_type": "writing",
                    "raw_content": raw_content
                },
                analysis_data=analysis_data
            )
            
        except Exception as e:
            return self.format_error_response(e) 