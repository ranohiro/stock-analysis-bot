import sqlite3
import pandas as pd
import os
import sys

# srcモジュールをインポートできるようにパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.db_manager import get_connection

def check_db():
    conn = get_connection()
    print("=== データベース格納状況の確認 ===")

    # 1. 日足株価 (daily_prices)
    print("\n[1] 日足株価 (daily_prices) - 企業名をJOINして直近5件表示")
    try:
        df_prices = pd.read_sql_query("""
            SELECT 
                dp.code, 
                c.name,  
                dp.date, 
                dp.close, 
                dp.volume,
                dp.trading_value
            FROM daily_prices dp
            JOIN companies c ON dp.code = c.code 
            ORDER BY dp.date DESC, dp.code ASC
            LIMIT 5;
        """, conn)
        print(df_prices.to_string(index=False))
    except Exception as e:
        print(f"  -> エラー（日足株価）: {e}")
        
    # 2. 財務指標 (daily_financials)
    print("\n[2] 財務指標 (daily_financials) - 直近5件")
    try:
        df_financials = pd.read_sql_query("""
            SELECT 
                code, date, market_cap, per_forecast, pbr_actual, dividend_yield
            FROM daily_financials
            ORDER BY date DESC, code ASC
            LIMIT 5;
        """, conn)
        print(df_financials.to_string(index=False))
    except Exception as e:
        print(f"  -> エラー（財務指標）: {e}")
        
    # 3. 信用残 (weekly_margin)
    print("\n[3] 信用残 (weekly_margin) - 直近5件 (日付ズレ確認)")
    try:
        df_margin = pd.read_sql_query("""
            SELECT 
                code, date, sell_balance_total, buy_balance_total, ratio
            FROM weekly_margin
            ORDER BY date DESC, code ASC
            LIMIT 5;
        """, conn)
        print(df_margin.to_string(index=False))
    except Exception as e:
        print(f"  -> エラー（信用残）: {e}")

    # 4. 業種別指数データ (daily_indices) - ★新規追加★
    print("\n[4] 業種別指数データ (daily_indices) - 直近5件")
    try:
        df_indices = pd.read_sql_query("""
            SELECT 
                code, name, date, close, change_ratio, market_cap_index
            FROM daily_indices
            ORDER BY date DESC, code ASC
            LIMIT 5;
        """, conn)
        print(df_indices.to_string(index=False))
    except Exception as e:
        print(f"  -> エラー（業種別指数）: {e}")

    # 5. データ件数概算
    print("\n[5] データ件数概算")
    tables = {
        "日足株価": "daily_prices",
        "財務指標": "daily_financials",
        "企業マスタ": "companies",
        "信用残": "weekly_margin",
        "業種別指数": "daily_indices"
    }
    for name, table in tables.items():
        try:
            count = pd.read_sql_query(f"SELECT COUNT(*) FROM {table}", conn).iloc[0, 0]
            print(f"  - {name}: {count} レコード")
        except Exception:
            print(f"  - {name}: テーブルが存在しないかエラー")
    
    conn.close()

if __name__ == '__main__':
    check_db()