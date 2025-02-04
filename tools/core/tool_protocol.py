"""Core protocol definition for tools.

This module defines the base protocol that all tools must implement.
"""

from typing import Any, Dict, Protocol


class Tool(Protocol):
    """Protocol defining the interface for tools."""

    async def execute(self, input_data: Dict[str, Any]) -> Any:
        """Execute the tool with given input data."""
        ...
