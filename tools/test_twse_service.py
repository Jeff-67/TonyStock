import asyncio
import pytest
from datetime import datetime
from .twse_service import TwseService

async def test_all_endpoints():
    """測試所有 TWSE API 端點"""
    print("\n開始測試所有 TWSE API 端點...")
    
    # 使用實際的交易日作為測試日期
    test_date = "20240311"  # 請使用最近的交易日
    test_stock_id = "2330"  # 使用台積電作為測試標的
    
    # 測試每個端點
    test_cases = [
        {
            "name": "股票基本資料",
            "func": lambda: TwseService.get_stock_info(test_stock_id),
            "expected_endpoint": "opendata/t187ap03_L"
        },
        {
            "name": "大盤成交資訊",
            "func": lambda: TwseService.get_market_trades(date_str=test_date),
            "expected_endpoint": "exchangeReport/FMTQIK"
        },
        {
            "name": "大盤統計資訊",
            "func": lambda: TwseService.get_market_highlight(date_str=test_date),
            "expected_endpoint": "exchangeReport/MI_INDEX"
        },
        {
            "name": "大盤漲跌證券數",
            "func": lambda: TwseService.get_market_breadth(date_str=test_date),
            "expected_endpoint": "exchangeReport/MI_INDEX20"
        },
        {
            "name": "個股日均值",
            "func": lambda: TwseService.get_stock_day_avg(test_stock_id, date_str=test_date),
            "expected_endpoint": "exchangeReport/STOCK_DAY_AVG"
        },
        {
            "name": "投信交易資料",
            "func": lambda: TwseService.get_fund_trading(test_stock_id, date_str=test_date),
            "expected_endpoint": "fund/T86"
        },
        {
            "name": "投信持股資料",
            "func": lambda: TwseService.get_fund_holdings(test_stock_id, date_str=test_date),
            "expected_endpoint": "fund/MI_QFIIS"
        },
        {
            "name": "融資融券餘額",
            "func": lambda: TwseService.get_margin_transactions(test_stock_id, date_str=test_date),
            "expected_endpoint": "margin/MI_MARGN"
        },
        {
            "name": "券商交易資料",
            "func": lambda: TwseService.get_broker_trades(test_stock_id, date_str=test_date),
            "expected_endpoint": "brokerBS/BRKMU"
        },
        {
            "name": "集保戶股權分散",
            "func": lambda: TwseService.get_tdcc_holdings(test_stock_id, date_str=test_date),
            "expected_endpoint": "tdcc/TDCC_OD_1"
        },
        {
            "name": "鉅額交易資料",
            "func": lambda: TwseService.get_block_trades(test_stock_id, date_str=test_date),
            "expected_endpoint": "block/BFIAUU"
        },
        {
            "name": "所有個股收盤資訊",
            "func": lambda: TwseService.get_stock_day_all(),
            "expected_endpoint": "exchangeReport/STOCK_DAY_ALL"
        },
        {
            "name": "指數收盤行情",
            "func": lambda: TwseService.get_indices(date_str=test_date),
            "expected_endpoint": "exchangeReport/MI_INDEX"
        },
        {
            "name": "權證成交資訊",
            "func": lambda: TwseService.get_warrant_trades(date_str=test_date),
            "expected_endpoint": "exchangeReport/MI_INDEX"
        }
    ]
    
    results = {}
    for test_case in test_cases:
        try:
            print(f"\n測試端點: {test_case['name']}")
            response = await test_case['func']()
            
            success = response.get('success', False)
            message = response.get('message', '')
            data = response.get('data', None)
            
            results[test_case['name']] = {
                "success": success,
                "message": message,
                "has_data": data is not None,
                "expected_endpoint": test_case['expected_endpoint']
            }
            
            # 輸出詳細資訊
            print(f"狀態: {'成功' if success else '失敗'}")
            print(f"訊息: {message}")
            print(f"是否有數據: {'是' if data is not None else '否'}")
            
        except Exception as e:
            print(f"測試 {test_case['name']} 時發生錯誤: {str(e)}")
            results[test_case['name']] = {
                "success": False,
                "message": str(e),
                "has_data": False,
                "expected_endpoint": test_case['expected_endpoint']
            }
    
    return results

if __name__ == "__main__":
    # 執行所有測試
    asyncio.run(test_all_endpoints()) 