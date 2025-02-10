"""Orchestrator module for coordinating different analysis agents."""

import asyncio
import logging
import re
import json
from typing import Dict, List, Optional, Tuple, Set

from .base import AnalysisResult, BaseAgent
from agents.planning_agent import PlanningAgent
from agents.research_agent import ResearchAgent
from technical_agents.technical_agent import TechnicalAgent
from agents.chips_agent import ChipsAgent

logger = logging.getLogger(__name__)

class AnalysisOrchestrator:
    """Coordinates different analysis agents and manages the analysis workflow."""
    
    def __init__(
        self,
        provider: str = "anthropic",
        model_name: str = "claude-3-sonnet-20240229"
    ):
        self.provider = provider
        self.model_name = model_name
        
        # Initialize agents
        self.agents = {
            'planning': PlanningAgent(provider, model_name),
            'research': ResearchAgent(provider, model_name),
            'technical': TechnicalAgent(provider, model_name),
            'chips': ChipsAgent(provider, model_name)
        }
        
        # Cache for storing intermediate results
        self.result_cache: Dict[str, AnalysisResult] = {}
        
    def parse_query(self, query: str) -> Tuple[str, str]:
        """Parse query to extract company name and analysis type."""
        company_match = re.search(r'\((\d{4})\)|[京鼎|文曄|群聯]', query)
        company_name = company_match.group() if company_match else ""
        return company_name, "planning"  # Always start with planning
        
    def parse_plan(self, plan_content: str) -> Set[str]:
        """Parse planning result to determine required analysis types.
        
        Args:
            plan_content: Planning agent's output
            
        Returns:
            Set of required analysis types
        """
        required_agents = set()
        
        # Look for keywords indicating required analyses
        if any(kw in plan_content.lower() for kw in ["technical", "price", "trend", "pattern", "技術面"]):
            required_agents.add("technical")
            
        if any(kw in plan_content.lower() for kw in ["chips", "volume", "institutional", "籌碼"]):
            required_agents.add("chips")
            
        if any(kw in plan_content.lower() for kw in ["research", "fundamental", "news", "基本面", "新聞"]):
            required_agents.add("research")
            
        # Always include research for context if no specific analysis is mentioned
        if not required_agents:
            required_agents.add("research")
            
        return required_agents
        
    async def run_planned_analysis(self, company: str, query: str) -> AnalysisResult:
        """Run analysis based on planning agent's output.
        
        Args:
            company: Company name or symbol
            query: Original user query
            
        Returns:
            Combined analysis result
        """
        try:
            # 1. Get analysis plan
            plan_result = await self.agents['planning'].analyze(query, company=company)
            if not plan_result.success:
                return plan_result
                
            # 2. Determine required analyses from plan
            required_agents = self.parse_plan(plan_result.content)
            logger.info(f"Required analyses from plan: {required_agents}")
            
            # 3. Run required analyses in parallel
            analysis_tasks = []
            for agent_type in required_agents:
                if agent := self.agents.get(agent_type):
                    analysis_tasks.append(
                        agent.analyze(query, company=company)
                    )
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 4. Combine results
            combined_content = [plan_result.content]  # Start with the plan
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Analysis error: {str(result)}")
                    continue
                if result.success:
                    combined_content.append(result.content)
                    
            if len(combined_content) <= 1:  # Only plan, no successful analyses
                return AnalysisResult(
                    success=False,
                    content="",
                    error="All analyses failed"
                )
                
            return AnalysisResult(
                success=True,
                content="\n\n".join(combined_content),
                metadata={
                    "company": company,
                    "analysis_types": list(required_agents),
                    "plan": plan_result.content
                }
            )
            
        except Exception as e:
            logger.error(f"Planned analysis error: {str(e)}")
            return AnalysisResult(
                success=False,
                content="",
                error=str(e)
            )
            
    async def analyze(self, query: str) -> str:
        """Main entry point for analysis."""
        try:
            # Parse query
            company, _ = self.parse_query(query)
            if not company:
                return "無法識別公司名稱，請確認輸入格式"
                
            # Get cached result if available
            cache_key = f"{company}:{query}"
            if cache_key in self.result_cache:
                return self.result_cache[cache_key].content
                
            # Run analysis based on plan
            result = await self.run_planned_analysis(company, query)
                
            # Cache successful results
            if result.success:
                self.result_cache[cache_key] = result
                
            return result.content if result.success else f"分析失敗: {result.error}"
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return f"分析過程發生錯誤: {str(e)}" 