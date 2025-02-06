"""Module containing prompt generation functions for report planning and writing."""


def search_experience_prompt() -> str:
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


def analysis_experience_prompt() -> str:
    """Generate analysis experience prompt for stock analysis.

    Returns:
        Formatted prompt string for the analysis experience
    """
    return """
## Analysis Response Structure Best Practices (Added 2025/01)
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

## Analysis Response Best Practices
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

5. Analysis Response Quality
   - Clear data visualization
   - Consistent terminology
   - Regular updates
   - Actionable recommendations
"""
