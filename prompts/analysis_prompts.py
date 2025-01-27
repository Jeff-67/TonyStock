"""Analysis prompts for different types of analysis tasks."""


def searching_framework(
    company_name: str, stock_id: str | None, current_time: str, company_instruction: str
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

Company-specific context and industry characteristics:
{company_instruction}"""
