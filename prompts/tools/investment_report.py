"""Provides prompt templates for investment report analysis using LLMs."""


def get_metadata_extraction_prompt(content: str) -> str:
    """
    Generate prompt for extracting metadata from investment report content.

    Args:
        content (str): The markdown content of the investment report

    Returns:
        str: Formatted prompt for metadata extraction
    """
    return f"""你是一個專業的投資報告分析助手。請從以下投資報告內容中提取以下元數據：

1. 發布日期 (publish_date)：使用 YYYY-MM-DD 格式
2. 來源機構 (source)：報告發布的投顧機構名稱
3. 語言 (language)：使用 ISO 639-1 代碼，例如 'zh-TW' 或 'en-US'

請僅返回這三個欄位的資訊，格式如下：
{{
    "publish_date": "YYYY-MM-DD",
    "source": "機構名稱",
    "language": "語言代碼"
}}

投資報告內容：
{content}
"""


def get_report_type_prompt(content: str) -> str:
    """
    Generate prompt for extracting report type information from investment report content.

    Args:
        content (str): The markdown content of the investment report

    Returns:
        str: Formatted prompt for report type extraction
    """
    return f"""你是一個專業的投資報告分析助手。請從以下投資報告內容中提取報告類型資訊，分為四個層級：

1. level_1：報告類型，必須是以下其中之一：
   - 個股分析：針對單一股票的分析報告
   - 產業分析：針對整個產業或次產業的分析報告

2. level_2：市場別，必須是以下其中之一：
   - 台股：台灣上市櫃股票
   - 美股：美國上市股票
   - 陸股：中國上市股票
   - 其他：其他市場股票

3. level_3：產業類別，必須是以下其中之一：
   - 科技股：包含半導體、電子零組件、資訊服務等
   - 金融股：包含銀行、保險、證券等
   - 傳產股：包含紡織、塑化、鋼鐵等
   - 電信股：包含電信服務、網路服務等
   - 其他：其他產業類別

4. level_4：
   - 如果是個股分析，請提供股票代碼（如：2330.TW）
   - 如果是產業分析，請提供產業名稱（如：半導體產業）

請僅返回這四個欄位的資訊，格式如下：
{{
    "level_1": "個股分析/產業分析",
    "level_2": "市場別",
    "level_3": "產業類別",
    "level_4": "股票代碼或產業名稱"
}}

投資報告內容：
{content}
"""


def get_contents_extraction_prompt(content: str) -> str:
    """
    Generate prompt for extracting report contents.

    Args:
        content (str): The markdown content of the investment report

    Returns:
        str: Formatted prompt for content extraction
    """
    return f"""你是一個專業的投資報告分析助手。請從以下投資報告內容中提取以下資訊並回傳JSON`：

1. title：報告標題，包含股票代號和主要觀點
2. summary：報告摘要，100-200字的核心論點總結
3. key_points：3-5個重點觀察

請僅返回這些欄位的資訊，JSON格式如下：
{{
    "title": "報告標題",
    "summary": "報告摘要",
    "key_points": [
        "重點1",
        "重點2",
        "重點3"
    ]
}}

注意事項：
1. 標題需包含股票代號（如有）和核心投資論點
2. 摘要需涵蓋公司現況、優勢和未來發展
3. 重點需具體且量化，包含數據支持
4. 使用原文的數據和描述，不要自行推測或計算

投資報告內容：
{content}
"""
