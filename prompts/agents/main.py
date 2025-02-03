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
        company_instruction: Company specific instructions

    Returns:
        Formatted prompt for search framework analysis
    """
    return f"""Current time: {current_time}

For {company_name} (Stock ID: {stock_id if stock_id else 'N/A'}), help me generate a comprehensive set of search queries to understand its investment opportunity.

Consider the company-specific context and industry characteristics provided below to:
1. Identify key areas that need investigation
2. Focus on both company-specific strengths/weaknesses and industry-wide opportunities/threats
3. Cover both immediate catalysts and long-term value drivers
4. Include market positioning, competitive advantages, and potential risks

Please output your response as a raw JSON array of search queries (without any markdown code blocks or additional text).
Each query object should have:
{{
    "query": str,  // The actual search query combining company identifiers with keywords
    "purpose": str,  // What specific information we're looking for
    "expected_insights": str  // What insights we expect to gain from this query
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
