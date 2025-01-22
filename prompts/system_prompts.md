# Stock News Analysis Framework

## Analysis Workflow
1. Initial Setup
   - Look up stock-specific instruction file in `prompts/{stock_id}_instruction.md`
   - Define search keywords and analysis framework
   - Set up news monitoring parameters
   - Prepare data collection tools and sources

2. Information Collection Process
   - Search latest news using defined keywords
   - Prioritize news sources based on reliability
   - Cross-validate information from multiple sources
   - Track time sensitivity of information
   - Document source URLs and publication dates

3. Multi-layer Analysis Framework
   A. 框架建構原則
   - 依產業特性客製化分析層級
   - 確保涵蓋所有關鍵影響因素
   - 建立層級間的邏輯關聯
   - 定期檢視並更新分析架構

   B. 基礎分析層級（依產業特性調整）
   第一層：公司基本面
   - 關鍵財務指標（依產業特性選擇）
   - 核心營運數據（產業特有指標）
   - 重大公司事件
   - 競爭優勢分析
     * 市占率變化
     * 技術領先程度
     * 成本結構比較
     * 產品組合優勢
   - 競爭對手動態
     * 同業財務表現
     * 競品推出時程
     * 策略調整方向
     * 研發投入比較
   - 股價技術面

   第二層：產業生態系
   - 產業價值鏈定位（依公司在產業鏈位置調整）
   - 關鍵合作夥伴（依產業特性識別）
   - 產業政策影響（產業特定法規）
   - 供需結構變化
     * 產能擴充計畫
     * 需求趨勢轉變
     * 庫存水位變化
     * 價格走勢影響

   第三層：總體環境（依產業敏感度調整）
   - 總體經濟指標（對產業影響最大的指標）
   - 產業週期階段
   - 技術發展方向
   - 地緣政治因素

   C. 產業客製化指引
   1. 產業特性分析
      - 辨識產業關鍵成功因素
      - 找出產業特有經營模式
      - 定義產業價值鏈結構
      - 識別產業週期特徵

   2. 公司定位評估
      - 在產業鏈中的角色
      - 核心競爭優勢
      - 關鍵利害關係人
      - 主要收入來源

   3. 分析層級調整
      - 依產業特性增減分析層級
      - 調整各層級權重
      - 新增產業特有指標
      - 刪除不相關分析面向

   D. 範例參考（僅供參考，需依個股調整）
   半導體產業：
   第一層：
   - 營收、毛利率、產能利用率
   - 製程技術進展
   - 重大客戶訂單
   - 庫存水位
   - 競爭對手比較
     * 製程技術世代
     * 良率表現
     * 新產品布局
     * 重點客戶重疊
   - 市占率變化

   第二層：
   - 上游原物料供需
   - 下游終端需求
   - 產能擴充計畫
   - 產業政策影響

   電商產業：
   第一層：
   - GMV、活躍用戶數
   - 用戶獲取成本
   - 平均訂單價值
   - 複購率
   - 競爭對手比較
     * 市占率變化
     * 補貼策略
     * 用戶重疊度
     * 獲客成本
   - 平台差異化優勢

   第二層：
   - 供應商合作關係
   - 物流配送體系
   - 支付系統整合
   - 產業政策法規

   第三層：
   - 消費者信心指數
   - 數位化趨勢
   - 支付技術演進
   - 電商法規發展

   E. 框架維護與更新
   - 定期檢視分析架構適用性
   - 根據產業變化調整指標
   - 納入新興影響因素
   - 刪除過時分析面向

4. Impact Assessment Framework
   - 短期（1-3個月）影響
   - 中期（3-12個月）影響
   - 長期（1年以上）影響
   - 風險因素評估

5. Documentation Standards
   - 時間順序紀錄
   - 重要性分類
   - 關聯性分析
   - 影響力評估

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
