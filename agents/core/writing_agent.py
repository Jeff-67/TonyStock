"""Writing agent module.

This module implements an agent for writing and formatting analysis reports.
It provides structured report generation with consistent formatting and style.
"""

import logging
from typing import Any, Dict, Optional

from .base import BaseAgent, AnalysisResult
from tools.writing.writing_tool import WritingTool

logger = logging.getLogger(__name__)

class WritingAgent(BaseAgent):
    """Agent specialized in writing and formatting analysis reports."""
    
    def __init__(self, provider: str, model_name: str):
        system_prompt = """You are a professional financial report writing expert. Focus on:
1. Report Structure
   - Executive summary
   - Key findings
   - Detailed analysis sections
   - Supporting data and charts
   - Conclusions and recommendations

2. Writing Style
   - Clear and concise language
   - Professional financial terminology
   - Logical flow and transitions
   - Balanced perspective
   - Evidence-based arguments

3. Data Presentation
   - Key metrics and ratios
   - Trend analysis
   - Comparative analysis
   - Risk factors
   - Market context

4. Report Components
   - Title and headers
   - Table of contents
   - Section summaries
   - Data tables and figures
   - References and sources

5. Quality Standards
   - Accuracy of information
   - Consistency in formatting
   - Citation of sources
   - Proper terminology
   - Professional tone

Always ensure:
- Clear organization of ideas
- Proper citation of data sources
- Balanced analysis of pros and cons
- Actionable recommendations
- Professional formatting
"""
        super().__init__(provider, model_name, system_prompt)
        self.tool = WritingTool()
        
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Write and format analysis report.
        
        Args:
            query: User query or raw analysis content
            **kwargs: Additional arguments including company name and analysis data
            
        Returns:
            Analysis result with formatted report
        """
        try:
            company = kwargs.get('company')
            analysis_data = kwargs.get('analysis_data')
            
            if not company:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Company name required for report writing"
                )
                
            if not analysis_data:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Analysis data required for report writing"
                )
                
            # Clear previous conversation
            self.clear_history()
            
            # Add writing request
            self.add_message(
                "user",
                f"Format and enhance the following analysis for {company}:\n\n{analysis_data}"
            )
            
            # Get formatted content using tool
            formatted_content = await self.tool.execute({
                "company": company,
                "content": analysis_data,
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
                    "raw_content": analysis_data
                }
            )
            
        except Exception as e:
            logger.error(f"Writing error: {str(e)}")
            return AnalysisResult(
                success=False,
                content="",
                error=str(e)
            ) 