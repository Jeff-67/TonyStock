#!/usr/bin/env python3
"""Orchestrate the analysis process."""

import asyncio
import logging
from typing import List, Dict, Any

from agents.capital_agent import CapitalAgent
from agents.technical_agent import TechnicalAgent
from agents.research_agent import ResearchAgent
from agents.core.planning_agent import PlanningAgent
from agents.core.writing_agent import WritingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def analyze_stock(company: str) -> Dict[str, Any]:
    """Analyze a stock.
    
    Args:
        company: Company name or stock ID
        
    Returns:
        Analysis results
    """
    try:
        # Initialize agents
        planning_agent = PlanningAgent(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229"
        )
        
        chips_agent = CapitalAgent(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229"
        )
        
        technical_agent = TechnicalAgent(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229"
        )
        
        finance_agent = ResearchAgent(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229"
        )
        
        writing_agent = WritingAgent(
            provider="anthropic",
            model_name="claude-3-sonnet-20240229"
        )
        
        # Get analysis plan
        plan = await planning_agent.analyze(company)
        if not plan.success:
            raise ValueError(f"Planning failed: {plan.error}")
            
        # Execute analysis tasks
        tasks = []
        
        # Chips analysis
        chips_task = asyncio.create_task(
            chips_agent.analyze(company)
        )
        tasks.append(("chips", chips_task))
        
        # Technical analysis
        technical_task = asyncio.create_task(
            technical_agent.analyze(company)
        )
        tasks.append(("technical", technical_task))
        
        # Financial analysis
        finance_task = asyncio.create_task(
            finance_agent.analyze(
                query=f"分析{company}的基本面",
                company=company
            )
        )
        tasks.append(("finance", finance_task))
        
        # Wait for all tasks
        results = {}
        for name, task in tasks:
            try:
                result = await task
                results[name] = {
                    "success": result.success,
                    "content": result.content,
                    "error": result.error
                }
            except Exception as e:
                logger.error(f"{name} analysis failed: {str(e)}")
                results[name] = {
                    "success": False,
                    "error": str(e)
                }
                
        # Integrate results using writing agent
        try:
            writing_result = await writing_agent.analyze(
                company=company,
                plan=plan.content,
                chips_analysis=results["chips"].get("content"),
                technical_analysis=results["technical"].get("content"),
                financial_analysis=results["finance"].get("content")
            )
            results["summary"] = {
                "success": writing_result.success,
                "content": writing_result.content,
                "error": writing_result.error
            }
        except Exception as e:
            logger.error(f"Writing summary failed: {str(e)}")
            results["summary"] = {
                "success": False,
                "error": str(e)
            }
                
        return {
            "success": True,
            "plan": {
                "success": plan.success,
                "content": plan.content,
                "error": plan.error
            },
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def main():
    """Main entry point."""
    companies = ["京鼎", "文曄", "群聯"]
    
    for company in companies:
        logger.info(f"Analyzing {company}...")
        result = await analyze_stock(company)
        
        if result["success"]:
            logger.info(f"Analysis completed for {company}")
            logger.info("Results:")
            logger.info(f"Plan: {result['plan']}")
            logger.info(f"Chips: {result['results']['chips']}")
            logger.info(f"Technical: {result['results']['technical']}")
            logger.info(f"Finance: {result['results']['finance']}")
            logger.info(f"Summary: {result['results']['summary']}")
        else:
            logger.error(f"Analysis failed for {company}: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 