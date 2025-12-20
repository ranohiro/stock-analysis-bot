import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'stock_data.db')

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
    
    # 7. 分析履歴 (analysis_history):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            company_name TEXT,
            analyzed_at TEXT NOT NULL,
            user_name TEXT,
            success INTEGER DEFAULT 1
        );
    """)
    conn.commit()
    print("✅ Tables created/verified successfully.")

def log_analysis_history(code: str, company_name: str = None, user_name: str = None, success: bool = True):
    """
    分析履歴を記録する
    
    Args:
        code: 証券コード
        company_name: 会社名（オプション）
        user_name: Discordユーザー名（オプション）
        success: 成功フラグ（デフォルト: True）
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analysis_history (stock_code, company_name, analyzed_at, user_name, success)
            VALUES (?, ?, ?, ?, ?)
        """, (code, company_name, datetime.now().isoformat(), user_name, 1 if success else 0))
        conn.commit()

def get_analysis_history(limit: int = 10):
    """
    分析履歴を取得する
    
    Args:
        limit: 取得件数（デフォルト: 10件）
        
    Returns:
        履歴のリスト [(id, stock_code, company_name, analyzed_at, user_name, success), ...]
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, stock_code, company_name, analyzed_at, user_name, success
            FROM analysis_history
            ORDER BY analyzed_at DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

def initialize_db():
    """データベースファイルを初期化し、テーブルを作成する"""
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
    
    with get_connection() as conn:
        create_tables(conn)
    print(f"✅ Database initialized at: {DB_PATH}")

def get_company_info(code: str) -> dict:
    """
    企業情報を取得する
    
    Args:
        code: 証券コード
        
    Returns:
        企業情報の辞書 (code, name, market, industry)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, name, market, industry
            FROM companies
            WHERE code = ?
        """, (code,))
        
        result = cursor.fetchone()
        if result:
            return {
                'code': result[0],
                'name': result[1],
                'market': result[2],
                'industry': result[3]
            }
        return None

def get_stock_prices(code: str, start_date: str = None, end_date: str = None, limit: int = None):
    """
    株価データを取得する
    
    Args:
        code: 証券コード
        start_date: 開始日 (YYYYMMDD形式)
        end_date: 終了日 (YYYYMMDD形式)
        limit: 取得件数の上限
        
    Returns:
        pandas.DataFrame: 株価データ (Date, Open, High, Low, Close, Volume)
    """
    import pandas as pd
    
    with get_connection() as conn:
        query = """
            SELECT date, open, high, low, close, volume
            FROM daily_prices
            WHERE code = ?
        """
        params = [code]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            # 日付をDatetimeに変換してインデックスに設定
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.rename(columns={
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            df = df.set_index('Date').sort_index()
        
        return df

def get_financial_data(code: str, limit: int = 5):
    """
    財務データを取得する（最新のN件）
    
    Args:
        code: 証券コード
        limit: 取得件数
        
    Returns:
        pandas.DataFrame: 財務データ
    """
    import pandas as pd
    
    with get_connection() as conn:
        query = """
            SELECT date, per_forecast, pbr_actual, eps_forecast, 
                   bps_actual, dividend_yield, market_cap
            FROM daily_financials
            WHERE code = ?
            ORDER BY date DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[code, limit])
        
        if not df.empty:
            # 日付をDatetimeに変換
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            # 最新順から古い順に並べ替え
            df = df.sort_values('date')
            df = df.rename(columns={
                'date': 'Date',
                'per_forecast': 'PER',
                'pbr_actual': 'PBR',
                'eps_forecast': 'EPS',
                'bps_actual': 'BPS',
                'dividend_yield': 'Dividend_Yield',
                'market_cap': 'Market_Cap'
            })
        
        return df
    
def get_margin_balance(code: str, limit: int = 26):
    """
    信用残データを取得する（最新のN件）
    デフォルトは半年分（約26週）
    
    Args:
        code: 証券コード
        limit: 取得件数
        
    Returns:
        pandas.DataFrame: 信用残データ
    """
    import pandas as pd
    
    with get_connection() as conn:
        # sell_balance_ins: 制度信用売残（機関の空売りを含むことが多い）
        query = """
            SELECT date, sell_balance_total, buy_balance_total, ratio,
                   sell_balance_ins, buy_balance_ins
            FROM weekly_margin
            WHERE code = ?
            ORDER BY date DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[code, limit])
        
        if not df.empty:
            # 日付をDatetimeに変換
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            # 最新順から古い順に並べ替え
            df = df.sort_values('date')
            df = df.rename(columns={
                'date': 'Date',
                'sell_balance_total': 'Sell_Balance',
                'buy_balance_total': 'Buy_Balance',
                'ratio': 'Ratio',
                'sell_balance_ins': 'Sell_Balance_Ins',  # 制度信用売残
                'buy_balance_ins': 'Buy_Balance_Ins'     # 制度信用買残
            })
            # インデックス設定
            df = df.set_index('Date')
        
        return df
    
    
def get_market_advance_decline(limit: int = 30, market_filter: str = None):
    """
    市場全体の騰落数を集計する（前日比ベース）
    
    Args:
        limit: 取得日数
        market_filter: '東証PR' など、companies.market に対するフィルタ
        
    Returns:
        pandas.DataFrame: columns=[date, up_count, down_count]
    """
    import pandas as pd
    
    with get_connection() as conn:
        # 1. Determine target codes first (if filter exists)
        market_condition = ""
        params = []
        if market_filter:
            market_condition = "AND code IN (SELECT code FROM companies WHERE market LIKE ?)"
            params.append(f"%{market_filter}%")
            
        # 2. Use Window Function to get Close - PrevClose
        # We fetch enough history (limit + 5 days buffer) to ensure diff is possible
        # Actually simplest is to fetch slightly more dates then limit results.
        
        query = f"""
            WITH PriceChanges AS (
                SELECT date,
                       close - LAG(close) OVER (PARTITION BY code ORDER BY date) as change
                FROM daily_prices
                WHERE 1=1 {market_condition}
            ),
            DailyCounts AS (
                SELECT date,
                       SUM(CASE WHEN change > 0 THEN 1 ELSE 0 END) as up_count,
                       SUM(CASE WHEN change < 0 THEN 1 ELSE 0 END) as down_count
                FROM PriceChanges
                WHERE change IS NOT NULL
                GROUP BY date
            )
            SELECT date, up_count, down_count
            FROM DailyCounts
            ORDER BY date DESC
            LIMIT ?
        """
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.sort_values('date')
            df = df.set_index('date')
        return df


if __name__ == "__main__":
    initialize_db()
