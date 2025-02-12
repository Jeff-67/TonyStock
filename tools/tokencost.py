"""Token cost calculation module.

This module provides functions for calculating the cost of LLM API calls based on token usage.
"""

from typing import Dict, Optional

# Cost per 1K tokens for different models
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "gpt-4o": {
        "input": 0.03,  # $0.03 per 1K tokens
        "output": 0.06,  # $0.06 per 1K tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.0015,  # $0.0015 per 1K tokens
        "output": 0.002,  # $0.002 per 1K tokens
    },
    "claude-3-sonnet-20240229": {
        "input": 0.03,  # $0.03 per 1K tokens
        "output": 0.06,  # $0.06 per 1K tokens
    }
}

def calculate_cost_by_tokens(
    model: str,
    input_tokens: int,
    output_tokens: int,
    model_costs: Optional[Dict[str, Dict[str, float]]] = None
) -> float:
    """Calculate the cost of an LLM API call based on token usage.

    Args:
        model: The model name
        input_tokens: Number of tokens in the input/prompt
        output_tokens: Number of tokens in the output/completion
        model_costs: Optional custom model costs dictionary

    Returns:
        float: The calculated cost in dollars
    """
    costs = model_costs or MODEL_COSTS
    model_name = model.split("/")[-1]  # Handle provider prefixes like "openai/"
    
    if model_name not in costs:
        # Default to gpt-4o costs if model not found
        model_name = "gpt-4o"
    
    model_cost = costs[model_name]
    input_cost = (input_tokens / 1000.0) * model_cost["input"]
    output_cost = (output_tokens / 1000.0) * model_cost["output"]
    
    return input_cost + output_cost 