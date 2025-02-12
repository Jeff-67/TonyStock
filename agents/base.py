"""Base agent module providing common functionality for all agents."""

import logging
from typing import Any, Dict, List, Optional, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from tools.llm_api import aquery_llm, Message
from prompts.tools.tools_schema import (
    tool_prompt_construct_anthropic,
    tool_prompt_construct_openai,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class BaseAnalysisData:
    """Base structure for analysis data."""
    symbol: str
    date: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseAnalysisData':
        """Create instance from dictionary."""
        return cls(**{
            k: v for k, v in data.items() 
            if k in cls.__dataclass_fields__
        })

@dataclass
class AnalysisResult:
    """Structure for analysis results."""
    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    analysis_data: Optional[BaseAnalysisData] = None
    timestamp: datetime = field(default_factory=datetime.now)

class BaseAgent:
    """Base agent class with common functionality."""
    
    def __init__(
        self,
        provider: str = "anthropic",
        model_name: str = "claude-3-sonnet-20240229",
        system_prompt: str = "",
    ):
        """Initialize the base agent.
        
        Args:
            provider: LLM provider (default: anthropic)
            model_name: Model name (default: claude-3-sonnet-20240229)
            system_prompt: System prompt for the agent
        """
        self.provider = provider
        self.model_name = model_name
        self.message_history: List[Dict[str, Any]] = []
        
        # Load system prompt
        if system_prompt:
            self.message_history.append({
                "role": "system",
                "content": system_prompt
            })
        else:
            self._load_default_prompt()
    
    def _load_default_prompt(self):
        """Load default system prompt from file."""
        try:
            prompt_path = Path(__file__).parent.parent / "prompts" / f"{self.__class__.__name__.lower()}_instruction.md"
            if prompt_path.exists():
                with open(prompt_path, "r", encoding="utf-8") as f:
                    self.message_history.append({
                        "role": "system",
                        "content": f.read()
                    })
        except Exception as e:
            logger.warning(f"Failed to load default prompt: {e}")
    
    async def call_model(
        self,
        messages: Optional[List[Message]] = None,
    ) -> Any:
        """Make a simple API call to the model without tools.
        
        Args:
            messages: List of messages to send to the model. If None, uses message history.
            
        Returns:
            Model response
        """
        try:
            if messages is None:
                messages = [dict(msg) for msg in self.message_history]
            
            return await aquery_llm(
                messages=messages,
                model=self.model_name,
                provider=self.provider
            )
        except Exception as e:
            logger.error(f"Model call failed: {str(e)}")
            raise
    
    async def call_tool(
        self,
        messages: Optional[List[Message]] = None,
    ) -> tuple[Any, Any]:
        """Make an API call to the model."""
        try:
            if messages is None:
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
    
    def format_error_response(self, error: Exception) -> AnalysisResult:
        """Format error response."""
        error_msg = str(error)
        logger.error(f"Analysis error: {error_msg}")
        
        return AnalysisResult(
            success=False,
            content="",
            error=error_msg,
            metadata={"error_type": type(error).__name__}
        ) 