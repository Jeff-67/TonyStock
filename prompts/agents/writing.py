"""Writing analysis prompt templates and generators.

This module contains prompt templates and generators for writing analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class WritingData:
    """Writing analysis data structure."""
    company: str
    title: str
    content: str
    analysis_type: str
    sources: List[Dict[str, str]]
    timestamp: datetime
    metadata: Optional[Dict[str, str]] = None

class WritingPromptGenerator:
    """Generator for writing analysis prompts."""
    
    @staticmethod
    def format_sources(sources: List[Dict[str, str]]) -> str:
        """Format sources for display."""
        formatted = []
        for source in sources:
            source_str = f"[{source.get('name', 'Unknown')}, "
            source_str += f"{source.get('date', 'No Date')}, "
            source_str += f"\"{source.get('title', 'No Title')}\"]"
            formatted.append(source_str)
        return "\n".join(formatted)

    @classmethod
    def format_sections(cls, data: WritingData) -> Dict[str, List[str]]:
        """Format all data sections."""
        return {
            "基本資訊": [
                f"公司: {data.company}",
                f"分析類型: {data.analysis_type}",
                f"時間: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            ],
            "內容摘要": [
                f"標題: {data.title}",
                "內容:",
                data.content
            ],
            "資料來源": [
                "引用來源:",
                cls.format_sources(data.sources)
            ]
        }

    @staticmethod
    def generate_system_prompt() -> str:
        """Generate system prompt for writing analysis."""
        with open("prompts/writing_instruction.md", "r") as file:
            return file.read()

    @classmethod
    def get_user_prompt(cls, company: str, data: WritingData) -> str:
        """Generate user prompt with formatted writing data.
        
        Args:
            company: Company name
            data: Writing data containing content and metadata
            
        Returns:
            Formatted prompt string with writing data and analysis request
        """
        prompt_parts = [
            f"# 寫作分析請求：{company}",
            "\n請根據以下資料提供完整的分析報告。\n"
        ]
        
        # 加入格式化的資料區段
        sections = cls.format_sections(data)
        for title, items in sections.items():
            prompt_parts.append(f"\n## {title}")
            prompt_parts.extend(items)
            
        # 加入分析重點
        prompt_parts.extend([
            "\n## 分析重點",
            "請針對以下面向進行詳細分析：",
            "",
            "1. 內容分類與重要性",
            "   - 依影響面向分類",
            "   - 依時間維度分類",
            "   - 評估重要程度",
            "   - 分析優先順序",
            "",
            "2. 影響分析",
            "   - 基本面影響",
            "   - 產業鏈影響",
            "   - 市場反應",
            "   - 競爭態勢",
            "",
            "3. 風險評估",
            "   - 關鍵風險因素",
            "   - 影響程度評估",
            "   - 因應對策建議",
            "   - 監控指標設定",
            "",
            "4. 發展前景",
            "   - 短期觀察重點",
            "   - 中期發展方向",
            "   - 長期策略布局",
            "   - 關鍵成功因素",
            "",
            "5. 具體建議",
            "   - 觀察指標設定",
            "   - 追蹤重點建議",
            "   - 風險控管方式",
            "   - 定期檢視機制"
        ])
        
        return "\n".join(prompt_parts)
