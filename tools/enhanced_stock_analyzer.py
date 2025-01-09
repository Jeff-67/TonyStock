import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import mplfinance as mpf
import talib
import requests
from bs4 import BeautifulSoup
import json

class EnhancedStockAnalyzer:
    def __init__(self, stock_id):
        self.stock_id = f"{stock_id}.TW"
        self.stock = yf.Ticker(self.stock_id)
        self.data = None
        self.period = "1y"
        
    def fetch_data(self):
        """獲取股票數據"""
        self.data = self.stock.history(period=self.period)
        return self.data
        
    def technical_analysis(self):
        """技術分析"""
        if self.data is None:
            self.fetch_data()
            
        # 計算技術指標
        self.data['MA5'] = self.data['Close'].rolling(window=5).mean()
        self.data['MA20'] = self.data['Close'].rolling(window=20).mean()
        self.data['MA60'] = self.data['Close'].rolling(window=60).mean()
        
        # RSI
        self.data['RSI'] = talib.RSI(self.data['Close'].values, timeperiod=14)
        
        # MACD
        macd, signal, hist = talib.MACD(self.data['Close'].values)
        self.data['MACD'] = macd
        self.data['Signal'] = signal
        self.data['Hist'] = hist
        
        # 布林帶
        self.data['Upper'], self.data['Middle'], self.data['Lower'] = talib.BBANDS(
            self.data['Close'].values,
            timeperiod=20
        )
        
        return self.data
        
    def plot_technical_chart(self, save_path=None):
        """繪製技術分析圖表"""
        if self.data is None:
            self.technical_analysis()
            
        # 設置風格
        plt.style.use('seaborn-v0_8')
        
        # 創建子圖
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), gridspec_kw={'height_ratios': [3, 1, 1]})
        
        # 繪製K線圖和均線
        ax1.plot(self.data.index, self.data['MA5'], label='MA5', alpha=0.8)
        ax1.plot(self.data.index, self.data['MA20'], label='MA20', alpha=0.8)
        ax1.plot(self.data.index, self.data['MA60'], label='MA60', alpha=0.8)
        ax1.plot(self.data.index, self.data['Upper'], 'r--', label='Upper BB', alpha=0.5)
        ax1.plot(self.data.index, self.data['Lower'], 'r--', label='Lower BB', alpha=0.5)
        
        # 繪製蠟燭圖
        for i in range(len(self.data)):
            if self.data['Close'].iloc[i] >= self.data['Open'].iloc[i]:
                color = 'red'
            else:
                color = 'green'
            ax1.bar(self.data.index[i], 
                   self.data['Close'].iloc[i] - self.data['Open'].iloc[i],
                   bottom=self.data['Open'].iloc[i],
                   color=color,
                   width=0.6)
        
        # RSI
        ax2.plot(self.data.index, self.data['RSI'], label='RSI', color='purple')
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5)
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5)
        
        # MACD
        ax3.plot(self.data.index, self.data['MACD'], label='MACD', color='blue')
        ax3.plot(self.data.index, self.data['Signal'], label='Signal', color='orange')
        ax3.bar(self.data.index, self.data['Hist'], label='Histogram', color='gray', alpha=0.5)
        
        # 設置標題和標籤
        ax1.set_title(f'{self.stock_id} Technical Analysis')
        ax1.legend()
        ax2.legend()
        ax3.legend()
        
        # 調整布局
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
            
    def get_basic_info(self):
        """獲取基本資訊"""
        info = self.stock.info
        basic_info = {
            'Company Name': info.get('longName', 'N/A'),
            'Industry': info.get('industry', 'N/A'),
            'Market Cap': info.get('marketCap', 'N/A'),
            'PE Ratio': info.get('trailingPE', 'N/A'),
            'PB Ratio': info.get('priceToBook', 'N/A'),
            '52 Week High': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52 Week Low': info.get('fiftyTwoWeekLow', 'N/A'),
            'Average Volume': info.get('averageVolume', 'N/A')
        }
        return basic_info
        
    def get_financial_metrics(self):
        """獲取財務指標"""
        try:
            financials = self.stock.financials
            balance_sheet = self.stock.balance_sheet
            cash_flow = self.stock.cashflow
            
            metrics = {
                'Revenue': financials.iloc[0, 0] if not financials.empty else 'N/A',
                'Gross Profit': financials.iloc[1, 0] if not financials.empty else 'N/A',
                'Net Income': financials.iloc[-1, 0] if not financials.empty else 'N/A',
                'Total Assets': balance_sheet.iloc[0, 0] if not balance_sheet.empty else 'N/A',
                'Total Debt': balance_sheet.iloc[3, 0] if not balance_sheet.empty else 'N/A',
                'Operating Cash Flow': cash_flow.iloc[0, 0] if not cash_flow.empty else 'N/A'
            }
            return metrics
        except Exception as e:
            print(f"Error fetching financial metrics: {e}")
            return {}
            
    def generate_report(self, output_path):
        """生成分析報告"""
        if self.data is None:
            self.technical_analysis()
            
        basic_info = self.get_basic_info()
        financial_metrics = self.get_financial_metrics()
        
        # 計算最新的技術指標值
        latest = self.data.iloc[-1]
        
        report = f"""# {basic_info['Company Name']} ({self.stock_id}) 技術分析報告
        
## 基本資訊
- 產業: {basic_info['Industry']}
- 市值: {basic_info['Market Cap']:,.0f} TWD
- 本益比: {basic_info['PE Ratio']:.2f}
- 股價淨值比: {basic_info['PB Ratio']:.2f}

## 技術指標 (最新)
- 收盤價: {latest['Close']:.2f}
- RSI: {latest['RSI']:.2f}
- MACD: {latest['MACD']:.2f}
- Signal: {latest['Signal']:.2f}

## 趨勢分析
- MA5: {latest['MA5']:.2f}
- MA20: {latest['MA20']:.2f}
- MA60: {latest['MA60']:.2f}

## 布林通道
- 上軌: {latest['Upper']:.2f}
- 中軌: {latest['Middle']:.2f}
- 下軌: {latest['Lower']:.2f}

## 財務指標
- 營收: {financial_metrics.get('Revenue', 'N/A'):,.0f} TWD
- 毛利: {financial_metrics.get('Gross Profit', 'N/A'):,.0f} TWD
- 淨利: {financial_metrics.get('Net Income', 'N/A'):,.0f} TWD
- 營業現金流: {financial_metrics.get('Operating Cash Flow', 'N/A'):,.0f} TWD

## 技術面建議
"""
        
        # 加入技術面建議
        if latest['RSI'] > 70:
            report += "- RSI顯示超買狀態，建議注意獲利了結\n"
        elif latest['RSI'] < 30:
            report += "- RSI顯示超賣狀態，可能存在反彈機會\n"
            
        if latest['MACD'] > latest['Signal']:
            report += "- MACD顯示多頭訊號\n"
        else:
            report += "- MACD顯示空頭訊號\n"
            
        if latest['Close'] > latest['Upper']:
            report += "- 股價突破布林通道上軌，注意回檔風險\n"
        elif latest['Close'] < latest['Lower']:
            report += "- 股價跌破布林通道下軌，可能存在超賣機會\n"
            
        # 保存報告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        return report 