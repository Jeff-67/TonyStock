"""Writing agent module for generating structured analysis reports.

This module implements the writing agent that generates well-structured
analysis reports based on collected data and analysis results.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    """Represents a section in the analysis report."""
    title: str
    content: str
    importance: int  # 1-5, with 5 being most important
    sources: List[str]
    timestamp: datetime

class WritingAgent:
    """Agent responsible for generating structured analysis reports."""
    
    def __init__(self):
        """Initialize the writing agent."""
        self.report_templates = {
            "news_analysis": self._news_analysis_template,
            "technical_analysis": self._technical_analysis_template,
            "fundamental_analysis": self._fundamental_analysis_template,
            "chip_analysis": self._chip_analysis_template,
            "comprehensive": self._comprehensive_template
        }
        
    async def generate_report(
        self,
        report_type: str,
        analysis_data: Dict[str, Any],
        company_info: Dict[str, str],
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a structured report based on analysis data.
        
        Args:
            report_type: Type of report to generate
            analysis_data: Collected analysis data
            company_info: Basic company information
            user_query: Optional original user query
            
        Returns:
            Generated report with metadata
        """
        try:
            # Get appropriate template
            template_func = self.report_templates.get(report_type)
            if not template_func:
                raise ValueError(f"Unknown report type: {report_type}")
                
            # Generate report sections
            sections = await template_func(
                analysis_data=analysis_data,
                company_info=company_info
            )
            
            # Organize sections by importance
            organized_sections = sorted(
                sections,
                key=lambda x: x.importance,
                reverse=True
            )
            
            # Format final report
            report = self._format_report(
                sections=organized_sections,
                company_info=company_info,
                report_type=report_type,
                user_query=user_query
            )
            
            return {
                "status": "success",
                "report": report,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": report_type,
                    "company": company_info,
                    "sections_count": len(sections)
                }
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def _news_analysis_template(
        self,
        analysis_data: Dict[str, Any],
        company_info: Dict[str, str]
    ) -> List[ReportSection]:
        """Template for news analysis reports."""
        sections = []
        
        # Recent major news
        if news_data := analysis_data.get("news", []):
            sections.append(
                ReportSection(
                    title="重大新聞摘要",
                    content=self._format_news_summary(news_data),
                    importance=5,
                    sources=[news["source"] for news in news_data],
                    timestamp=datetime.now()
                )
            )
            
        # Industry trends
        if trends := analysis_data.get("industry_trends", {}):
            sections.append(
                ReportSection(
                    title="產業趨勢分析",
                    content=self._format_trends(trends),
                    importance=4,
                    sources=trends.get("sources", []),
                    timestamp=datetime.now()
                )
            )
            
        return sections
        
    async def _technical_analysis_template(
        self,
        analysis_data: Dict[str, Any],
        company_info: Dict[str, str]
    ) -> List[ReportSection]:
        """Template for technical analysis reports."""
        sections = []
        
        # Price trends
        if price_data := analysis_data.get("price_analysis", {}):
            sections.append(
                ReportSection(
                    title="價格趨勢分析",
                    content=self._format_price_analysis(price_data),
                    importance=5,
                    sources=["historical_price_data"],
                    timestamp=datetime.now()
                )
            )
            
        # Technical indicators
        if indicators := analysis_data.get("technical_indicators", {}):
            sections.append(
                ReportSection(
                    title="技術指標分析",
                    content=self._format_indicators(indicators),
                    importance=4,
                    sources=["technical_indicators"],
                    timestamp=datetime.now()
                )
            )
            
        return sections
        
    async def _fundamental_analysis_template(
        self,
        analysis_data: Dict[str, Any],
        company_info: Dict[str, str]
    ) -> List[ReportSection]:
        """Template for fundamental analysis reports."""
        sections = []
        
        # Financial metrics
        if financials := analysis_data.get("financials", {}):
            sections.append(
                ReportSection(
                    title="財務指標分析",
                    content=self._format_financials(financials),
                    importance=5,
                    sources=["financial_statements"],
                    timestamp=datetime.now()
                )
            )
            
        # Growth analysis
        if growth := analysis_data.get("growth_analysis", {}):
            sections.append(
                ReportSection(
                    title="成長性分析",
                    content=self._format_growth(growth),
                    importance=4,
                    sources=["financial_statements", "market_data"],
                    timestamp=datetime.now()
                )
            )
            
        return sections
        
    async def _chip_analysis_template(
        self,
        analysis_data: Dict[str, Any],
        company_info: Dict[str, str]
    ) -> List[ReportSection]:
        """Template for chip analysis reports."""
        sections = []
        
        # Institutional investors
        if institutional := analysis_data.get("institutional_investors", {}):
            sections.append(
                ReportSection(
                    title="法人動向分析",
                    content=self._format_institutional(institutional),
                    importance=5,
                    sources=["twse_data"],
                    timestamp=datetime.now()
                )
            )
            
        # Margin trading
        if margin := analysis_data.get("margin_trading", {}):
            sections.append(
                ReportSection(
                    title="融資融券分析",
                    content=self._format_margin(margin),
                    importance=4,
                    sources=["twse_data"],
                    timestamp=datetime.now()
                )
            )
            
        return sections
        
    async def _comprehensive_template(
        self,
        analysis_data: Dict[str, Any],
        company_info: Dict[str, str]
    ) -> List[ReportSection]:
        """Template for comprehensive analysis reports."""
        sections = []
        
        # Combine sections from all templates
        for template in [
            self._news_analysis_template,
            self._technical_analysis_template,
            self._fundamental_analysis_template,
            self._chip_analysis_template
        ]:
            template_sections = await template(
                analysis_data=analysis_data,
                company_info=company_info
            )
            sections.extend(template_sections)
            
        return sections
        
    def _format_report(
        self,
        sections: List[ReportSection],
        company_info: Dict[str, str],
        report_type: str,
        user_query: Optional[str]
    ) -> str:
        """Format the final report from sections."""
        # Header
        report = [
            f"# {company_info['name']} ({company_info['stock_id']}) 分析報告",
            f"報告類型: {report_type}",
            f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        if user_query:
            report.extend([
                "## 分析目標",
                user_query,
                ""
            ])
            
        # Add sections
        for section in sections:
            report.extend([
                f"## {section.title}",
                section.content,
                "",
                "資料來源:",
                *[f"- {source}" for source in section.sources],
                ""
            ])
            
        return "\n".join(report)
        
    def _format_news_summary(self, news_data: List[Dict[str, Any]]) -> str:
        """Format news summary section."""
        summary = []
        for news in sorted(
            news_data,
            key=lambda x: x.get("importance", 0),
            reverse=True
        ):
            summary.extend([
                f"### {news['title']}",
                f"日期: {news['date']}",
                f"來源: {news['source']}",
                "",
                news['summary'],
                ""
            ])
        return "\n".join(summary)
        
    def _format_trends(self, trends: Dict[str, Any]) -> str:
        """Format industry trends section."""
        formatted = [
            "### 主要趨勢",
            *[f"- {trend}" for trend in trends.get("main_trends", [])],
            "",
            "### 影響因素",
            *[f"- {factor}" for factor in trends.get("impact_factors", [])],
            "",
            "### 未來展望",
            *[f"- {outlook}" for outlook in trends.get("outlook", [])]
        ]
        return "\n".join(formatted)
        
    def _format_price_analysis(self, price_data: Dict[str, Any]) -> str:
        """Format price analysis section."""
        analysis = [
            f"### 價格區間",
            f"52週高點: {price_data.get('52w_high')}",
            f"52週低點: {price_data.get('52w_low')}",
            f"當前價格: {price_data.get('current_price')}",
            "",
            "### 趨勢分析",
            *[f"- {trend}" for trend in price_data.get("trends", [])]
        ]
        return "\n".join(analysis)
        
    def _format_indicators(self, indicators: Dict[str, Any]) -> str:
        """Format technical indicators section."""
        formatted = []
        for indicator, value in indicators.items():
            formatted.extend([
                f"### {indicator}",
                f"數值: {value.get('value')}",
                f"信號: {value.get('signal')}",
                ""
            ])
        return "\n".join(formatted)
        
    def _format_financials(self, financials: Dict[str, Any]) -> str:
        """Format financial metrics section."""
        metrics = [
            "### 關鍵財務指標",
            f"本益比(P/E): {financials.get('pe_ratio')}",
            f"股價淨值比(P/B): {financials.get('pb_ratio')}",
            f"殖利率: {financials.get('dividend_yield')}%",
            "",
            "### 獲利能力",
            f"營業毛利率: {financials.get('gross_margin')}%",
            f"營業利益率: {financials.get('operating_margin')}%",
            f"淨利率: {financials.get('net_margin')}%"
        ]
        return "\n".join(metrics)
        
    def _format_growth(self, growth: Dict[str, Any]) -> str:
        """Format growth analysis section."""
        analysis = [
            "### 營收成長",
            f"年增率: {growth.get('yoy_revenue_growth')}%",
            f"季增率: {growth.get('qoq_revenue_growth')}%",
            "",
            "### 獲利成長",
            f"年增率: {growth.get('yoy_profit_growth')}%",
            f"季增率: {growth.get('qoq_profit_growth')}%"
        ]
        return "\n".join(analysis)
        
    def _format_institutional(self, institutional: Dict[str, Any]) -> str:
        """Format institutional investors section."""
        analysis = [
            "### 三大法人買賣超",
            f"外資: {institutional.get('foreign_investors')}",
            f"投信: {institutional.get('investment_trust')}",
            f"自營商: {institutional.get('dealers')}",
            "",
            "### 近期趨勢",
            *[f"- {trend}" for trend in institutional.get("trends", [])]
        ]
        return "\n".join(analysis)
        
    def _format_margin(self, margin: Dict[str, Any]) -> str:
        """Format margin trading section."""
        analysis = [
            "### 融資餘額",
            f"當前餘額: {margin.get('margin_balance')}",
            f"較前日: {margin.get('margin_change')}",
            "",
            "### 融券餘額",
            f"當前餘額: {margin.get('short_balance')}",
            f"較前日: {margin.get('short_change')}"
        ]
        return "\n".join(analysis) 