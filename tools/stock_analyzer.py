import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import json
import logging
import asyncio
import sys
sys.path.append('tools')
from web_scraper import process_urls
from search_engine import search

# 設置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAnalyzer:
    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.twse_url = "https://www.twse.com.tw/zh/"
        self.mops_url = "https://mops.twse.com.tw/mops/web/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_basic_info(self):
        """獲取基本資訊"""
        try:
            # 使用yfinance獲取基本資訊
            stock = yf.Ticker(f"{self.stock_id}.TW")
            info = stock.info
            return {
                "公司名稱": info.get("longName", "N/A"),
                "產業別": info.get("industry", "N/A"),
                "市值": info.get("marketCap", "N/A"),
                "本益比": info.get("trailingPE", "N/A"),
                "股價淨值比": info.get("priceToBook", "N/A"),
                "52週高點": info.get("fiftyTwoWeekHigh", "N/A"),
                "52週低點": info.get("fiftyTwoWeekLow", "N/A"),
                "平均成交量": info.get("averageVolume", "N/A")
            }
        except Exception as e:
            logger.error(f"獲取基本資訊失敗: {str(e)}")
            return None

    def get_historical_data(self, period="1y"):
        """獲取歷史股價數據"""
        try:
            stock = yf.Ticker(f"{self.stock_id}.TW")
            hist = stock.history(period=period)
            return hist
        except Exception as e:
            logger.error(f"獲取歷史數據失敗: {str(e)}")
            return None

    def calculate_technical_indicators(self, df):
        """計算技術指標"""
        try:
            # 計算KD指標
            df['K'], df['D'] = self._calculate_kd(df)
            
            # 計算MACD
            df['MACD'], df['Signal'], df['Hist'] = self._calculate_macd(df['Close'])
            
            # 計算RSI
            df['RSI'] = self._calculate_rsi(df['Close'])
            
            # 計算移動平均線
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            
            return df
        except Exception as e:
            logger.error(f"計算技術指標失敗: {str(e)}")
            return None

    def _calculate_kd(self, df, n=9, m1=3, m2=3):
        """計算KD指標"""
        df['Highest'] = df['High'].rolling(n).max()
        df['Lowest'] = df['Low'].rolling(n).min()
        df['RSV'] = (df['Close'] - df['Lowest']) / (df['Highest'] - df['Lowest']) * 100
        
        K = pd.Series(index=df.index)
        D = pd.Series(index=df.index)
        
        for i in range(len(df)):
            if i == 0:
                K.iloc[i] = 50
                D.iloc[i] = 50
            else:
                K.iloc[i] = K.iloc[i-1] * (m1-1)/m1 + df['RSV'].iloc[i]/m1
                D.iloc[i] = D.iloc[i-1] * (m2-1)/m2 + K.iloc[i]/m2
        
        return K, D

    def _calculate_macd(self, price, fast=12, slow=26, signal=9):
        """計算MACD指標"""
        exp1 = price.ewm(span=fast, adjust=False).mean()
        exp2 = price.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        hist = macd - signal_line
        return macd, signal_line, hist

    def _calculate_rsi(self, prices, period=14):
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def plot_technical_analysis(self, df):
        """繪製技術分析圖表"""
        try:
            # 設置風格
            plt.style.use('seaborn-v0_8')
            
            # 創建圖表
            fig = plt.figure(figsize=(15, 12))
            gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1])
            
            # K線圖
            ax1 = fig.add_subplot(gs[0])
            df['Open'].plot(ax=ax1, label='Open')
            df['Close'].plot(ax=ax1, label='Close')
            df['High'].plot(ax=ax1, label='High')
            df['Low'].plot(ax=ax1, label='Low')
            df['MA5'].plot(ax=ax1, label='MA5', linestyle='--')
            df['MA20'].plot(ax=ax1, label='MA20', linestyle='--')
            df['MA60'].plot(ax=ax1, label='MA60', linestyle='--')
            ax1.set_title(f'{self.stock_id} Technical Analysis')
            ax1.set_ylabel('Price')
            ax1.legend()
            
            # KD線
            ax2 = fig.add_subplot(gs[1])
            ax2.plot(df.index, df['K'], label='K')
            ax2.plot(df.index, df['D'], label='D')
            ax2.axhline(y=80, color='r', linestyle='--')
            ax2.axhline(y=20, color='g', linestyle='--')
            ax2.set_ylabel('KD Value')
            ax2.legend()
            
            # MACD
            ax3 = fig.add_subplot(gs[2])
            ax3.plot(df.index, df['MACD'], label='MACD')
            ax3.plot(df.index, df['Signal'], label='Signal')
            ax3.bar(df.index, df['Hist'], label='Histogram')
            ax3.set_ylabel('MACD')
            ax3.legend()
            
            plt.tight_layout()
            plt.savefig('technical_analysis.png')
            plt.close()
            
            # 生成技術分析報告
            report = self._generate_technical_analysis_report(df)
            with open('technical_analysis_report.txt', 'w', encoding='utf-8') as f:
                f.write(report)
            
            return True
        except Exception as e:
            logger.error(f"繪製技術分析圖表失敗: {str(e)}")
            return False

    def _generate_technical_analysis_report(self, df):
        """生成技術分析報告"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        report = f"""技術分析報告 - {self.stock_id}
