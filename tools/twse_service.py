import aiohttp
from typing import Dict, Any, Optional, Callable
from datetime import datetime, date
from functools import wraps
import requests
from json import JSONDecodeError
import re


class TwseApiError(Exception):
    """TWSE API 錯誤"""
    pass


class TwseResponseError(TwseApiError):
    """TWSE API 響應錯誤"""
    pass


class TwseValidationError(TwseApiError):
    """TWSE API 參數驗證錯誤"""
    pass


class CustomResponse:
    """自定義響應格式"""

    @staticmethod
    def ok(data: Any) -> Dict[str, Any]:
        """返回成功的響應"""
        return {
            "success": True,
            "message": "Success",
            "data": data
        }

    @staticmethod
    def not_found(message: str) -> Dict[str, Any]:
        """返回未找到資源的響應"""
        return {
            "success": False,
            "message": message,
            "data": None
        }


def with_twse_session(func: Callable) -> Callable:
    """裝飾器：自動處理 TWSE API 的會話管理

    Args:
        func (Callable): 要裝飾的函數

    Returns:
        Callable: 裝飾後的函數
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with aiohttp.ClientSession() as session:
            return await func(*args, session=session, **kwargs)
    return wrapper


class TwseService:
    """台灣證券交易所 API 服務"""

    BASE_URL = "https://openapi.twse.com.tw/v1"
    custom_response = CustomResponse

    ENDPOINTS = {
        'STOCK_INFO': '/opendata/t187ap03_L',
        'MARKET_TRADES': '/exchangeReport/FMTQIK',
        'MARKET_HIGHLIGHT': '/exchangeReport/MI_INDEX',
        'MARKET_BREADTH': '/exchangeReport/MI_INDEX20',
        'STOCK_DAY_AVG': '/exchangeReport/STOCK_DAY_AVG_ALL',
        'FUND_TRADING': '/fund/T86',
        'FUND_HOLDINGS': '/fund/MI_QFIIS',
        'MARGIN_TRANSACTIONS': '/margin/MI_MARGN',
        'TDCC_HOLDINGS': '/tdcc/TDCC_OD_1',
        'BLOCK_TRADES': '/block/BFIAUU',
        'STOCK_DAY_ALL': '/exchangeReport/STOCK_DAY_ALL',
        'INDICES': '/exchangeReport/MI_INDEX',
        'WARRANT_TRADES': '/warrant/WARRANT_ALL',
        'FOREIGN_HOLDINGS': '/fund/MI_QFIIS_cat'
    }

    @staticmethod
    def _validate_stock_id(stock_id: str) -> bool:
        """驗證股票代碼格式"""
        return bool(re.match(r'^\d{4,6}$', stock_id))

    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """驗證日期格式 (YYYYMMDD)"""
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return True
        except ValueError:
            return False

    @staticmethod
    async def _make_request(session: aiohttp.ClientSession, endpoint: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """發送請求到 TWSE API"""
        url = f"{TwseService.BASE_URL}/{endpoint}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)",
            "X-Requested-With": "XMLHttpRequest"
        }
        try:
            print(f"\nRequesting URL: {url}")
            if params:
                print(f"With params: {params}")
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except Exception as e:
                        print(f"Failed to parse JSON from {url}: {str(e)}")
                        return None
                print(f"Request to {url} failed with status {response.status}")
                return None
        except Exception as e:
            print(f"Error accessing {url}: {str(e)}")
            return None

    @staticmethod
    def _format_date(date_str: Optional[str] = None) -> str:
        """格式化日期為 YYYYMMDD 格式"""
        if date_str:
            if not TwseService._validate_date(date_str):
                raise TwseValidationError(f"Invalid date format: {date_str}")
            return date_str
        return datetime.now().strftime("%Y%m%d")

    @staticmethod
    @with_twse_session
    async def get_stock_info(stock_id: str, *, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """獲取股票基本資料"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
        
        endpoint = TwseService.ENDPOINTS['STOCK_INFO']
        params = {"stockNo": stock_id}
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found(f"No data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_market_trades(*, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取大盤成交資訊"""
        endpoint = TwseService.ENDPOINTS['MARKET_TRADES']
        params = {"date": TwseService._format_date(date_str)}
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found("No market trades data available")

    @staticmethod
    @with_twse_session
    async def get_market_highlight(*, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取大盤統計資訊"""
        endpoint = TwseService.ENDPOINTS['MARKET_HIGHLIGHT']
        params = {"date": TwseService._format_date(date_str)}
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found("No market highlight data available")

    @staticmethod
    @with_twse_session
    async def get_market_breadth(*, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取大盤漲跌證券數合計"""
        endpoint = TwseService.ENDPOINTS['MARKET_BREADTH']
        params = {"date": TwseService._format_date(date_str)}
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found("No market breadth data available")

    @staticmethod
    @with_twse_session
    async def get_stock_day_avg(stock_id: str, *, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取個股日均值"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
            
        endpoint = TwseService.ENDPOINTS['STOCK_DAY_AVG']
        params = {"date": TwseService._format_date(date_str)}
        data = await TwseService._make_request(session, endpoint, params)
        if data:
            stock_data = [item for item in data if item.get("stockNo") == stock_id]
            return TwseService.custom_response.ok(stock_data)
        return TwseService.custom_response.not_found(f"No day average data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_fund_trading(stock_id: str, *, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取投信交易資料"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
            
        endpoint = TwseService.ENDPOINTS['FUND_TRADING']
        params = {
            "stockNo": stock_id,
            "date": TwseService._format_date(date_str)
        }
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found(f"No fund trading data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_fund_holdings(stock_id: str, *, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取投信持股資料"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
            
        endpoint = TwseService.ENDPOINTS['FUND_HOLDINGS']
        params = {
            "stockNo": stock_id,
            "date": TwseService._format_date(date_str)
        }
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found(f"No fund holdings data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_foreign_holdings(*, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取外資持股比例資料"""
        endpoint = TwseService.ENDPOINTS['FOREIGN_HOLDINGS']
        params = {"date": TwseService._format_date(date_str)}
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found("No foreign holdings data available")

    @staticmethod
    @with_twse_session
    async def get_margin_transactions(stock_id: str, *, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取個股融資融券餘額"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
            
        endpoint = TwseService.ENDPOINTS['MARGIN_TRANSACTIONS']
        params = {
            "stockNo": stock_id,
            "date": TwseService._format_date(date_str)
        }
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found(f"No margin transactions data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_broker_trades(stock_id: str, *, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取券商交易資料"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
            
        endpoint = TwseService.ENDPOINTS['STOCK_DAY_ALL']
        params = {
            "stockNo": stock_id,
            "date": TwseService._format_date(date_str)
        }
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found(f"No broker trades data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_tdcc_holdings(stock_id: str, *, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取集保戶股權分散資料"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
            
        endpoint = TwseService.ENDPOINTS['TDCC_HOLDINGS']
        params = {
            "stockNo": stock_id,
            "date": TwseService._format_date(date_str)
        }
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found(f"No TDCC holdings data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_block_trades(stock_id: str, *, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取個股鉅額交易資料"""
        if not TwseService._validate_stock_id(stock_id):
            raise TwseValidationError(f"Invalid stock ID: {stock_id}")
            
        endpoint = TwseService.ENDPOINTS['BLOCK_TRADES']
        params = {
            "stockNo": stock_id,
            "date": TwseService._format_date(date_str)
        }
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found(f"No block trades data found for stock {stock_id}")

    @staticmethod
    @with_twse_session
    async def get_stock_day_all(*, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """獲取所有個股收盤資訊"""
        endpoint = TwseService.ENDPOINTS['STOCK_DAY_ALL']
        data = await TwseService._make_request(session, endpoint)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found("No stocks day data available")

    @staticmethod
    @with_twse_session
    async def get_indices(*, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取指數收盤行情"""
        endpoint = TwseService.ENDPOINTS['INDICES']
        params = {"date": TwseService._format_date(date_str)}
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found("No indices data available")

    @staticmethod
    @with_twse_session
    async def get_warrant_trades(*, session: aiohttp.ClientSession, date_str: Optional[str] = None) -> Dict[str, Any]:
        """獲取權證成交資訊"""
        endpoint = TwseService.ENDPOINTS['WARRANT_TRADES']
        params = {"date": TwseService._format_date(date_str)}
        data = await TwseService._make_request(session, endpoint, params)
        return TwseService.custom_response.ok(data) if data else \
               TwseService.custom_response.not_found("No warrant trades data available")

    # 測試用方法
    @staticmethod
    async def test_all_endpoints():
        """測試所有端點是否可以正常訪問"""
        test_stock_id = "2330"  # 以台積電為例
        test_date = "20240211"  # 使用固定的測試日期
        
        endpoints = [
            ("Market Trades", lambda: TwseService.get_market_trades(date_str=test_date)),
            ("Market Highlight", lambda: TwseService.get_market_highlight(date_str=test_date)),
            ("Market Breadth", lambda: TwseService.get_market_breadth(date_str=test_date)),
            ("Stock Info", lambda: TwseService.get_stock_info(test_stock_id)),
            ("Stock Day Avg", lambda: TwseService.get_stock_day_avg(test_stock_id, date_str=test_date)),
            ("Fund Trading", lambda: TwseService.get_fund_trading(test_stock_id, date_str=test_date)),
            ("Fund Holdings", lambda: TwseService.get_fund_holdings(test_stock_id, date_str=test_date)),
            ("Foreign Holdings", lambda: TwseService.get_foreign_holdings(date_str=test_date)),
            ("Margin Transactions", lambda: TwseService.get_margin_transactions(test_stock_id, date_str=test_date)),
            ("Broker Trades", lambda: TwseService.get_broker_trades(test_stock_id, date_str=test_date)),
            ("TDCC Holdings", lambda: TwseService.get_tdcc_holdings(test_stock_id, date_str=test_date)),
            ("Block Trades", lambda: TwseService.get_block_trades(test_stock_id, date_str=test_date)),
            ("Stock Day All", lambda: TwseService.get_stock_day_all()),
            ("Indices", lambda: TwseService.get_indices(date_str=test_date)),
            ("Warrant Trades", lambda: TwseService.get_warrant_trades(date_str=test_date))
        ]
        
        results = {}
        for name, func in endpoints:
            try:
                print(f"\nTesting endpoint: {name}")
                response = await func()
                results[name] = {
                    "success": response['success'],
                    "message": response['message']
                }
            except Exception as e:
                print(f"Error testing {name}: {str(e)}")
                results[name] = {
                    "success": False,
                    "message": str(e)
                }
        
        return results 