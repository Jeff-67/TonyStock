from .enhanced_stock_analyzer import EnhancedStockAnalyzer
from .news_sentiment_analyzer import NewsSentimentAnalyzer
import os
from datetime import datetime

class StockReportGenerator:
    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.stock_analyzer = EnhancedStockAnalyzer(stock_id)
        self.news_analyzer = NewsSentimentAnalyzer(stock_id)
        self.report_dir = "reports"
        
    def ensure_report_dir(self):
        """確保報告目錄存在"""
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
            
    def generate_full_report(self):
        """生成完整報告"""
        self.ensure_report_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成技術分析報告和圖表
        chart_path = f"{self.report_dir}/{self.stock_id}_technical_{timestamp}.png"
        self.stock_analyzer.plot_technical_chart(chart_path)
        tech_report_path = f"{self.report_dir}/{self.stock_id}_technical_{timestamp}.md"
        tech_report = self.stock_analyzer.generate_report(tech_report_path)
        
        # 生成新聞情緒分析報告
        self.news_analyzer.fetch_news()
        self.news_analyzer.analyze_sentiment()
        news_report_path = f"{self.report_dir}/{self.stock_id}_news_{timestamp}.md"
        news_report = self.news_analyzer.generate_sentiment_report(news_report_path)
        
        # 生成綜合報告
        full_report_path = f"{self.report_dir}/{self.stock_id}_full_report_{timestamp}.md"
        
        # 獲取基本資訊和財務指標
        basic_info = self.stock_analyzer.get_basic_info()
        financial_metrics = self.stock_analyzer.get_financial_metrics()
        
        # 生成完整報告
        report = f"""# {basic_info['Company Name']} ({self.stock_id}) 投資分析報告
        
## 執行摘要
- 報告日期: {datetime.now().strftime("%Y-%m-%d")}
- 公司名稱: {basic_info['Company Name']}
- 產業: {basic_info['Industry']}
- 市值: {basic_info['Market Cap']:,.0f} TWD

## 投資重點
1. 基本面分析
   - 本益比: {basic_info['PE Ratio']:.2f}
   - 股價淨值比: {basic_info['PB Ratio']:.2f}
   - 52週高點: {basic_info['52 Week High']}
   - 52週低點: {basic_info['52 Week Low']}

2. 財務表現
   - 營收: {financial_metrics.get('Revenue', 'N/A'):,.0f} TWD
   - 毛利: {financial_metrics.get('Gross Profit', 'N/A'):,.0f} TWD
   - 淨利: {financial_metrics.get('Net Income', 'N/A'):,.0f} TWD
   - 營業現金流: {financial_metrics.get('Operating Cash Flow', 'N/A'):,.0f} TWD

3. 技術面分析
![技術分析圖表]({chart_path})

4. 新聞輿情分析
{news_report}

## 風險因素
1. 市場風險
   - 產業競爭
   - 原物料價格波動
   - 匯率風險

2. 營運風險
   - 產能利用率
   - 研發進度
   - 法規遵循

## 投資建議
"""
        
        # 根據技術指標和新聞情緒給出建議
        latest = self.stock_analyzer.data.iloc[-1]
        avg_sentiment = sum(score['score'] for score in self.news_analyzer.sentiment_scores) / len(self.news_analyzer.sentiment_scores) if self.news_analyzer.sentiment_scores else 0
        
        # 綜合評估
        technical_score = 0
        if latest['RSI'] < 30:
            technical_score += 1
        elif latest['RSI'] > 70:
            technical_score -= 1
            
        if latest['MACD'] > latest['Signal']:
            technical_score += 1
        else:
            technical_score -= 1
            
        if latest['Close'] > latest['MA20']:
            technical_score += 1
        else:
            technical_score -= 1
            
        # 加入投資建議
        report += "\n### 綜合評估\n"
        report += f"- 技術面評分: {technical_score} (-3到3)\n"
        report += f"- 新聞情緒評分: {avg_sentiment:.2f} (-1到1)\n"
        
        if technical_score > 0 and avg_sentiment > 0:
            report += "\n建議: 可考慮買入\n"
            report += "- 技術面呈現強勢\n"
            report += "- 新聞情緒偏正面\n"
        elif technical_score < 0 and avg_sentiment < 0:
            report += "\n建議: 建議觀望\n"
            report += "- 技術面呈現弱勢\n"
            report += "- 新聞情緒偏負面\n"
        else:
            report += "\n建議: 持續觀察\n"
            report += "- 技術面與基本面出現分歧\n"
            report += "- 建議待訊號明確後再進場\n"
        
        # 保存報告
        with open(full_report_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        return full_report_path 