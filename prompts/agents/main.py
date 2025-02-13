"""Module containing core prompt generation functions for search and analysis tasks."""
def writing_planning_prompt() -> str:
   """Generate writing guidelines for analysis reports.

   Returns:
       str: Writing guidelines and formatting instructions
   """
   return """Writing Guidelines for Analysis Reports:

1. Structure and Organization
   - Begin with an executive summary
   - Use clear section headings and subheadings
   - Maintain logical flow between sections
   - End with clear conclusions and action points

2. Content Requirements
   - Focus on factual, data-driven analysis
   - Support claims with specific evidence
   - Include quantitative metrics where possible
   - Address both positive and negative factors
   - Consider short-term and long-term implications

3. Language and Style
   - Use clear, professional language
   - Avoid ambiguous statements
   - Be concise and precise
   - Use industry-standard terminology
   - Maintain objective tone

4. Data Presentation
   - Present numbers in consistent format
   - Use appropriate units and currencies
   - Include time periods for all data
   - Compare with relevant benchmarks
   - Cite data sources clearly

5. Risk Analysis
   - Identify key risk factors
   - Assess probability and impact
   - Consider mitigating factors
   - Highlight monitoring metrics
   - Include both internal and external risks

6. Recommendations
   - Base on analyzed data
   - Consider practical feasibility
   - Provide specific action items
   - Include implementation timeline
   - Address potential challenges

7. Quality Standards
   - Ensure accuracy of all data
   - Cross-verify critical information
   - Maintain internal consistency
   - Follow standard formatting
   - Include proper citations

8. Technical Details
   - Use appropriate charts and graphs
   - Include relevant technical metrics
   - Explain complex concepts clearly
   - Provide necessary context
   - Define specialized terms

9. Market Context
   - Consider broader market conditions
   - Include competitor analysis
   - Address industry trends
   - Examine regulatory environment
   - Evaluate market positioning

10. Future Outlook
   - Project future scenarios
   - Identify growth opportunities
   - Consider potential challenges
   - Include key metrics to monitor
   - Set realistic expectations."""


def planning_prompt(
   company_news: str,
   company_instruction: str,
   chip_instruction: str,
   technical_analysis_instruction: str,
   writing_instruction: str,
   planning_instruction: str,
   user_message: str,
) -> str:
   """Generate prompt for agent usage planning.

   Args:
      company_news: Collected news content to analyze
      company_instruction: Company-specific analysis instructions
      chip_instruction: Chip industry analysis instructions
      technical_analysis_instruction: Technical analysis framework
      writing_instruction: Writing style and format instructions
      user_message: User's query or request

   Returns:
      Formatted prompt for agent usage planning
   """
   return f"""Please develop a comprehensive analysis plan using the available agents to answer the user's question `{user_message}`.

<Analysis Context>
1. Company and Industry Characteristics
{company_instruction}

2. Market Sentiment Analysis Framework
{chip_instruction}

3. Technical Analysis Framework
{technical_analysis_instruction}

4. Writing Guidelines
{writing_instruction}

5. News Content to Analyze
{company_news}

6. Writing Guidelines
{planning_instruction}
</Analysis Context>

Available Analysis Agents:

1. Research Agent (research_agent.py)
   - Purpose: Fundamental research and news analysis
   - Capabilities:
     * News content analysis
     * Company research
     * Industry analysis
     * Market research
     * Competitive analysis

2. Technical Analysis Agent (ta_agents.py)
   - Purpose: Technical market analysis
   - Capabilities:
     * Price trend analysis
     * Volume analysis
     * Technical indicators
     * Chart pattern recognition
     * Market timing signals

3. Chip Analysis Agent (chip_agent.py)
   - Purpose: Semiconductor industry specific analysis
   - Capabilities:
     * Supply chain analysis
     * Industry cycle analysis
     * Technology trend analysis
     * Market demand analysis
     * Competitive landscape analysis

For each analysis phase, please specify:
1. Which agent(s) to use
2. Analysis objectives and scope
3. Required input data
4. Expected analysis output
5. Dependencies on other agents' outputs
6. Validation and cross-checking methods

Special considerations:
1. Logical sequence of agent deployment
2. Integration of different analysis perspectives
3. Cross-validation between agents
4. Completeness of analysis coverage
5. Efficiency of analysis process
6. Quality assurance measures"""


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
