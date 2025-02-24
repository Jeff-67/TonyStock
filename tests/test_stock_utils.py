"""Test script for stock utility functions."""

from utils.stock_utils import (
    get_all_stock_mapping,
    retrieve_stock_name,
    stock_id_to_name,
    stock_name_to_id,
)


def main():
    """Run test cases for stock utility functions.

    Tests the following functions:
    - get_all_stock_mapping(): Tests retrieval of stock name to ID mapping
    - stock_name_to_id(): Tests conversion of company names to ticker symbols
    - stock_id_to_name(): Tests conversion of ticker symbols to company names
    - retrieve_stock_name(): Tests extraction of stock names from user messages
    """
    # Test get_all_stock_mapping
    print("\n1. Testing get_all_stock_mapping():")
    mapping = get_all_stock_mapping()
    print(f"Found {len(mapping)} stocks")
    print("Sample entries:", dict(list(mapping.items())[:3]))

    # Test stock_name_to_id
    print("\n2. Testing stock_name_to_id():")
    test_companies = ["台積電", "聯發科", "NonExistentCompany"]
    for company in test_companies:
        result = stock_name_to_id(company)
        print(f"{company} -> {result}")

    # Test stock_id_to_name
    print("\n3. Testing stock_id_to_name():")
    test_ids = ["2330", "2454", "9999"]
    for stock_id in test_ids:
        result = stock_id_to_name(stock_id)
        print(f"{stock_id} -> {result}")

    # Test retrieve_stock_name
    print("\n4. Testing retrieve_stock_name():")
    test_messages = [
        [{"content": "我想要查詢台積電的資訊"}],
        [{"content": "請告訴我聯發科的股價"}],
        [{"content": "這是一個沒有股票名稱的訊息"}],
    ]
    for msg in test_messages:
        result = retrieve_stock_name(msg)
        print(f'Message: {msg[0]["content"]} -> Found stock: {result}')


if __name__ == "__main__":
    main()
