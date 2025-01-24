# Stock News Analysis Framework

## Analysis Workflow
1. 前置準備
   - 檢查 `prompts/{stock_id}_instruction.md` 了解：
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

2. 新聞蒐集流程
   A. 關鍵字邏輯展開（依產業特性）
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

   B. 系統性搜索執行
      - 使用 search_engine.py 搜索新聞
        * 按時間順序搜索
        * 使用邏輯運算符組合
        * 考慮不同語言版本
        * 過濾無關訊息

      - 使用 web_scraper.py 獲取內容
        * 完整保存原文
        * 記錄來源與時間
        * 建立分類標籤
        * 標注重要程度

3. 新聞分析與整理
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

4. 影響分析
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

5. 報告產出
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

3. Comprehensive Analysis Framework (Added 2025/01)
   - Positive Factors
     * Technology advantages with concrete metrics
     * Market expansion with specific progress
     * Strategic positioning success cases
     * Financial performance improvements

   - Negative Factors
     * Technology limitations and constraints
     * Product positioning challenges
     * Competition threats and market pressures
     * Operational inefficiencies

   - Risk Categories
     * Technology Risks
       - Performance limitations
       - Platform dependencies
       - Stability concerns
       - Development uncertainties

     * Market Risks
       - Adoption uncertainties
       - Demand fluctuations
       - Competition dynamics
       - Pricing pressures

     * Operational Risks
       - Resource constraints
       - Implementation challenges
       - Service delivery issues
       - Quality control concerns

     * Financial Risks
       - Margin pressures
       - Investment requirements
       - Cost structure changes
       - Revenue model uncertainties

     * Supply Chain Risks
       - Component dependencies
       - Capacity constraints
       - Cost volatility
       - Supplier relationships

     * Business Model Risks
       - Monetization challenges
       - Customer retention
       - Service scalability
       - Market positioning

4. Monitoring Framework
   - Short-term Indicators (1-3 months)
     * Customer acquisition metrics
     * Implementation progress
     * Initial performance data
     * Early market feedback

   - Mid-term Indicators (3-6 months)
     * Market development pace
     * Competitive responses
     * Technology advancement
     * Business model validation

   - Long-term Indicators (6+ months)
     * Strategic goal achievement
     * Market position evolution
     * Technology roadmap execution
     * Business sustainability metrics

## Required Analysis Components
1. Data Collection
   - Use search_engine.py for news search
   - Use web_scraper.py for content retrieval
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