分析日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. 價格分析
-----------------
最新收盤價: {latest['Close']:.2f}
與前一日比較: {(latest['Close'] - prev['Close']):.2f} ({((latest['Close'] - prev['Close'])/prev['Close']*100):.2f}%)
最近高點: {df['High'][-20:].max():.2f}
最近低點: {df['High'][-20:].min():.2f}

2. 移動平均線分析
-----------------
5日均線: {latest['MA5']:.2f}
20日均線: {latest['MA20']:.2f}
60日均線: {latest['MA60']:.2f}
均線排列: {"多頭" if latest['MA5'] > latest['MA20'] > latest['MA60'] else "空頭" if latest['MA5'] < latest['MA20'] < latest['MA60'] else "盤整"}

3. KD指標分析
-----------------
K值: {latest['K']:.2f}
D值: {latest['D']:.2f}
狀態: {"超買" if latest['K'] > 80 else "超賣" if latest['K'] < 20 else "正常"}

4. MACD分析
-----------------
MACD: {latest['MACD']:.2f}
Signal: {latest['Signal']:.2f}
Histogram: {latest['Hist']:.2f}
趨勢: {"多頭" if latest['MACD'] > latest['Signal'] else "空頭"}

5. RSI分析
-----------------
RSI: {latest['RSI']:.2f}
狀態: {"超買" if latest['RSI'] > 70 else "超賣" if latest['RSI'] < 30 else "正常"}

