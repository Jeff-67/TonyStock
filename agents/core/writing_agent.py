"""Writing agent module.

This module implements an agent for writing and formatting analysis reports.
It provides structured report generation with consistent formatting and style.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime

from ..base import BaseAgent, AnalysisResult, BaseAnalysisData
from prompts.agents.writing import WritingPromptGenerator, WritingData
from opik import track
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
    @track()
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
            
            # Create writing data for prompt generation
            writing_data = WritingData(
                company=company,
                title=f"{company} Stock Analysis",
                content=raw_content,
                analysis_type="comprehensive",
                sources=[],
                timestamp=datetime.now(),
                metadata={"symbol": symbol}
            )
            
            # Generate prompts
            system_prompt = WritingPromptGenerator.generate_system_prompt()
            user_prompt = WritingPromptGenerator.get_user_prompt(company, writing_data)  
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.call_model(messages=messages)
            
            # Extract content from response
            if isinstance(response, tuple):
                response_obj = response[0]
                if hasattr(response_obj, 'choices') and response_obj.choices:
                    formatted_content = response_obj.choices[0].message.content
                else:
                    formatted_content = str(response_obj)
            else:
                formatted_content = str(response)
            
            return AnalysisResult(
                success=True,
                content=formatted_content,
                metadata={
                    "company": company,
                    "analysis_type": "writing",
                    "raw_content": raw_content
                },
                analysis_data=analysis_data
            )
            
        except Exception as e:
            return self.format_error_response(e)


    
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Create sample analysis data
        raw_content = """
Technical Analysis:
- Current price: 530
- MA5: 525.5
- MA20: 515.2
- RSI: 65.3
- MACD: 2.5

Market Analysis:
- Strong upward trend
- Above major moving averages
- Moderate trading volume

Fundamental Analysis:
- Recent contract wins
- Stable revenue growth
- Positive industry outlook
"""
        
        # Initialize writing agent
        agent = WritingAgent()
        
        # Test the analysis
        result = await agent.analyze(
            query="Format and enhance the analysis",
            company="京鼎",
            analysis_data=raw_content,
            symbol="2449",
            date="2024-03-15"
        )
        
        # Print results
        if result.success:
            print("Analysis successful!")
            print("\nFormatted Report:")
            print("-" * 50)
            print(result.content)
        else:
            print(f"Analysis failed: {result.error}")
            
    # Run the test
    asyncio.run(test()) 