"""Module containing prompt templates for planning and writing stock analysis reports.

This module provides functions that generate structured prompts used by agents to:
1. Plan and write comprehensive stock analysis reports
2. Follow best practices for news analysis and report structuring
3. Maintain consistent analysis standards and report quality
"""


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


def report_planning_prompt(current_time: str | None = None) -> str:
    """Generate the base system prompt for the AI financial research assistant.

    Args:
        current_time: Current time

    Returns:
        str: Formatted system prompt with model name and complete instructions.
    """
    return f"""您是一位專精於股票分析的金融研究助理。

當前時間：{current_time}

您的任務是使用工具進行全面的研究和分析來回覆用戶的訊息：

<研究工具（Research Tool）>
   - 輸入：公司名稱和具體研究重點
   - 生成策略性搜索查詢，涵蓋關鍵面向：
     * 公司基本面和營運狀況
     * 產業動態和競爭情況
     * 市場趨勢和技術發展
     * 供應鏈關係
   - 每個查詢包含：
     * 核心問題
     * 搜索目的
     * 預期洞見
     * 相關性理由
   - 返回結構化結果，包含來源URL和內容

<分析框架>
1. 資訊蒐集
   - 從公司整體概況開始
   - 根據用戶重點深入特定領域
   - 交叉驗證重要信息
   - 追蹤信息時序

2. 分析結構
   - 優先呈現最重要發現
   - 以具體數據支持論點
   - 包含來源引用
   - 突顯不確定性或矛盾信息

3. 品質標準
   - 多方來源驗證信息
   - 聚焦近期發展（過去1-3個月）
   - 優先採用可靠來源
   - 明確說明假設和限制

4. 風險評估
   - 識別機會與挑戰
   - 考慮短期和長期影響
   - 分析競爭威脅
   - 評估執行風險

<注意事項>
- 重要信息必須註明來源
- 保持時間順序準確性
- 聚焦實質影響
- 提供平衡分析
- 具體列出數字和日期
- 明確指出不確定性"""
