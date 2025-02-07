"""Module defining schema and configuration for analysis tools."""


def tool_prompt_construct_anthropic() -> list:
    """Construct tool configuration for Anthropic models.

    Returns:
        dict: Tool configuration dictionary containing search engine,
            web scraper, and PDF reader tool specifications.
    """
    return [
        {
            "name": "research",
            "description": """Strategic news search tool that generates structured queries and returns search results.

Key Features:
1. Generates targeted search queries based on user's request
2. Follows systematic framework covering company, industry, and market aspects
3. Returns structured results with sources and context

Output Format:
[{
    "query": {
        "query": str,           # The actual search query
        "core_question": str,   # Which core question this addresses
        "purpose": str,         # What information we're looking for
        "expected_insights": str, # Expected insights from this query
        "reasoning": str        # Why this query is relevant
    },
    "search_results": [{
        "url": str,            # Source URL
        "context": str         # Relevant content
    }]
}]""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to research (e.g., '群聯', '京鼎')",
                    },
                    "user_message": {
                        "type": "string",
                        "description": "User's specific research request or focus area",
                    },
                },
                "required": ["company_name", "user_message"],
            },
        },
        {
            "name": "technical_analysis",
            "description": """Technical analysis tool using TA-Lib to analyze stock price patterns and indicators.

Key Features:
1. Trend analysis using moving averages
2. Momentum indicators (RSI, MACD, Stochastic)
3. Volatility measures (ATR, Bollinger Bands)
4. Volume analysis and pattern recognition
5. Support/resistance level identification

Output Format:
{
    "trend_analysis": {
        "overall_trend": str,
        "moving_averages": {
            "SMA_50": float,
            "SMA_200": float,
            "EMA_20": float
        }
    },
    "momentum_indicators": {
        "RSI": float,
        "MACD": {
            "macd": float,
            "signal": float,
            "histogram": float
        },
        "Stochastic": {
            "slowK": float,
            "slowD": float
        }
    },
    "volatility_indicators": {
        "ATR": float,
        "Bollinger_Bands": {
            "upper": float,
            "middle": float,
            "lower": float
        }
    },
    "volume_indicators": {
        "OBV": float
    },
    "patterns": List[str],
    "support_resistance": {
        "support_levels": List[float],
        "resistance_levels": List[float]
    }
}""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol to analyze",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data to analyze (default: 200)",
                    },
                },
                "required": ["symbol"],
            },
        },
    ]


def tool_prompt_construct_openai() -> list:
    """Construct tool configuration for OpenAI models.

    Returns:
        list: List of tool configurations in OpenAI format containing search engine,
            web scraper, and other tool specifications.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "research",
                "description": """Strategic news search tool that generates structured queries and returns search results.

Key Features:
1. Generates targeted search queries based on user's request
2. Follows systematic framework covering company, industry, and market aspects
3. Returns structured results with sources and context

Output Format:
[{
    "query": {
        "query": str,           # The actual search query
        "core_question": str,   # Which core question this addresses
        "purpose": str,         # What information we're looking for
        "expected_insights": str, # Expected insights from this query
        "reasoning": str        # Why this query is relevant
    },
    "search_results": [{
        "url": str,            # Source URL
        "context": str         # Relevant content
    }]
}]""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the company to research (e.g., '群聯', '京鼎')",
                        },
                        "user_message": {
                            "type": "string",
                            "description": "User's specific research request or focus area",
                        },
                    },
                    "required": ["company_name", "user_message"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "technical_analysis",
                "description": """Technical analysis tool using TA-Lib to analyze stock price patterns and indicators.

Key Features:
1. Trend analysis using moving averages
2. Momentum indicators (RSI, MACD, Stochastic)
3. Volatility measures (ATR, Bollinger Bands)
4. Volume analysis and pattern recognition
5. Support/resistance level identification

Output Format:
{
    "trend_analysis": {
        "overall_trend": str,
        "moving_averages": {
            "SMA_50": float,
            "SMA_200": float,
            "EMA_20": float
        }
    },
    "momentum_indicators": {
        "RSI": float,
        "MACD": {
            "macd": float,
            "signal": float,
            "histogram": float
        },
        "Stochastic": {
            "slowK": float,
            "slowD": float
        }
    },
    "volatility_indicators": {
        "ATR": float,
        "Bollinger_Bands": {
            "upper": float,
            "middle": float,
            "lower": float
        }
    },
    "volume_indicators": {
        "OBV": float
    },
    "patterns": List[str],
    "support_resistance": {
        "support_levels": List[float],
        "resistance_levels": List[float]
    }
}""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to analyze",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days of historical data to analyze (default: 200)",
                        },
                    },
                    "required": ["symbol"],
                },
            },
        },
    ]