6. 綜合建議
-----------------
"""
        # 添加綜合建議
        signals = []
        if latest['MA5'] > latest['MA20'] > latest['MA60']:
            signals.append("均線呈現多頭排列")
        if latest['MA5'] < latest['MA20'] < latest['MA60']:
            signals.append("均線呈現空頭排列")
        if latest['K'] > 80 or latest['RSI'] > 70:
            signals.append("技術指標顯示超買")
        if latest['K'] < 20 or latest['RSI'] < 30:
            signals.append("技術指標顯示超賣")
        if latest['MACD'] > latest['Signal']:
            signals.append("MACD顯示上升趨勢")
        if latest['MACD'] < latest['Signal']:
            signals.append("MACD顯示下降趨勢")
            
        report += "\n".join(signals)
        
        return report

    def get_institutional_investors(self):
        """獲取法人買賣超資料"""
        # 這裡需要實現從證交所或其他來源獲取法人資料的邏輯
        pass

    def get_financial_statements(self):
        """獲取財務報表數據"""
        # 這裡需要實現從公開資訊觀測站獲取財務報表的邏輯
        pass

    async def fetch_additional_data(self, urls):
        """Fetch additional data using the web scraper."""
        try:
            results = await process_urls(urls, max_concurrent=3)
            for url, content in zip(urls, results):
                print(f"\n=== Content from {url} ===")
                print(content)
                print("=" * 80)
        except Exception as e:
            logger.error(f"Error fetching additional data: {str(e)}")

    async def search_stock_info(self):
        """搜尋股票相關資訊"""
        try:
            # 使用search_engine搜尋相關資訊
            search_queries = [
                f"{self.stock_id} 公司新聞",
                f"{self.stock_id} 財務報表",
                f"{self.stock_id} 產業分析",
                f"{self.stock_id} 法人買賣超"
            ]
            
            all_urls = []
            for query in search_queries:
                # 使用search_engine.py進行搜尋
                search_results = await search(query, max_results=5)
                urls = [result['url'] for result in search_results if result.get('url')]
                all_urls.extend(urls)
            
            # 使用web_scraper.py抓取網頁內容
            contents = await process_urls(all_urls, max_concurrent=5)
            
            # 整理搜尋結果
            analysis_data = self._process_search_results(search_queries, all_urls, contents)
            
            # 儲存分析結果
            self._save_analysis_results(analysis_data)
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"搜尋股票資訊失敗: {str(e)}")
            return None

    def _process_search_results(self, queries, urls, contents):
        """處理搜尋結果"""
        analysis_data = {
            'news': [],
            'financial': [],
            'industry': [],
            'institutional': []
        }
        
        for query, url, content in zip(queries, urls, contents):
            if not content:
                continue
                
            # 根據查詢類型分類內容
            if '新聞' in query:
                analysis_data['news'].append({
                    'url': url,
                    'content': content
                })
            elif '財務報表' in query:
                analysis_data['financial'].append({
                    'url': url,
                    'content': content
                })
            elif '產業分析' in query:
                analysis_data['industry'].append({
                    'url': url,
                    'content': content
                })
            elif '法人買賣超' in query:
                analysis_data['institutional'].append({
                    'url': url,
                    'content': content
                })
        
        return analysis_data

    def _save_analysis_results(self, analysis_data):
        """儲存分析結果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for category, data in analysis_data.items():
            if data:
                filename = f'stock_{self.stock_id}_{category}_{timestamp}.txt'
                with open(filename, 'w', encoding='utf-8') as f:
                    for item in data:
                        f.write(f"\n=== From {item['url']} ===\n")
                        f.write(item['content'])
                        f.write("\n" + "="*80 + "\n")

    async def analyze_stock(self):
        """綜合分析股票"""
        try:
            # 獲取基本資訊
            basic_info = self.get_basic_info()
            logger.info("基本資訊已獲取")

            # 獲取技術分析數據
            hist_data = self.get_historical_data()
            if hist_data is not None:
                hist_data = self.calculate_technical_indicators(hist_data)
                self.plot_technical_analysis(hist_data)
                logger.info("技術分析完成")

            # 搜尋並分析額外資訊
            analysis_data = await self.search_stock_info()
            logger.info("網路資訊搜尋完成")

            # 生成綜合報告
            report = self._generate_comprehensive_report(basic_info, hist_data, analysis_data)
            
            # 儲存報告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f'stock_{self.stock_id}_report_{timestamp}.txt'
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"分析報告已儲存至 {report_filename}")
            
            return report

        except Exception as e:
            logger.error(f"股票分析失敗: {str(e)}")
            return None

    def _generate_comprehensive_report(self, basic_info, hist_data, analysis_data):
        """生成綜合分析報告"""
        report = f"""
股票分析報告 - {self.stock_id}
分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. 基本資訊
-----------------
{json.dumps(basic_info, indent=2, ensure_ascii=False) if basic_info else "無法獲取基本資訊"}

2. 技術分析
-----------------
請參考技術分析圖表及報告文件

3. 新聞摘要
-----------------
{self._summarize_category(analysis_data, 'news') if analysis_data else "無法獲取新聞資料"}

4. 財務分析
-----------------
{self._summarize_category(analysis_data, 'financial') if analysis_data else "無法獲取財務資料"}

5. 產業分析
-----------------
{self._summarize_category(analysis_data, 'industry') if analysis_data else "無法獲取產業資料"}

6. 法人動向
-----------------
{self._summarize_category(analysis_data, 'institutional') if analysis_data else "無法獲取法人資料"}

7. 投資建議
-----------------
{self._generate_investment_advice(basic_info, hist_data, analysis_data)}
"""
        return report

    def _summarize_category(self, analysis_data, category):
        """摘要特定類別的資料"""
        if not analysis_data or category not in analysis_data:
            return "無相關資料"
        
        summary = []
        for item in analysis_data[category]:
            summary.append(f"來源: {item['url']}")
            # 擷取內容的前500個字元作為摘要
            content_summary = item['content'][:500] + "..." if len(item['content']) > 500 else item['content']
            summary.append(content_summary)
            summary.append("-" * 40)
        
        return "\n".join(summary)

    def _generate_investment_advice(self, basic_info, hist_data, analysis_data):
        """生成投資建議"""
        advice = ["基於目前分析結果，投資建議如下："]
        
        # 根據技術分析提供建議
        if hist_data is not None:
            latest = hist_data.iloc[-1]
            if latest['K'] > 80:
                advice.append("技術面：KD指標顯示超買情況，建議注意風險")
            elif latest['K'] < 20:
                advice.append("技術面：KD指標顯示超賣情況，可能有反彈機會")

        # 根據基本面提供建議
        if basic_info:
            pe_ratio = basic_info.get('本益比', 0)
            if pe_ratio and pe_ratio != 'N/A':
                if float(pe_ratio) > 30:
                    advice.append("基本面：本益比偏高，建議謹慎評估")
                elif float(pe_ratio) < 10:
                    advice.append("基本面：本益比偏低，可能具有投資價值")

        # 加入免責聲明
        advice.append("\n免責聲明：以上建議僅供參考，投資人應自行承擔投資風險")
        
        return "\n".join(advice)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Taiwan stock data')
    parser.add_argument('stock_id', type=str, help='Stock ID to analyze (e.g., 2330)')
    parser.add_argument('--period', type=str, default='1y', help='Analysis period (e.g., 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)')
    
    args = parser.parse_args()
    
    analyzer = StockAnalyzer(args.stock_id)
    asyncio.run(analyzer.analyze_stock()) 