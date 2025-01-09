from .llm_api import query_llm
from .web_scraper import process_urls
from .search_engine import search
import pandas as pd
from datetime import datetime, timedelta
import json
import asyncio

class NewsSentimentAnalyzer:
    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.news_data = []
        self.sentiment_scores = []
        
    def fetch_news(self, days=30):
        """獲取新聞"""
        # 使用search_engine搜尋新聞
        query = f"{self.stock_id} 新聞 最新"
        search_results = search(query)
        
        # 使用web_scraper獲取新聞內容
        urls = [result['url'] for result in search_results]
        contents = asyncio.run(process_urls(urls))  # 使用 asyncio.run 運行異步函數
        
        for url, content in zip(urls, contents):
            if content:
                self.news_data.append({
                    'url': url,
                    'content': content,
                    'date': datetime.now().strftime('%Y-%m-%d')  # 實際應該從新聞內容提取日期
                })
                
    def analyze_sentiment(self):
        """分析新聞情緒"""
        if not self.news_data:
            return
            
        # 暫時使用簡單的關鍵詞分析
        positive_keywords = ['成長', '增加', '上漲', '突破', '利多', '獲利', '看好', '創新高']
        negative_keywords = ['下跌', '虧損', '衰退', '利空', '風險', '警示', '跌停', '創新低']
        
        for news in self.news_data:
            content = news['content'].lower()
            
            # 計算正面和負面關鍵詞出現次數
            positive_count = sum(1 for keyword in positive_keywords if keyword in content)
            negative_count = sum(1 for keyword in negative_keywords if keyword in content)
            
            # 計算情緒分數 (-1 到 1)
            total_count = positive_count + negative_count
            if total_count == 0:
                score = 0
            else:
                score = (positive_count - negative_count) / total_count
                
            # 提取關鍵字
            keywords = []
            for keyword in positive_keywords:
                if keyword in content:
                    keywords.append(keyword)
            for keyword in negative_keywords:
                if keyword in content:
                    keywords.append(keyword)
                    
            # 生成評分理由
            if score > 0:
                reason = f"新聞中包含{positive_count}個正面關鍵詞，{negative_count}個負面關鍵詞，整體偏正面"
            elif score < 0:
                reason = f"新聞中包含{positive_count}個正面關鍵詞，{negative_count}個負面關鍵詞，整體偏負面"
            else:
                reason = "新聞中正面和負面關鍵詞數量相當，或無明顯情緒傾向"
                
            sentiment_data = {
                'score': score,
                'reason': reason,
                'keywords': keywords,
                'url': news['url'],
                'date': news['date']
            }
            self.sentiment_scores.append(sentiment_data)
                
    def generate_sentiment_report(self, output_path):
        """生成情緒分析報告"""
        if not self.sentiment_scores:
            return "No sentiment data available"
            
        # 計算平均情緒分數
        avg_score = sum(score['score'] for score in self.sentiment_scores) / len(self.sentiment_scores)
        
        # 找出最正面和最負面的新聞
        sorted_scores = sorted(self.sentiment_scores, key=lambda x: x['score'])
        most_negative = sorted_scores[0]
        most_positive = sorted_scores[-1]
        
        report = f"""# {self.stock_id} 新聞情緒分析報告

## 整體情緒摘要
- 分析新聞數量: {len(self.sentiment_scores)}
- 平均情緒分數: {avg_score:.2f}
- 情緒傾向: {"正面" if avg_score > 0.3 else "負面" if avg_score < -0.3 else "中性"}

## 最正面新聞
- 分數: {most_positive['score']}
- 原因: {most_positive['reason']}
- 關鍵字: {', '.join(most_positive['keywords'])}
- 連結: {most_positive['url']}

## 最負面新聞
- 分數: {most_negative['score']}
- 原因: {most_negative['reason']}
- 關鍵字: {', '.join(most_negative['keywords'])}
- 連結: {most_negative['url']}

## 詳細分析
"""
        
        # 添加所有新聞的分析
        for score in self.sentiment_scores:
            report += f"""
### {score['date']}
- 情緒分數: {score['score']}
- 原因: {score['reason']}
- 關鍵字: {', '.join(score['keywords'])}
- 連結: {score['url']}
"""
        
        # 保存報告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        return report 