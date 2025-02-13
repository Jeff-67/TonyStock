"""Token cost calculation module.

This module provides functions for calculating the cost of LLM API calls based on token usage.
"""

from typing import Dict, Optional

# Cost per 1K tokens for different models (USD)
MODEL_COSTS = {
    'gpt-4': {'input': 0.03, 'output': 0.06},
    'gpt-4o': {'input': 0.03, 'output': 0.06},
    'gpt-4-32k': {'input': 0.06, 'output': 0.12},
    'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
    'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015}
}

def calculate_cost_by_tokens(
    model: str = 'gpt-4o',
    input_tokens: int = 0,
    output_tokens: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    **kwargs
) -> float:
    """Calculate cost based on token usage.
    
    Args:
        model: Model name
        input_tokens: Number of input tokens (alternative to prompt_tokens)
        output_tokens: Number of output tokens (alternative to completion_tokens)
        prompt_tokens: Number of input tokens (alternative to input_tokens)
        completion_tokens: Number of output tokens (alternative to output_tokens)
        **kwargs: Additional keyword arguments (ignored)
        
    Returns:
        Calculated cost in USD
    """
    # Get model name and check if it exists in MODEL_COSTS
    if model not in MODEL_COSTS:
        return 0.0
        
    # Use input_tokens if provided, otherwise use prompt_tokens
    input_count = input_tokens if input_tokens > 0 else prompt_tokens
    
    # Use output_tokens if provided, otherwise use completion_tokens
    output_count = output_tokens if output_tokens > 0 else completion_tokens
    
    # Calculate costs
    costs = MODEL_COSTS[model]
    input_cost = (input_count / 1000) * costs['input']
    output_cost = (output_count / 1000) * costs['output']
    
    return input_cost + output_cost 