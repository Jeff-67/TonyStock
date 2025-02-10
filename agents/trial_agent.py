"""Trial agent module for interacting with Claude AI model.

This module implements a chat agent that can interact with Claude AI model,
process its responses, execute tools based on model requests, and verify
tool execution results. It provides a structured way to handle conversations
with tool usage capabilities.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from opik import track

from prompts.agents.planning import report_planning_prompt
from prompts.tools.tools_schema import (
    tool_prompt_construct_anthropic,
    tool_prompt_construct_openai,
)
from settings import Settings
from tools.analysis.analysis_tool import PlanningTool
from tools.core.tool_protocol import Tool
from tools.llm_api import aquery_llm
from tools.research.research_tool import ResearchTool
from tools.technical_analysis.ta_tool import TATool
from tools.chips_analysis.chips_tool import ChipsTool
from tools.time.time_tool import get_current_time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
settings = Settings()


class ToolExecutionError(Exception):
    """Raised when a tool execution fails."""
    pass


@dataclass
class ToolExecutionResult:
    """Result of a tool execution including success status and output.

    Attributes:
        success: Whether the tool execution was successful
        tool_name: Name of the tool that was executed
        result: Optional result data from the tool execution
        message: Optional message describing the execution result
    """
    success: bool
    tool_name: str
    result: Optional[Any] = None
    message: str = ""


@dataclass
class ModelResponse:
    """Structured response from the Claude model.

    Attributes:
        stop_reason: Reason why the model stopped generating
        content: List of content blocks from the model
        tool_use: Optional tool use request from the model
        text_content: Optional extracted text content from the response
    """
    stop_reason: str
    content: List[Any]
    tool_use: Optional[Dict[str, Any]] = None
    text_content: Optional[str] = None


class Agent:
    """Agent for interacting with Claude AI model."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        tools: Optional[Dict[str, Tool]] = None,
    ):
        """Initialize the LLM agent.

        Args:
            provider: Provider name
            model_name: Model name
            tools: Tools
            stock_name: Stock name for system prompt
        """
        self.provider = provider
        self.model_name = model_name
        self.tools: Dict[str, Tool] = tools if tools is not None else {}

        # Initialize system message in history
        system_text = report_planning_prompt(current_time=get_current_time())
        self.message_history: List[Dict[str, Any]] = [
            {"role": "system", "content": system_text},
            {
                "role": "system",
                "content": "如果有user問你你是誰，或是問候你，請回答你的專長是分析京鼎、文曄還有群聯這三隻股票的觀察家。",
            },
        ]
        self.company_news: list[Dict[str, Any]] = []
        self.current_plan: Optional[str] = None
        self.current_company: Optional[str] = None
        self.current_user_message: Optional[str] = None

    @track()
    async def generate_plan(self, user_message: str, company_name: str) -> str:
        """Generate analysis plan for the given company and user message.

        Args:
            user_message: User's query or request
            company_name: Name of the company to analyze

        Returns:
            Generated analysis plan
        """
        try:
            # Store user message first
            self.current_user_message = user_message
            
            planning_tool = PlanningTool(lambda: self.company_news)
            plan = await planning_tool.execute({
                "company_name": company_name,
                "user_message": user_message
            })
            self.current_plan = plan
            self.current_company = company_name
            
            # Add plan to message history
            self.message_history.append({
                "role": "assistant",
                "content": f"分析計畫：\n{plan}"
            })
            
            return plan
        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}")
            raise

    @track()
    async def execute_analysis_step(self, step_name: str, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a single analysis step using the specified tool.

        Args:
            step_name: Name of the analysis step
            tool_name: Name of the tool to use
            tool_input: Input parameters for the tool

        Returns:
            Analysis result for this step
        """
        try:
            logger.info(f"Executing {step_name} using {tool_name}")
            result = await self.process_tool_call(tool_name, tool_input)
            
            # Add result to message history
            self.message_history.append({
                "role": "assistant",
                "content": f"{step_name} 分析結果：\n{result}"
            })
            
            return result
        except Exception as e:
            logger.error(f"Error executing {step_name}: {str(e)}")
            raise

    @track()
    async def execute_analysis_plan(self) -> str:
        """Execute the current analysis plan.

        Returns:
            Combined analysis results
        """
        if not self.current_plan or not self.current_company or not self.current_user_message:
            raise ValueError("No analysis plan, company, or user message set")

        try:
            # 1. 執行研究步驟
            await self.execute_analysis_step(
                "市場研究",
                "research",
                {
                    "company_name": self.current_company,
                    "user_message": self.current_user_message
                }
            )

            # 2. 執行技術分析
            await self.execute_analysis_step(
                "技術分析",
                "technical_analysis",
                {
                    "symbol": self.current_company,
                    "user_message": self.current_user_message
                }
            )

            # 3. 執行籌碼分析
            await self.execute_analysis_step(
                "籌碼分析",
                "chips_analysis",
                {
                    "company_name": self.current_company,
                    "user_message": self.current_user_message
                }
            )

            # 4. 生成最終報告
            final_report = await self.execute_analysis_step(
                "綜合分析",
                "analysis_report",
                {
                    "company_name": self.current_company,
                    "report_type": "comprehensive",
                    "user_message": self.current_user_message
                }
            )

            return final_report
        except Exception as e:
            logger.error(f"Error executing analysis plan: {str(e)}")
            raise

    @track()
    async def call_model(self) -> ModelResponse:
        """Make an API call to the model."""
        try:
            # Create new list with shallow copies of each message dict
            messages = [dict(msg) for msg in self.message_history]

            tool_prompt_text = (
                tool_prompt_construct_anthropic()
                if self.provider == "anthropic"
                else tool_prompt_construct_openai()
            )

            return await aquery_llm(
                messages=messages,
                model=self.model_name,
                provider=self.provider,
                tools=tool_prompt_text,
            )
        except Exception as e:
            logger.error(f"Model call failed: {str(e)}")
            raise

    @track()
    async def process_tool_call(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Any:
        """Process a tool call and return the result."""
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                raise ToolExecutionError(f"Unknown tool: {tool_name}")
            return await tool.execute(tool_input)
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")

    @track(project_name="tony_stock")
    async def chat(self, user_message: str) -> str:
        """Handle the chat flow with tool usage."""
        try:
            # Extract company name from user message
            company_name = None
            if "京鼎" in user_message:
                company_name = "京鼎"
            elif "文曄" in user_message:
                company_name = "文曄"
            elif "群聯" in user_message:
                company_name = "群聯"

            if not company_name:
                return "抱歉，我只能分析京鼎、文曄和群聯這三家公司。請問您想了解哪一家公司？"

            # Add user message to history
            self.message_history.append({"role": "user", "content": user_message})

            try:
                # 1. 生成分析計畫
                await self.generate_plan(user_message, company_name)
                
                # 2. 執行分析計畫
                final_report = await self.execute_analysis_plan()
                
                # 3. 添加最終報告到歷史記錄
                self.message_history.append({
                    "role": "assistant",
                    "content": final_report
                })
                
                return final_report
                
            except Exception as e:
                logger.error(f"Error in analysis workflow: {str(e)}")
                return f"分析過程中發生錯誤：{str(e)}"

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return f"Error during chat: {str(e)}"


async def main():
    """Run an interactive chat session with the agent."""
    # Create agent first without tools
    agent = Agent(
        provider="anthropic",
        model_name="claude-3-sonnet-20240229",
        tools={},  # Empty tools dict initially
    )

    # Now set up tools using the fully created agent
    tools: Dict[str, Tool] = {
        "research": ResearchTool(lambda news: agent.company_news.extend(news)),
        "technical_analysis": TATool(),
        "chips_analysis": ChipsTool(),
    }

    # Update agent's tools
    agent.tools = tools

    # Test chips analysis
    print("\nTesting Chips Analysis:")
    response = await agent.chat("請從各個面向詳細分析京鼎(3413)，並且給予未來的預測")
    print('='*100)
    print(response)
    print('='*100)


if __name__ == "__main__":
    asyncio.run(main())
