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
            "description": """Search for relevant news and information online using DuckDuckGo with API/HTML fallback.

Query Construction Guidelines:
1. Basic Format (Most Effective):
   - Use: "[Company Name] [Stock Code] [Key Products/Technology] [Year]"
   - Example: "群聯 8299 PCIe SSD 2025"
   - Keep it simple, avoid complex operators

2. Core Business Search:
   - Focus on main products and technologies
   - Example: "群聯 控制晶片 AI 2025"
   - Example: "Phison NAND Flash 2025"

3. Industry Chain Search:
   - Add one topic at a time
   - Example: "群聯 8299 營收"
   - Example: "群聯 8299 新產品"

4. Search Tips:
   - Use both company name and stock code
   - Add year for recent news
   - Keep queries concise (4-5 terms max)
   - Mix Chinese and English terms
   - Avoid special operators (date:, site:, etc.)""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query following the query construction guidelines above",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "search_framework",
            "description": """Generate a comprehensive search framework for company analysis.

Framework Generation Guidelines:
1. Industry Understanding:
   - Analyzes industry characteristics and value chain
   - Identifies company's position and competitive advantages
   - Maps key stakeholders (suppliers, customers, competitors)

2. Search Categories:
   - Company-specific: financials, operations, strategy
   - Industry chain: upstream/downstream dynamics
   - Market trends: demand, technology, regulations
   - Competition: market share, product development

3. Output Format:
   - Returns JSON array of structured search queries
   - Each query includes purpose and expected insights
   - Queries are prioritized by importance
   - Covers both immediate and long-term factors""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Company name to generate search framework for (e.g., '群聯', '京鼎')",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "analysis_report",
            "description": """Generate a comprehensive stock news analysis report based on collected news and information.

Input Schema:
- company_name: Name of the company to analyze""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to analyze",
                    }
                },
                "required": ["company_name"],
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
                "description": """Search for relevant news and information online using DuckDuckGo with API/HTML fallback.

Query Construction Guidelines:
1. Basic Format (Most Effective):
   - Use: "[Company Name] [Stock Code] [Key Products/Technology] [Year]"
   - Example: "群聯 8299 PCIe SSD 2025"
   - Keep it simple, avoid complex operators

2. Core Business Search:
   - Focus on main products and technologies
   - Example: "群聯 控制晶片 AI 2025"
   - Example: "Phison NAND Flash 2025"

3. Industry Chain Search:
   - Add one topic at a time
   - Example: "群聯 8299 營收"
   - Example: "群聯 8299 新產品"

4. Search Tips:
   - Use both company name and stock code
   - Add year for recent news
   - Keep queries concise (4-5 terms max)
   - Mix Chinese and English terms
   - Avoid special operators (date:, site:, etc.)""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query following the query construction guidelines above",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_framework",
                "description": """Generate a comprehensive search framework for company analysis.

Framework Generation Guidelines:
1. Industry Understanding:
   - Analyzes industry characteristics and value chain
   - Identifies company's position and competitive advantages
   - Maps key stakeholders (suppliers, customers, competitors)

2. Search Categories:
   - Company-specific: financials, operations, strategy
   - Industry chain: upstream/downstream dynamics
   - Market trends: demand, technology, regulations
   - Competition: market share, product development

3. Output Format:
   - Returns JSON array of structured search queries
   - Each query includes purpose and expected insights
   - Queries are prioritized by importance
   - Covers both immediate and long-term factors""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Company name to generate search framework for (e.g., '群聯', '京鼎')",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    ]
