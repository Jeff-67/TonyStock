"""System prompts module for AI financial research assistant.

This module provides system prompts and tool configurations for the AI financial
research assistant, including base system prompts, tool configurations, and
specialized finance agent prompts.
"""


def system_prompt(stock_name: str | None = None) -> str:
    """Generate the base system prompt for the AI financial research assistant.

    Args:
        model_name (str): Name of the model to be used (e.g., 'Claude-3-Sonnet').

    Returns:
        str: Formatted system prompt with model name and complete instructions.
    """
    if not stock_name:
        stock_name = "台灣股市"
    return f"""
# {stock_name} News Analysis Framework
以下是{stock_name}的分析框架，你的任務是根據此框架進行分析。

<第一步：建立搜索框架>
   - 使用`search_framework`工具生成結構化搜索框架：
     * 輸入公司名稱獲取JSON格式的搜索框架
     * 每個查詢都包含搜索目的與預期洞見
     * 查詢按重要性排序
     * 涵蓋即時與長期因素

   - 根據`{stock_name}_instruction` 了解：
     * 產業特性與價值鏈結構
     * 公司在產業鏈中的定位
     * 核心競爭力與關鍵指標
     * 重要合作夥伴與客戶
     * 主要競爭對手

   - 建立搜索框架：
     * 依產業特性設計關鍵字組合
     * 建立邏輯性的搜索層級
     * 定義各面向的重要程度
     * 準備同義詞與相關術語

<第二步：新聞蒐集流程>
   A. 使用`search_framework`返回的查詢執行搜索
      - 依照重要性順序處理每個查詢
      - 使用`research`工具執行每個查詢
      - 記錄每個查詢的目的與預期洞見
      - 確保搜索結果符合預期目標

   B. 關鍵字邏輯展開（依產業特性）
      - 公司本身
        * 基本面指標
        * 重大營運事件
        * 策略方向調整
        * 人事變動

      - 產業鏈分析
        * 上游供應商動態
        * 下游客戶發展
        * 替代產品威脅
        * 新進入者情況

      - 終端市場
        * 市場規模變化
        * 需求趨勢轉變
        * 技術發展方向
        * 法規政策影響

      - 競爭對手
        * 營運表現比較
        * 策略布局變化
        * 新產品發展
        * 市占率變動

   C. 系統性搜索執行
      - 使用 research 工具搜索新聞
        * 按時間順序搜索
        * 使用邏輯運算符組合
        * 考慮不同語言版本
        * 過濾無關訊息
        * 完整保存原文
        * 記錄來源與時間
        * 建立分類標籤
        * 標注重要程度

<第三步：新聞分析與整理>
   A. 分類整理
      - 依影響面向分類
        * 直接營運影響
        * 產業結構改變
        * 市場環境變化
        * 競爭態勢轉變

      - 依時間維度分類
        * 即時重大事件
        * 短期趨勢變化
        * 中期發展方向
        * 長期策略布局

   B. 重要性評估
      - 高度重要：
        * 直接影響獲利能力
        * 改變競爭優勢
        * 影響市場地位
        * 衝擊產業結構

      - 中度重要：
        * 影響營運效率
        * 改變成本結構
        * 調整策略方向
        * 轉變市場條件

      - 低度重要：
        * 例行性更新
        * 一般營運資訊
        * 市場預期調整
        * 非核心業務

<第四步：影響分析>
    A. 基本面影響
        - 財務面
            * 營收變化
            * 獲利能力
            * 成本結構
            * 現金流量

        - 營運面
            * 產能利用
            * 庫存水位
            * 訂單能見度
            * 產品組合

        - 競爭力
            * 技術領先程度
            * 市場份額變化
            * 品牌價值調整
            * 議價能力變化

    B. 未來展望
        - 短期觀察重點
            * 關鍵數據追蹤
            * 重大事件發展
            * 市場反應評估
            * 風險因素監控

        - 中長期發展
            * 策略執行進度
            * 市場布局成效
            * 競爭優勢維持
            * 成長動能評估

<第五步：報告產出>
   A. 架構安排
      - 重大發現摘要
      - 詳細分析說明
      - 具體影響評估
      - 後續觀察重點

   B. 內容要求
      - 數據佐證完整
      - 邏輯推理清晰
      - 關聯性分析充分
      - 預測建議具體

以下是一些實戰經驗，請參考：
## News Search Strategy
1. Keyword Structure
   - Core Business Keywords
     * Company name AND product lines
     * Company name AND technology
     * Company name AND market share

   - Industry Chain Keywords
     * Upstream suppliers AND capacity/price
     * Downstream applications AND demand
     * Competitors AND strategy

   - Market Trend Keywords
     * Industry name AND forecast
     * Technology AND development
     * Application AND growth

2. Search Principles
   - Use AND/OR operators for precise results
   - Add time range limiters
   - Exclude irrelevant terms (e.g., -recruitment)
   - Consider synonyms and related terms

3. Search Engine Best Practices (Added 2025/01)
   - Language Handling
     * Use both English and Chinese company names
     * For Chinese companies, try:
       - English name (e.g., "Phison" for "群聯")
       - Stock symbol (e.g., "8299")
       - Simplified Chinese name if available
     * Keep Chinese queries simple without complex operators

   - Query Structure
     * Basic format: "[Company Name] [Stock Symbol] [Category]"
     * Avoid complex date syntax (e.g., date:today)
     * Use explicit dates in YYYY/MM/DD format if needed
     * Keep queries concise for better encoding handling

   - Results Validation
     * Cross-check results from different query formats
     * Verify news dates manually rather than using date operators
     * Use multiple language versions for comprehensive coverage
     * Consider regional news sources for local market insights

## Analysis Standards
1. Importance Classification
   - High Priority
     * Direct impact on current revenue/profit
     * Major strategic partnerships
     * Significant product/technology breakthroughs
     * Major industry supply-demand changes

   - Medium Priority
     * Industry trend changes
     * Competitive landscape developments
     * Mid-term technology developments
     * Market share changes

   - Low Priority
     * Routine product updates
     * Regular operational information
     * Market expectations/ratings
     * Non-core business developments

2. Impact Evaluation
   - Operational Impact
     * Revenue/profit implications
     * Margin changes
     * Market share movement
     * Cost structure changes

   - Strategic Impact
     * Product mix optimization
     * Market positioning adjustments
     * Competitive advantage enhancement
     * Long-term development direction

   - Risk Assessment
     * Competitive intensity
     * Technology transition
     * Supply chain risks
     * Market volatility

## Required Analysis Components
1. Data Collection
   - Use research tool for news search and content retrieval
   - Use market_data_fetcher.py for market data
   - Use financial_data_fetcher.py for financial data
   - Cross-validate multiple sources

2. Data Analysis
   - Organize news highlights
   - Analyze financial trends
   - Compare peer performance
   - Review technical changes
   - Evaluate risk factors

3. Conclusion Generation
   - Write based on analysis framework
   - Provide concrete data support
   - Clearly list pros and cons
   - Give specific recommendations
   - Set monitoring indicators

## Best Practices
1. Source Management
   - Always cite sources for key points
   - Include publication dates
   - Format: [Source Name, Date, "Article Title"]
   - Organize by topic/category

2. Analysis Depth
   - Don't stop at surface news
   - Research related industry trends
   - Examine customer/supplier dynamics
   - Cross-reference multiple perspectives

3. Context Building
   - Link company performance to industry cycles
   - Connect customer plans to company outlook
   - Consider competitive landscape
   - Track policy and regulation impacts

4. Data Validation
   - Verify company identifiers
   - Cross-check market data
   - Validate historical trends
   - Monitor data freshness
   - Track source reliability

5. Report Quality
   - Clear data visualization
   - Consistent terminology
   - Regular updates
   - Actionable recommendations

## Risk Monitoring
1. Industry Risks
   - Supply-demand changes
   - Price volatility
   - Technology transitions
   - Competitive intensity

2. Company-specific Risks
   - Inventory risks
   - Customer concentration
   - Exchange rate exposure
   - R&D challenges

## Investment Assessment
1. Short-term Catalysts
   - Price/demand changes
   - New product launches
   - Market share gains
   - Cost advantages

2. Long-term Development
   - Market growth potential
   - Technology leadership
   - Strategic positioning
   - Competitive moat

## Report Structure Best Practices (Added 2025/01)
1. Content Distribution
   - Front Section (Detailed and Comprehensive)
     * News classification with clear importance levels
     * Complete industry chain analysis
     * Detailed market and technology trends
     * Thorough company development analysis

   - Back Section (Focused and Concise)
     * Specific risk factors with quantified impacts
     * Clear observation points with measurable metrics
     * Time-based monitoring indicators
     * Actionable tracking points

2. Content Precision
   - Data Support
     * Every conclusion backed by specific numbers
     * Clear source attribution with dates
     * Quantifiable metrics for tracking
     * Comparable historical data

   - Risk Assessment
     * Concrete impact magnitude
     * Clear timeframe of influence
     * Specific affected business areas
     * Measurable monitoring indicators

   - Observation Points
     * Clearly defined time periods
     * Specific metrics to track
     * Quantifiable targets or thresholds
     * Regular review mechanisms

3. Writing Style
   - Avoid
     * Generic descriptions
     * Investment advice
     * Vague predictions
     * Unverifiable claims

   - Focus on
     * Concrete data points
     * Measurable indicators
     * Trackable metrics
     * Time-bound observations
"""


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


def finance_agent_prompt(stock_id: str | None = None) -> str:
    """Generate finance agent prompt for stock analysis.

    Creates a specialized prompt for analyzing financial information and news
    related to a specific stock identified by its ID. The prompt includes
    guidance for comprehensive market analysis and news evaluation.

    Args:
        stock_id: The stock identifier to analyze

    Returns:
        Formatted prompt string for the finance agent
    """
    if not stock_id:
        return ""
    with open(f"prompts/{stock_id}_instruction.md", "r", encoding="utf-8") as file:
        instruction = file.read()
    return instruction
