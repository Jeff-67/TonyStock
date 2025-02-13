"""Shared type definitions."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Message:
    """Message structure for LLM interactions."""
    role: str
    content: str
    name: Optional[str] = None 