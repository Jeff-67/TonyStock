"""Module defining schema and configuration for analysis tools."""


def tool_prompt_construct_anthropic() -> list:
    """Construct tool configuration for Anthropic models.

    Returns:
        dict: Tool configuration dictionary containing integrated research and technical analysis tools.
    """
    return [
        {
            "type": "function",
            "name": "research",
            "description": """新聞和市場研究工具，提供結構化查詢和分析結果。

功能：
1. 公司分析
2. 產業鏈分析
3. 市場環境分析
4. 競爭格局分析

輸出格式：
[{
    "query": {
        "query": str,
        "purpose": str,
        "category": str
    },
    "search_results": [{
        "url": str,
        "title": str,
        "date": str,
        "context": str
    }],
    "analysis": {
        "summary": str,
        "impact": dict,
        "confidence": float
    }
}]""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名稱",
                    },
                    "user_message": {
                        "type": "string",
                        "description": "使用者的研究需求",
                    }
                },
                "required": ["company_name", "user_message"],
            },
        },
        {
            "type": "function",
            "name": "chip_analysis",
            "description": """半導體產業分析工具。

功能：
1. 產業鏈分析 (上中下游)
2. 技術分析 (製程、封裝、設計)
3. 市場分析 (規模、份額、趨勢)
4. 應用領域分析
5. 產能分析
6. 創新追蹤
7. 風險評估

輸出格式：
{
    "industry_chain": dict,
    "technical_analysis": dict,
    "market_analysis": dict,
    "applications": dict,
    "capacity": dict,
    "innovation": dict,
    "risks": dict
}""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名稱",
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "分析類型",
                    }
                },
                "required": ["company_name"],
            },
        },
        {
            "type": "function",
            "name": "technical_analysis",
            "description": """技術分析工具，使用 TA-Lib 分析股價模式和指標。

功能：
1. 趨勢分析 (移動平均線)
2. 動能指標 (RSI、MACD、KD)
3. 波動指標 (ATR、布林通道)
4. 成交量分析
5. 支撐壓力位分析

輸出格式：
{
    "trend_analysis": dict,
    "momentum_indicators": dict,
    "volatility_indicators": dict,
    "volume_indicators": dict,
    "support_resistance": dict
}""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代號",
                    },
                    "days": {
                        "type": "integer",
                        "description": "分析天數",
                    }
                },
                "required": ["symbol"],
            },
        }
    ]


def tool_prompt_construct_openai() -> list:
    """Construct tool configuration for OpenAI models.

    Returns:
        dict: Tool configuration dictionary containing integrated research and technical analysis tools.
    """
    tools = tool_prompt_construct_anthropic()
    return [{"type": "function", "function": tool} for tool in tools]
