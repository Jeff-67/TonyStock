"""Module containing prompt generation functions for report planning and writing."""


def writing_planning_prompt() -> str:
    """Generate writing report prompt for stock news analysis.

    Returns:
        Formatted prompt string for the writing report
    """
    return """
<第一步：新聞分析與整理>
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

<第二步：影響分析>
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

<第三步：報告產出>
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


def report_planning_prompt(
    stock_name: str | None = None, current_time: str | None = None
) -> str:
    """Generate the base system prompt for the AI financial research assistant.

    Args:
        model_name (str): Name of the model to be used (e.g., 'Claude-3-Sonnet').

    Returns:
        str: Formatted system prompt with model name and complete instructions.
    """
    if not stock_name:
        stock_name = "台灣股市"
    return f"""
Current Time: {current_time}
# {stock_name} News Analysis Framework
以下是{stock_name}的分析框架，你的任務是根據此框架進行分析。

<第一步：建立搜索框架>
   - 使用`search_framework`工具生成結構化搜索框架：
     * 輸入公司名稱獲取JSON格式的搜索框架
     * 每個查詢都包含搜索目的與預期洞見
     * 查詢按重要性排序
     * 涵蓋即時與長期因素

<第二步：新聞蒐集流程>
   A. 使用`search_framework`返回的查詢執行搜索
      - 依照重要性順序處理每個查詢
      - 使用`research`工具執行每個查詢
      - 記錄每個查詢的目的與預期洞見
      - 確保搜索結果符合預期目標

   B. 系統性搜索執行
      - 使用 research 工具搜索新聞
        * 按時間順序搜索
        * 考慮不同語言版本
        * 完整保存原文
        * 記錄來源與時間
        * 建立分類標籤

<第三步：新聞影響分析與整理並報告產出>
   A. 使用`analysis_report`工具進行分析以及報告產出
      - 輸入參數準備：
        * company_name：公司名稱

      - 報告要求：
        * 數據佐證完整
        * 邏輯推理清晰
        * 關聯性分析充分
        * 建議具體
        * 時效性資訊標註日期
        * 訊息需註明來源
"""


def search_planning_prompt() -> str:
    """Generate search planning prompt for stock analysis.

    Args:
        stock_name: Name of the stock to analyze

    Returns:
        Formatted prompt string for the search planning
    """
    return """
## News Search Strategy
- 關鍵字按造邏輯展開（依產業特性）
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

以下是一些實戰經驗，請參考：
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
"""
