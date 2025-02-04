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
