"""Base agent module providing common functionality for all agents."""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from tools.llm_api import aquery_llm
from prompts.tools.tools_schema import (
    tool_prompt_construct_anthropic,
    tool_prompt_construct_openai,
)

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Structure for analysis results."""
    success: bool
    content: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseAgent:
    """Base agent class with common functionality."""
    
    def __init__(
        self,
        provider: str = "anthropic",
        model_name: str = "claude-3-sonnet-20240229",
        system_prompt: str = "",
    ):
        self.provider = provider
        self.model_name = model_name
        self.message_history: List[Dict[str, Any]] = []
        if system_prompt:
            self.message_history.append({
                "role": "system",
                "content": system_prompt
            })
            
    async def call_model(self) -> tuple[Any, Any]:
        """Make an API call to the model."""
        try:
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
            
    async def analyze(self, query: str, **kwargs) -> AnalysisResult:
        """Base analysis method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement analyze method")
    
    def clear_history(self):
        """Clear message history except system prompt."""
        if self.message_history and self.message_history[0]["role"] == "system":
            self.message_history = [self.message_history[0]]
        else:
            self.message_history = []
            
    def add_message(self, role: str, content: str):
        """Add a message to the history."""
        self.message_history.append({
            "role": role,
            "content": content
        }) 