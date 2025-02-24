"""Module for storing and managing TSE (Taiwan Stock Exchange) stock tickers in the database.

This module provides functionality to create the necessary database table and store
stock ticker information including company names and their corresponding ticker symbols.
"""

import csv
import os
from typing import Dict, List

from database.utils import db_manager


def create_table() -> bool:
    """Create TSE_STOCKS table if it doesn't exist."""
    conn = db_manager._init_mysql_connection()
    if not conn:
        print("Failed to connect to MySQL database.")
        return False

    try:
        with conn.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS TSE_STOCKS (
                ticker VARCHAR(10) PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(sql)
            conn.commit()
            print("TSE_STOCKS table created/verified successfully.")
            return True
    except Exception as e:
        print(f"Error creating table: {e}")
        return False
    finally:
        conn.close()


def read_tse_tickers() -> List[Dict[str, str]]:
    """Read TSE tickers from the CSV file."""
    tickers = []
    csv_path = os.path.join("static", "TSE_ticker.csv")

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:  # Ensure we have both ticker and company name
                tickers.append({"ticker": row[0], "company_name": row[1]})
    return tickers


def store_tickers_to_mysql():
    """Store TSE tickers in MySQL database."""
    # First create table if it doesn't exist
    if not create_table():
        print("Failed to create/verify table structure.")
        return

    # Read tickers from CSV
    tickers = read_tse_tickers()

    if not tickers:
        print("No tickers found in the CSV file.")
        return

    # Store in MySQL
    if db_manager.insert_data(
        db_type="mysql", data=tickers, table="TSE_STOCKS", key="ticker"
    ):
        print(f"Successfully stored {len(tickers)} tickers in MySQL database.")
    else:
        print("Failed to store tickers in MySQL database.")


if __name__ == "__main__":
    store_tickers_to_mysql()
