"""Module containing core prompt generation functions for search and analysis tasks."""


def searching_framework_prompt(
    company_name: str,
    stock_id: str | None,
    current_time: str,
    company_instruction: str,
    searching_instruction: str,
    user_message: str,
) -> str:
    """Generate prompt for search framework analysis.

    Args:
        company_name: Target company name
        stock_id: Company stock ID
        current_time: Current time in Asia/Taipei timezone
        company_instruction: Company specific instructions
        searching_instruction: Additional search keywords instructions
        user_message: User message
    Returns:
        Formatted prompt for search framework analysis
    """
    return f"""Current time: {current_time}

For {company_name} (Stock ID: {stock_id if stock_id else 'N/A'}), help me generate a comprehensive set of search queries to understand its investment opportunity by considering the user message: `{user_message}`.

First, consider these core questions about the company:

1. 為什麼會賺錢？(Why is it profitable?)
   - Business model and revenue streams
   - Core competencies and competitive advantages
   - Key products/services and their market positioning
   - Value chain position and pricing power

2. 賺多少錢？(How much does it earn?)
   - Current financial performance
   - Profit margins and profitability metrics
   - Revenue growth trends
   - Cash flow generation capability

3. 未來會賺多少錢？(Future earning potential?)
   - Growth catalysts and opportunities
   - Order visibility and backlog
   - Capacity expansion plans
   - New product/market development
   - Industry growth drivers

4. 此產業的競爭如何？(Industry competition landscape?)
   - Market share analysis
   - Competitor strategies and movements
   - Industry supply-demand dynamics
   - Entry barriers and threats
   - Regulatory environment

5. 他的優勢是什麼？(Competitive advantages?)
   - Technology leadership
   - Customer relationships
   - Cost advantages
   - Brand value/Market position
   - Patents and intellectual property

6. 他的劣勢是什麼？(Disadvantages/Weaknesses?)
   - Technology gaps or limitations
   - Customer concentration risks
   - Cost structure challenges
   - Market position vulnerabilities
   - Resource constraints
   - Financial weaknesses
   - Geographic limitations
   - Management risks

Then, based on the user's message and company context, expand your search scope to include relevant external factors that could impact these core questions:

A. 產業鏈關聯 (Industry Chain Connections)
   - How do industry chain dynamics affect the core questions?
   - What upstream/downstream trends are relevant?
   - How do supply chain changes impact the company?

B. 總體環境 (Macro Environment)
   - Which global economic factors are relevant?
   - What geopolitical events could impact the analysis?
   - How do government policies affect the situation?

C. 市場趨勢 (Market Trends)
   - What are the relevant technology transitions?
   - How are customer preferences changing?
   - What new market opportunities or threats exist?

D. 競爭格局 (Competitive Landscape)
   - How are competitor actions affecting the situation?
   - What are the changes in market share?
   - How is the industry structure evolving?

Please analyze the user's message and generate search queries that:
1. Address the relevant core questions (1-6)
2. Incorporate necessary external factors (A-D) that could impact those core questions
3. Consider both immediate and longer-term implications
4. Connect company-specific issues with broader industry/market context

Output your response as a raw JSON array of search queries (without any markdown code blocks or additional text).
Each query object should have:
{{
    "query": str,  // The actual search query combining company identifiers with keywords
    "core_question": str,  // Which core question (1-6) this query primarily addresses
    "external_factors": [str],  // List of relevant external factors (A-D) this query considers
    "purpose": str,  // What specific information we're looking for
    "expected_insights": str,  // What insights we expect to gain from this query
    "reasoning": str  // Why this query is relevant to the user's message
}}

<Company-specific context and industry characteristics>
{company_instruction}
</Company-specific context and industry characteristics>

<Searching keywords instruction>
{searching_instruction}
</Searching keywords instruction>"""


def analysis_report_prompt(
    company_news: str, company_instruction: str, writing_instruction: str
) -> str:
    """Generate prompt for news analysis report.

    Args:
        company_news: Collected news content to analyze
        company_instruction: Company-specific analysis instructions
        writing_instruction: Writing style and format instructions

    Returns:
        Formatted prompt for generating analysis report
    """
    return f"""Please analyze the provided news content and generate a comprehensive analysis report following the structured framework below.

<Company Context and Industry Characteristics>
{company_instruction}
</Company Context and Industry Characteristics>

<Writing Guidelines>
{writing_instruction}
</Writing Guidelines>

<News Content to Analyze>
{company_news}
</News Content to Analyze>

Based on the above framework, please analyze the news content following the writing guidelines provided."""
