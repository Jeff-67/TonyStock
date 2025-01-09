from tools.report_generator import StockReportGenerator
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive stock analysis report')
    parser.add_argument('stock_id', help='Stock ID to analyze')
    args = parser.parse_args()
    
    # 創建報告生成器
    generator = StockReportGenerator(args.stock_id)
    
    # 生成報告
    print(f"開始分析股票 {args.stock_id}...")
    report_path = generator.generate_full_report()
    
    print(f"\n分析完成！報告已保存至: {report_path}")
    
    # 顯示報告內容
    with open(report_path, 'r', encoding='utf-8') as f:
        print("\n報告預覽:")
        print("="*50)
        print(f.read())
        print("="*50)

if __name__ == "__main__":
    main() 