"""Orchestrator module for coordinating different analysis agents."""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from agents.base import AnalysisResult, BaseAgent, BaseAnalysisData
from .planning_agent import PlanningAgent
from agents.research_agent import ResearchAgent
from agents.technical_agents import TechnicalAgent
from agents.capital_agent import CapitalAgent

logger = logging.getLogger(__name__)

@dataclass
class OrchestratorData(BaseAnalysisData):
    """Analysis data for orchestrator results."""
    company: str
    query: str
    plan: Optional[str] = None
    agent_results: Dict[str, AnalysisResult] = field(default_factory=dict)

class AnalysisOrchestrator(BaseAgent):
    """Coordinates analysis agents and manages workflow."""
    
    ANALYSIS_KEYWORDS = {
        'technical': ["technical", "price", "trend", "pattern", "技術面"],
        'capital': ["chips", "volume", "institutional", "籌碼"],
        'research': ["research", "fundamental", "news", "基本面", "新聞"]
    }
    
    POSITIONAL_AGENTS = {'technical', 'capital'}  # Agents that take company as positional arg
    
    def __init__(self, provider: str = "openai", model_name: str = "gpt-4o"):
        """Initialize orchestrator and its agents."""
        super().__init__(provider=provider, model_name=model_name)
        self.agents = {
            'planning': PlanningAgent(provider, model_name),
            'research': ResearchAgent(provider, model_name),
            'technical': TechnicalAgent(provider, model_name),
            'capital': CapitalAgent()
        }
    
    def _extract_company(self, query: str) -> Optional[str]:
        """Extract company identifier from query."""
        if match := re.search(r'\((\d{4})\)', query):
            return match.group(1)
        if match := re.search(r'(京鼎|文曄|群聯)', query):
            return match.group()
        return None
    
    def _determine_required_agents(self, plan: str) -> Set[str]:
        """Determine required agents based on planning output."""
        required = set()
        plan_lower = plan.lower()
        
        for agent_type, keywords in self.ANALYSIS_KEYWORDS.items():
            if any(kw in plan_lower for kw in keywords):
                required.add(agent_type)
                
        return required or {'research'}  # Default to research if no specific requirements
    
    async def _execute_analysis(self, company: str, query: str) -> AnalysisResult:
        """Execute the full analysis workflow."""
        # Get analysis plan
        plan_result = await self.agents['planning'].analyze(query, company=company)
        if not plan_result.success:
            return plan_result
            
        # Run required analyses
        required_agents = self._determine_required_agents(plan_result.content)
        analysis_tasks = []
        
        for agent_type in required_agents:
            if agent := self.agents.get(agent_type):
                if agent_type in ('technical', 'capital'):
                    # These agents expect company as the first argument
                    analysis_tasks.append(agent.analyze(company))
                else:
                    # These agents expect query as first argument and company as kwarg
                    analysis_tasks.append(agent.analyze(query, company=company))
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Process results
        agent_results = {}
        content_parts = [plan_result.content]
        
        for agent_type, result in zip(required_agents, results):
            if isinstance(result, Exception):
                logger.error(f"Analysis error in {agent_type}: {str(result)}")
                agent_results[agent_type] = self.format_error_response(result)
                continue
                
            agent_results[agent_type] = result
            if result.success:
                content_parts.append(result.content)
                
        # Create analysis data
        analysis_data = OrchestratorData(
            symbol=company,
            date=datetime.now().strftime("%Y%m%d"),
            company=company,
            query=query,
            plan=plan_result.content,
            agent_results=agent_results
        )
        
        # Return combined result
        return AnalysisResult(
            success=len(content_parts) > 1,
            content="\n\n".join(content_parts) if len(content_parts) > 1 else "",
            error="All analyses failed" if len(content_parts) <= 1 else None,
            metadata={"company": company, "analysis_types": list(required_agents)},
            analysis_data=analysis_data
        )
    
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Run analysis workflow for the given query."""
        try:
            if company := self._extract_company(query):
                return await self._execute_analysis(company, query)
            return AnalysisResult(
                success=False,
                content="",
                error="無法識別公司名稱，請確認輸入格式"
            )
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return self.format_error_response(e)

if __name__ == "__main__":
    async def test():
        orchestrator = AnalysisOrchestrator()
        result = await orchestrator.analyze("請分析京鼎(2449)的技術面和籌碼面")
        print(result.content if result.success else f"分析失敗: {result.error}")
    
    asyncio.run(test())