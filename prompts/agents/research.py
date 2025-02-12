"""Research analysis prompt templates and generators.

This module contains prompt templates and generators for research analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from datetime import datetime

@dataclass
class ResearchData:
    """Research analysis data."""
    company: str
    query: str
    framework_queries: int
    total_results: int
    search_results: List[Dict[str, Any]]
    timestamp: datetime

class ResearchPromptGenerator:
    """Generator for research analysis prompts."""
    
    @staticmethod
    def format_search_results(results: List[Dict[str, Any]]) -> str:
        """Format search results for display.
        
        Args:
            results: List of search results with queries and content
            
        Returns:
            Formatted string of search results
        """
        formatted = []
        
        for result in results:
            query_item = result["query"]
            formatted.append(f"\n## {query_item.get('context', 'Research Results')}")
            formatted.append(f"Query: {query_item['query']}\n")
            
            for search_result in result["search_results"]:
                if search_result.get("error"):
                    continue
                    
                formatted.append(f"### {search_result.get('title', 'No Title')}")
                formatted.append(f"Source: {search_result.get('url', 'No URL')}\n")
                content = search_result.get("content", "").strip()
                if content:
                    formatted.append(content)
                formatted.append("---\n")
                
        return "\n".join(formatted)

    @staticmethod
    def generate_system_prompt() -> str:
        """Generate system prompt for research analysis."""
        with open("prompts/research_instruction.md", "r") as file:
            return file.read()

    @classmethod
    def get_user_prompt(cls, company: str, data: ResearchData) -> str:
        """Generate user prompt with formatted research data.
        
        Args:
            company: Company name
            data: Research data containing search results
            
        Returns:
            Formatted prompt string with research data and analysis request
        """
        prompt_parts = [
            f"# Research Analysis Request for {company}",
            f"\nOriginal Query: {data.query}",
            f"\nResearch Scope:",
            f"- Total Queries: {data.framework_queries}",
            f"- Total Results: {data.total_results}",
            f"- Research Time: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n",
            "\n## Research Results",
            cls.format_search_results(data.search_results),
            "\n## Analysis Requirements",
            "Please provide a comprehensive analysis focusing on:",
            "",
            "1. Key Findings",
            "   - Main developments and announcements",
            "   - Critical business updates",
            "   - Strategic initiatives",
            "",
            "2. Market Impact",
            "   - Industry implications",
            "   - Competitive position changes",
            "   - Market opportunities and challenges",
            "",
            "3. Strategic Analysis",
            "   - Business strategy alignment",
            "   - Growth initiatives",
            "   - Innovation and development",
            "",
            "4. Risk Assessment",
            "   - Potential challenges",
            "   - Market risks",
            "   - Mitigation strategies",
            "",
            "5. Future Outlook",
            "   - Growth prospects",
            "   - Development roadmap",
            "   - Key areas to monitor",
            "",
            "Please ensure:",
            "- Clear organization of findings",
            "- Source attribution for key points",
            "- Balanced perspective",
            "- Actionable insights",
            "- Time-sensitive context"
        ]
        
        return "\n".join(prompt_parts)
