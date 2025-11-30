import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'stock_data.db')

def get_connection():
    """SQLite接続オブジェクトを返す"""
    return sqlite3.connect(DB_PATH)

def create_tables(conn: sqlite3.Connection):
    """データベーステーブルを定義し、作成する"""
    cursor = conn.cursor()

    # 1. 銘柄マスタ (companies):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            code TEXT PRIMARY KEY,
            name TEXT,
            market TEXT,
            industry TEXT
        );
    """)

    # 2. 日足株価 (daily_prices):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            code TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            trading_value REAL,
            market_cap_total REAL,
            PRIMARY KEY (code, date)
        );
    """)

    # 3. 日足財務指標 (daily_financials): 拡張カラムを追加
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_financials (
            code TEXT,
            date TEXT,
            market_cap REAL,
            shares_outstanding REAL,
            per_forecast REAL,
            pbr_actual REAL,
            eps_forecast REAL,
            bps_actual REAL,
            dividend_yield REAL,
            min_investment REAL,
            PRIMARY KEY (code, date)
        );
    """)

    # 4. 週次信用残 (weekly_margin):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_margin (
            code TEXT,
            date TEXT,
            sell_balance_total REAL,
            buy_balance_total REAL,
            ratio REAL,
            sell_balance_ins REAL,   -- 制度信用
            buy_balance_ins REAL,    -- 制度信用
            sell_balance_gen REAL,   -- 一般信用
            buy_balance_gen REAL,    -- 一般信用
            PRIMARY KEY (code, date)
        );
    """)

    #　5. 指標データ (sector・index):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_indices (
            code TEXT NOT NULL,
            name TEXT,
            date TEXT NOT NULL,
            close REAL,                 -- 終値
            change_ratio REAL,          -- 前日比（％）
            market_cap_index REAL,      -- 時価総額（指数用・浮動株ベース）
            volume REAL,                -- 売買単位換算後株式数 (指標の出来高に相当)
            銘柄数 INTEGER,             -- 銘柄数
            PRIMARY KEY (code, date)
        )
    """)
    conn.commit()
    print("✅ Tables created/verified successfully.")

def initialize_db():
    """データベースファイルを初期化し、テーブルを作成する"""
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
    
    with get_connection() as conn:
        create_tables(conn)
    print(f"✅ Database initialized at: {DB_PATH}")

if __name__ == '__main__':
    initialize_db()

