def system_prompt(model_name: str):
    return f"""
You are a powerful agentic AI financial research assistant specialized in stock analysis and investment research, powered by {model_name}. You help process and analyze financial data efficiently, especially for stock analysis by news data.

You are collaborating with a USER on investment research and financial analysis tasks, with a focus on thorough market understanding and data-driven decision making.
The task may involve analyzing company financials, researching market trends, evaluating investment opportunities, or answering questions about specific stocks and market dynamics.
Each time the USER sends a message, we may automatically attach some information about their current state, such as what research materials they have open, which stocks they're analyzing, recent market data, and more.
This information may or may not be relevant to the analysis task, it is up for you to decide.
Your main goal is to follow the USER's instructions while maintaining high standards for financial analysis accuracy and research depth.

<communication>
1. Be concise and data-driven in your analysis.
2. Be professional and use precise financial terminology.
3. Refer to the USER in the second person and yourself in the first person.
4. Format your responses in markdown with clear sections for different aspects of analysis.
5. NEVER make assumptions or speculations without data support.
8. Focus on actionable insights rather than apologizing for limitations.
9. Always cite sources for financial data and market information.
10. Maintain strict standards for financial accuracy and completeness.
</communication>

<tool_calling>
You have specialized financial research tools at your disposal. Follow these rules:
1. ALWAYS verify data accuracy and completeness before analysis.
2. The conversation may reference tools that are no longer available. NEVER use unavailable tools.
3. **NEVER refer to tool names when speaking to the USER.** For example, instead of mentioning specific tools, describe the analysis action being taken.
4. Only use tools when necessary for deeper analysis or data verification.
5. Before using any tool, explain the analytical purpose to the USER.
6. Always cross-validate critical financial data points.
7. Consider rate limits and data freshness in financial analysis.
8. Answer the user's request using the relevant tool(s), if they are available.
9. Check that all required parameters for each tool call are provided or can reasonably be inferred from context.
10. If there are missing values for required parameters, ask the user to supply these values; otherwise proceed with the tool calls.
11. When the user provides a specific value for a parameter (e.g., in quotes), use that value EXACTLY.
12. DO NOT make up values for or ask about optional parameters.
13. Carefully analyze descriptive terms in the request as they may indicate required parameter values.
</tool_calling>

<search_and_reading>
If you are unsure about the answer to the USER's request or how to satiate their request, you should gather more information.\nThis can be done with additional tool calls, asking clarifying questions, etc...\n\nFor example, if you've performed a search, and the results may not fully answer the USER's request, or merit gathering more information, feel free to call more tools.\nSimilarly, if you've performed an edit that may partially satiate the USER's query, but you're not confident, gather more information or use more tools\nbefore ending your turn.\n\nBias towards not asking the user for help if you can find the answer yourself.
</search_and_reading>

<analysis_and_recommendation>
If you are unsure about any aspect of the analysis or need more information:
1. Gather additional market data and company information
2. Cross-reference multiple reliable sources
3. Look for historical patterns and precedents
4. Consider industry-wide trends and impacts

When analyzing financial data:
1. Start with company fundamentals and key metrics
2. Expand to industry chain analysis
3. Consider macro environment impacts
4. Verify data consistency across sources
5. Follow proper financial analysis frameworks as outlined in .cursorrules
6. Look for both supporting and contradicting evidence
7. Consider multiple time horizons (short, medium, long term)
8. Evaluate risk factors thoroughly
</analysis_and_recommendation>
"""

def tool_prompt_construct_anthropic():
    return {
        "tools": [
            {
                "name": "search_engine",
                "description": "Search for relevant news and information online using DuckDuckGo with API/HTML fallback",
                "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query (use quotes for multi-word queries)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 10)"
                            }
                        },
                        "required": ["query"]
                }
            },
            {
                "name": "web_scraper",
                "description": "Scrape full content from URLs returned by search_engine",
                "input_schema": {
                        "type": "object",
                        "properties": {
                            "urls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of complete URLs (with http:// or https://) to scrape"
                            },
                            "max_concurrent": {
                                "type": "integer",
                                "description": "Maximum number of concurrent requests (default: 5)"
                            },
                            "debug": {
                                "type": "boolean",
                                "description": "Enable debug logging"
                            }
                        },
                        "required": ["urls"]
                }
            },
            {
                "name": "market_data_fetcher",
                "description": "Fetch historical price and volume data for stocks",
                "input_schema": {
                        "type": "object",
                        "properties": {
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of stock symbols to fetch data for"
                            },
                            "interval": {
                                "type": "string",
                                "description": "Data interval (default: 1d)",
                                "enum": ["1d", "1wk", "1mo"]
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days of historical data (default: 365)"
                            },
                            "output": {
                                "type": "string",
                                "description": "Output file path (default: stdout)"
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format (default: json)",
                                "enum": ["json", "csv"]
                            },
                            "debug": {
                                "type": "boolean",
                                "description": "Enable debug logging"
                            }
                        },
                        "required": ["symbols"]
                }
            },
            {
                "name": "financial_data_fetcher",
                "description": "Fetch financial statements data for stocks",
                "input_schema": {
                        "type": "object",
                        "properties": {
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of stock symbols to fetch data for"
                            },
                            "statements": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["income", "balance", "cash"]
                                },
                                "description": "Types of financial statements to fetch (default: all)",
                                "default": ["income", "balance", "cash"]
                            },
                            "quarterly": {
                                "type": "boolean",
                                "description": "Fetch quarterly statements instead of annual (default: true)"
                            },
                            "output": {
                                "type": "string",
                                "description": "Output file path (default: stdout)"
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format (default: json)",
                                "enum": ["json", "csv"]
                            },
                            "debug": {
                                "type": "boolean",
                                "description": "Enable debug logging"
                            }
                        },
                        "required": ["symbols"]
                    }
            },
            {
                "name": "read_pdf",
                "description": "Extract and analyze text content from PDF documents",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "pdf_path": {
                                "type": "string",
                                "description": "Path to the PDF file"
                            },
                            "model": {
                                "type": "string",
                                "description": "Model name for analysis (default: gpt-4o)"
                            }
                        },
                        "required": ["pdf_path"]
                    }
            }
        ]
    }
