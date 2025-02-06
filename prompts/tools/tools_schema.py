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
    ]
