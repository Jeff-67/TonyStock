"""Orchestrator module for coordinating different analysis agents."""

import asyncio
import logging
import re
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import sys
import time

from opik import track

from agents.base import AnalysisResult, BaseAgent, BaseAnalysisData
from .planning_agent import PlanningAgent
from agents.research_agent import ResearchAgent
from agents.technical_agent import TechnicalAgent
from agents.capital_agent import CapitalAgent
from .writing_agent import WritingAgent

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

# Get module logger
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
            'capital': CapitalAgent(),
            'writing': WritingAgent(provider, model_name)
        }
    
    @track()
    def _extract_company(self, query: str) -> Optional[str]:
        """Extract company identifier from query."""
        if match := re.search(r'\((\d{4})\)', query):
            return match.group(1)
        if match := re.search(r'(京鼎|文曄|群聯)', query):
            return match.group()
        return None
    
    @track()
    def _determine_required_agents(self, plan: str) -> Set[str]:
        """Determine required agents based on planning output."""
        required = set()
        plan_lower = plan.lower()
        
        for agent_type, keywords in self.ANALYSIS_KEYWORDS.items():
            if any(kw in plan_lower for kw in keywords):
                required.add(agent_type)
                
        return required or {'research'}
    
    @track()
    async def _execute_analysis(self, company: str, query: str) -> AnalysisResult:
        """Execute the full analysis workflow."""
        try:
            # Get analysis plan
            logger.info("Getting analysis plan...")
            print("\nGetting analysis plan...", flush=True)
            plan_result = await self.agents['planning'].analyze(query, company=company)
            if not plan_result.success:
                return plan_result
                
            # Run required analyses
            required_agents = self._determine_required_agents(plan_result.content)
            analysis_tasks = []
            
            logger.info(f"Required agents: {required_agents}")
            print(f"\nRequired analyses: {', '.join(required_agents)}", flush=True)
            
            for agent_type in required_agents:
                if agent := self.agents.get(agent_type):
                    logger.info(f"Starting {agent_type} analysis...")
                    print(f"\nStarting {agent_type} analysis...", flush=True)
                    if agent_type in ('technical', 'capital'):
                        analysis_tasks.append(agent.analyze(company))
                    else:
                        analysis_tasks.append(agent.analyze(query, company=company))
            
            # Set timeout for individual analyses
            async with asyncio.timeout(180):  # 3 minutes timeout for analyses
                results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results
            agent_results = {}
            content_parts = [str(plan_result.content)]  # Convert to string explicitly
            
            for agent_type, result in zip(required_agents, results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis error in {agent_type}: {str(result)}")
                    print(f"\nError in {agent_type} analysis: {str(result)}", flush=True)
                    agent_results[agent_type] = self.format_error_response(result)
                    continue
                    
                agent_results[agent_type] = result
                if result.success:
                    logger.info(f"{agent_type} analysis completed successfully")
                    print(f"\n{agent_type} analysis completed", flush=True)
                    content_parts.append(str(result.content))  # Convert to string explicitly
                    
            # Create analysis data
            analysis_data = OrchestratorData(
                symbol=company,
                date=datetime.now().strftime("%Y%m%d"),
                company=company,
                query=query,
                plan=str(plan_result.content),  # Convert to string explicitly
                agent_results=agent_results
            )

            # If no successful results, return error
            if len(content_parts) <= 1:
                return AnalysisResult(
                    success=False,
                    content="",
                    error="All analyses failed",
                    metadata={"company": company, "analysis_types": list(required_agents)},
                    analysis_data=analysis_data
                )

            # Combine all content
            combined_content = "\n\n".join(content_parts)
            
            # Use writing agent to format final report
            logger.info("Formatting final report...")
            print("\nFormatting final report...", flush=True)
            
            # Set timeout for writing agent
            async with asyncio.timeout(60):  # 1 minute timeout for writing
                writing_result = await self.agents['writing'].analyze(
                    query,
                    company=company,
                    analysis_data=combined_content
                )
            
            if writing_result.success:
                logger.info("Report formatting completed")
                print("\nReport formatting completed", flush=True)
                return AnalysisResult(
                    success=True,
                    content=str(writing_result.content),  # Convert to string explicitly
                    metadata={
                        "company": company,
                        "analysis_types": list(required_agents),
                        "raw_content": combined_content
                    },
                    analysis_data=analysis_data
                )
            else:
                # Fallback to unformatted content if writing agent fails
                logger.warning("Writing agent failed, returning unformatted content")
                print("\nWriting agent failed, returning unformatted content", flush=True)
                return AnalysisResult(
                    success=True,
                    content=combined_content,
                    metadata={"company": company, "analysis_types": list(required_agents)},
                    analysis_data=analysis_data
                )
                
        except asyncio.TimeoutError as e:
            logger.error("Analysis timed out")
            print("\nAnalysis timed out", flush=True)
            return AnalysisResult(
                success=False,
                content="",
                error="Analysis timed out",
                metadata={"company": company, "error_type": "timeout"}
            )
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            print(f"\nAnalysis error: {str(e)}", flush=True)
            return self.format_error_response(e)
        
    @track(project_name="stock_analysis")
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

async def main():
    """Main entry point for the orchestrator."""
    try:
        logger.info("Starting analysis orchestrator...")
        print("Initializing analysis...", flush=True)
        
        orchestrator = AnalysisOrchestrator(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229"
        )
        
        # Test case - start with just one query for testing
        query = "請分析京鼎(2449)的技術面和籌碼面"
        
        logger.info(f"\n=== Starting analysis for query: {query} ===")
        print(f"\nAnalyzing: {query}", flush=True)
        
        try:
            # Set timeout for the analysis
            async with asyncio.timeout(300):  # 5 minutes timeout
                # Track start time
                start_time = time.time()
                
                # Run analysis
                print("\nExecuting analysis...", flush=True)
                result = await orchestrator.analyze(query)
                
                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                
                if result and result.success:
                    logger.info(f"Analysis completed successfully in {elapsed_time:.2f} seconds!")
                    print("\nAnalysis Result:", flush=True)
                    print("=" * 80, flush=True)
                    
                    if result.content:
                        print(result.content, flush=True)
                    else:
                        print("No content in result", flush=True)
                        
                    print("=" * 80, flush=True)
                    print(f"\nAnalysis completed in {elapsed_time:.2f} seconds", flush=True)
                    
                    if result.metadata:
                        logger.info("Analysis metadata:")
                        print("\nMetadata:", flush=True)
                        for key, value in result.metadata.items():
                            print(f"{key}: {value}", flush=True)
                            logger.info(f"{key}: {value}")
                else:
                    error_msg = getattr(result, 'error', 'Unknown error') if result else 'No result returned'
                    logger.error(f"Analysis failed after {elapsed_time:.2f} seconds: {error_msg}")
                    print(f"\nAnalysis failed: {error_msg}", flush=True)
                    if result and result.metadata:
                        logger.error("Error metadata:")
                        print("\nError metadata:", flush=True)
                        for key, value in result.metadata.items():
                            print(f"{key}: {value}", flush=True)
                            logger.error(f"{key}: {value}")
                            
        except asyncio.TimeoutError:
            logger.error("Analysis timed out after 5 minutes")
            print("\nAnalysis timed out after 5 minutes", flush=True)
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            print(f"\nError during analysis: {str(e)}", flush=True)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"\nError in main: {str(e)}", flush=True)
        raise
    finally:
        # Ensure all output is flushed
        sys.stdout.flush()
        sys.stderr.flush()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {str(e)}", flush=True)
        sys.exit(1)
    finally:
        # Final flush of output
        sys.stdout.flush()
        sys.stderr.flush()