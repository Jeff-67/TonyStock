"""Trial agent module for interacting with Claude AI model.

This module implements a chat agent that can interact with Claude AI model,
process its responses, and coordinate between specialized analysis agents.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from opik import track

from .base import BaseAgent, AnalysisResult
from .chips_agent import ChipsAnalysisAgent
from .technical_agents import TechnicalAgent
from prompts.agents.planning import report_planning_prompt
from tools.time.time_tool import get_current_time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TrialAgent(BaseAgent):
    """Trial agent for coordinating specialized analysis agents."""

    def __init__(
        self,
        provider: str = "anthropic",
        model_name: str = "claude-3-sonnet-20240229",
    ):
        """Initialize the trial agent.

        Args:
            provider: Provider name
            model_name: Model name
        """
        system_prompt = report_planning_prompt(current_time=get_current_time())
        super().__init__(provider, model_name, system_prompt)
        
        # Additional system message
        self.add_message(
            "system",
            "如果有user問你你是誰，或是問候你，請回答你的專長是分析京鼎、文曄還有群聯這三隻股票的觀察家。"
        )
        
        # Initialize specialized agents
        self.technical_agent = TechnicalAgent(provider, model_name)
        self.company_news: List[Dict[str, Any]] = []
        self.company_name: Optional[str] = None
        
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Process user query and coordinate analysis between specialized agents.
        
        Args:
            query: User query
            **kwargs: Additional arguments
            
        Returns:
            Analysis result
        """
        try:
            # Store user message
            self.add_message("user", query)
            
            # Extract company name and symbol from query
            # This is a simplified example - you may want to add more sophisticated parsing
            if "京鼎" in query or "3413" in query:
                self.company_name = "京鼎"
                symbol = "3413"
            elif "文曄" in query or "3036" in query:
                self.company_name = "文曄"
                symbol = "3036"
            elif "群聯" in query or "8299" in query:
                self.company_name = "群聯"
                symbol = "8299"
            else:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="Could not identify company from query. Please specify 京鼎(3413), 文曄(3036), or 群聯(8299)."
                )
            
            # Collect analysis from specialized agents
            analysis_results = []
            
            # Technical Analysis
            technical_result = await self.technical_agent.analyze(
                query,
                company=symbol
            )
            if technical_result.success:
                analysis_results.append(("Technical Analysis", technical_result.content))
            
            # Chips Analysis
            chips_agent = ChipsAnalysisAgent(symbol)
            chips_data = await chips_agent.analyze()
            if chips_data:
                analysis_results.append(("Chips Analysis", chips_agent.get_analysis_summary()))
            
            # Combine all analyses
            combined_analysis = "\n\n".join([
                f"## {title}\n{content}" 
                for title, content in analysis_results
            ])
            
            # Add combined analysis to conversation
            self.add_message(
                "user",
                f"Based on the following analysis for {self.company_name} ({symbol}), "
                "provide a comprehensive summary and future outlook. "
                "Focus on key findings, potential risks, and actionable insights.\n\n" +
                combined_analysis
            )
            
            # Get final summary from model
            response, _ = await self.call_model()
            
            return AnalysisResult(
                success=True,
                content=response.choices[0].message.content,
                metadata={
                    "company_name": self.company_name,
                    "symbol": symbol,
                    "analysis_components": [title for title, _ in analysis_results]
                }
            )
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return AnalysisResult(
                success=False,
                content="",
                error=str(e)
            )


async def main():
    """Run an interactive chat session with the agent."""
    # Create agent
    agent = TrialAgent()
    
    # Run test analysis
    result = await agent.analyze("請從各個面向詳細分析京鼎(3413)，並且給予未來的預測")
    
    print('='*100)
    print(result.content if result.success else f"Error: {result.error}")
    print('='*100)


if __name__ == "__main__":
    asyncio.run(main()) 