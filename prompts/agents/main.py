"""Module containing core prompt generation functions for search and analysis tasks."""


def searching_framework_prompt(
    company_name: str,
    stock_id: str | None,
    current_time: str,
    company_instruction: str,
    searching_instruction: str,
) -> str:
    """Generate prompt for search framework analysis.

    Args:
        company_name: Target company name
        stock_id: Company stock ID
        current_time: Current time in Asia/Taipei timezone
        company_instruction: Company specific instructions including business context,
                           key focus areas, and industry characteristics
        searching_instruction: Additional search keywords instructions
    Returns:
        Formatted prompt for search framework analysis
    """
    return f"""Current time: {current_time}

For {company_name} (Stock ID: {stock_id if stock_id else 'N/A'}), help me generate a comprehensive set of search queries to systematically gather investment-critical information. The search strategy should be tailored based on the company-specific context provided.

Core Information Framework:

1. Business Fundamentals
   - Business model evolution and current state
   - Revenue structure and profit drivers
   - Core competencies and competitive moat
   - Value chain positioning and pricing power
   - Customer base and market segments

2. Financial Performance & Health
   - Revenue and profit trends
   - Margin structure and dynamics
   - Cash flow generation and capital efficiency
   - Balance sheet strength and capital structure
   - Working capital management

3. Growth & Development
   - Organic growth initiatives
   - M&A and strategic investments
   - New product/market development
   - Capacity expansion plans
   - R&D pipeline and innovation

4. Industry & Competition
   - Market share and positioning
   - Competitive landscape changes
   - Industry supply-demand dynamics
   - Entry barriers and disruption risks
   - Regulatory environment impact

5. Operational Excellence
   - Manufacturing capabilities
   - Supply chain management
   - Cost structure optimization
   - Quality control systems
   - Operational efficiency initiatives

6. Risk Assessment
   - Customer concentration
   - Technology obsolescence
   - Supply chain vulnerabilities
   - Financial risks
   - Regulatory compliance
   - Environmental and social risks

External Factor Framework:

A. Supply Chain Dynamics
   - Upstream supplier relationships
   - Downstream customer dynamics
   - Material/component pricing trends
   - Supply chain restructuring

B. Market Evolution
   - Technology transitions
   - Customer preference shifts
   - New market opportunities
   - Substitution threats

C. Policy & Regulation
   - Government policies
   - Industry regulations
   - Environmental standards
   - Trade relationships

D. Macro Factors
   - Economic cycle impact
   - Currency effects
   - Geopolitical influences
   - Regional market conditions

Please generate search queries that:
1. Prioritize the most relevant aspects based on company characteristics
2. Consider industry-specific success factors
3. Focus on company-specific risk factors
4. Address both immediate operational and long-term strategic aspects

Output your response as a raw JSON array of search queries (without any markdown code blocks or additional text).
Each query object should have:
{{
    "query": str,  // The actual search query combining company identifiers with keywords
    "purpose": str,  // What specific information we're looking for
    "expected_insights": str,  // What insights we expect to gain from this query
    "reasoning": str  // Why this information is particularly relevant for this company
}}

<Company-specific context and industry characteristics>
{company_instruction}
</Company-specific context and industry characteristics>

<Searching keywords instruction>
{searching_instruction}
</Searching keywords instruction>"""


def analysis_report_prompt(
    company_news: str,
    company_instruction: str,
    writing_instruction: str,
    user_message: str,
) -> str:
    """Generate prompt for news analysis report.

    Args:
        company_news: Collected news content to analyze
        company_instruction: Company-specific analysis instructions
        writing_instruction: Writing style and format instructions

    Returns:
        Formatted prompt for generating analysis report
    """
    return f"""Please analyze the provided news content and generate a comprehensive analysis report following the structured framework below to answer the user's question `{user_message}`.

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
