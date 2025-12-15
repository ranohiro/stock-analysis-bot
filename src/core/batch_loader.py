import os
import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import io
import time
import jpholiday
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.core.db_manager import get_connection
from typing import Union

# .envファイルを読み込み
load_dotenv()
KABU_PLUS_USER = os.getenv('KABU_PLUS_USER')
KABU_PLUS_PASSWORD = os.getenv('KABU_PLUS_PASSWORD')

# 株・プラスのベースURL
KABU_PLUS_BASE_URL = 'https://csvex.com/kabu.plus/csv/'
TIMEOUT = 30
ENCODING = 'cp932'

# --- 接続設定 ---
def make_session_with_retries():
    """リトライ機能付きのrequestsセッションを作成"""
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({
        "User-Agent": "StockAnalysisBot/1.0"
    })
    return s

def fetch_csv_as_dataframe(url: str, session: requests.Session, skiprows: int = 0):
    """URLからCSVをダウンロードし、Pandas DataFrameとして返す"""
    auth_tuple = (KABU_PLUS_USER, KABU_PLUS_PASSWORD)
    
    try:
        response = session.get(url, auth=auth_tuple, timeout=TIMEOUT)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content), encoding=ENCODING, skiprows=skiprows)
        return df

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"  -> スキップ: {url.split('/')[-1]} (404 Not Found)")
        elif response.status_code == 401:
            print(f"  -> エラー: 401 Unauthorized")
        else:
            print(f"  -> エラー: HTTP {e}")
    except Exception as e:
        print(f"  -> エラー: {e}")
    return None


# --- 1. 日足株価 & 企業マスタ更新 ---
def insert_daily_prices(date_str: str, conn: sqlite3.Connection, session: requests.Session):
    filename = f"japan-all-stock-prices-2_{date_str}.csv"
    url = f"{KABU_PLUS_BASE_URL}japan-all-stock-prices-2/daily/{filename}"
    
    df = fetch_csv_as_dataframe(url, session, skiprows=0)
    if df is None: return

    try:
        # DBに格納するカラム（DB名はcamel_case）とCSVヘッダー名のマッピング
        col_map = {
            'SC': 'code',
            '名称': 'name',       # 企業名を保存
            '市場': 'market',     # 市場区分
            '業種': 'industry',   # 業種
            '日付': 'date',
            '始値': 'open',
            '高値': 'high',
            '安値': 'low',
            '株価': 'close',
            '出来高': 'volume',
            '売買代金（千円）': 'trading_value',
            '時価総額（百万円）': 'market_cap_total'
        }
        
        # 必要なカラムの存在チェック (必須カラムのみ)
        must_have = ['SC', '名称', '日付', '株価']
        missing = [c for c in must_have if c not in df.columns]
        if missing:
            print(f"  -> デバッグ情報：現在のDFカラム: {list(df.columns)}")
            raise KeyError(f"CSVに必須カラムが見つかりません: {missing}")

        # リネーム対象のCSVカラムを抽出（存在するもののみ）
        valid_cols = {csv_name: db_name for csv_name, db_name in col_map.items() if csv_name in df.columns}
        df.rename(columns=valid_cols, inplace=True)
        
        # データ型変換
        df['date'] = date_str 
        df['code'] = df['code'].astype(str)

        # --- A. 企業マスタ (companies) の更新 ---
        # 毎日更新することで、社名変更や新規上場に対応
        companies_df = df[['code', 'name', 'market', 'industry']].copy()
        companies_df.drop_duplicates(subset=['code'], inplace=True)
        
        comp_records = [tuple(x) for x in companies_df.where(pd.notnull(companies_df), None).to_numpy()]
        conn.executemany("""
            INSERT OR REPLACE INTO companies (code, name, market, industry)
            VALUES (?, ?, ?, ?)
        """, comp_records)

        # --- B. 日足株価 (daily_prices) の更新 ---
        # 既存カラムに加え、売買代金と時価総額（全銘柄）を追加
        prices_db_cols = ['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'trading_value', 'market_cap_total']
        prices_df = df[[c for c in prices_db_cols if c in df.columns]].copy()
        
        # DBカラムに不足している場合はNoneを追加
        for col in prices_db_cols:
            if col not in prices_df.columns:
                prices_df[col] = None

        price_records = [tuple(row) for row in prices_df.where(pd.notnull(prices_df), None).itertuples(index=False)]

        conn.executemany(f"""
            INSERT OR REPLACE INTO daily_prices ({', '.join(prices_db_cols)}) 
            VALUES ({', '.join(['?'] * len(prices_db_cols))})
        """, price_records)
        
        print(f"  -> 株価・企業情報: {len(price_records)}件 処理完了")

    except Exception as e:
        print(f"  -> エラー(株価): {e}")


# --- 2. 財務指標 ---
def insert_daily_financials(date_str: str, conn: sqlite3.Connection, session: requests.Session):
    filename = f"japan-all-stock-data_{date_str}.csv"
    url = f"{KABU_PLUS_BASE_URL}japan-all-stock-data/daily/{filename}"
    
    # 財務データも1行目がヘッダーなので skiprows=0
    df = fetch_csv_as_dataframe(url, session, skiprows=0)
    if df is None: return
    
    try:
        col_map = {
            'SC': 'code',
            '時価総額（百万円）': 'market_cap',
            '発行済株式数': 'shares_outstanding',
            '配当利回り（予想）': 'dividend_yield',
            'PER（予想）': 'per_forecast',
            'PBR（実績）': 'pbr_actual',
            'EPS（予想）': 'eps_forecast',
            'BPS（実績）': 'bps_actual',
            '最低投資金額': 'min_investment'
        }
        
        # 必要なカラムの存在チェック (必須カラムのみ)
        must_have = ['SC', 'PER（予想）', 'PBR（実績）']
        missing = [c for c in must_have if c not in df.columns]
        if missing:
            # 時価総額のカラム名が揺れる可能性に対応
            if '時価総額（全銘柄）' in df.columns:
                df.rename(columns={'時価総額（全銘柄）': 'market_cap'}, inplace=True)
                col_map.pop('時価総額（百万円）', None) 
            else:
                raise KeyError(f"CSVに必須カラムが見つかりません: {missing}")
        
        # リネーム
        valid_cols = {csv_name: db_name for csv_name, db_name in col_map.items() if csv_name in df.columns}
        df.rename(columns=valid_cols, inplace=True)
        
        # DB挿入カラムのリスト
        fin_db_cols = ['code', 'date', 'market_cap', 'shares_outstanding', 'per_forecast', 'pbr_actual', 
                    'eps_forecast', 'bps_actual', 'dividend_yield', 'min_investment']

        df['date'] = date_str
        df['code'] = df['code'].astype(str)
        
        # DBカラムに不足している場合はNoneを追加
        for col in fin_db_cols:
            if col not in df.columns:
                df[col] = None
        
        # DB挿入順に並べ替え
        df = df[fin_db_cols]

        records = [tuple(row) for row in df.where(pd.notnull(df), None).itertuples(index=False)]

        conn.executemany(f"""
            INSERT OR REPLACE INTO daily_financials ({', '.join(fin_db_cols)}) 
            VALUES ({', '.join(['?'] * len(fin_db_cols))})
        """, records)
        print(f"  -> 財務指標: {len(records)}件 処理完了")
        
    except Exception as e:
        print(f"  -> エラー(財務): {e}")


# --- 3. 信用残 ---
def insert_weekly_margin(date_str: str, conn: sqlite3.Connection, session: requests.Session):
    # 祝日チェック：週次データが公表される可能性のある市場営業日のみ処理
    download_date = datetime.strptime(date_str, '%Y%m%d').date()
    if jpholiday.is_holiday(download_date): # 祝日チェック
        print(f"  -> スキップ: {date_str} (市場休業日/祝日)")
        return
    
    filename = f"tosho-stock-margin-transactions-2_{date_str}.csv"
    url = f"{KABU_PLUS_BASE_URL}tosho-stock-margin-transactions-2/weekly/{filename}"
    
    df = fetch_csv_as_dataframe(url, session, skiprows=0)
    if df is None: return

    try:
        original_cols = ["SC","公表日","信用取引区分","信用売残","信用売残 前週比","信用買残","信用買残 前週比","貸借倍率", "制度信用売残", "制度信用売残 前週比", "制度信用買残", "制度信用買残 前週比", "一般信用売残", "一般信用売残 前週比", "一般信用買残", "一般信用買残 前週比"]
        
        if len(df.columns) == len(original_cols):
            df.columns = original_cols
        else:
            raise KeyError(f"カラム数不一致: CSV({len(df.columns)}) vs 期待値({len(original_cols)})")

        # --- 日付計算ロジック（祝日対応版）---
        # 1. 公表日（通常火曜など）から、データが指し示す「前週の金曜日」を計算
        current_date = datetime.strptime(date_str, '%Y%m%d').date()
        
        # 土曜・日曜・公表日当日を起点にしないように、まず月曜まで移動
        if current_date.weekday() >= 5: # 土日なら
            days_to_subtract = current_date.weekday() - 4
        else:
            days_to_subtract = current_date.weekday() + 1
            
        data_date = current_date - timedelta(days=days_to_subtract)
        
        # 2. 市場営業日までさかのぼる（祝日・金曜日が休場日対応）
        while data_date.weekday() >= 5 or jpholiday.is_holiday(data_date):
            data_date -= timedelta(days=1)
            
        found_date_str = data_date.strftime('%Y%m%d')
        df['date'] = found_date_str 

        # 欠損値を含む行を削除 (数値データがない行を除くため)
        df.dropna(subset=['信用売残', '信用買残'], inplace=True) 
        
        # DBに格納するカラムとCSVヘッダー名のマッピング
        col_map = {
            'SC': 'code',
            '信用売残': 'sell_balance_total', '信用買残': 'buy_balance_total',
            '貸借倍率': 'ratio', '制度信用売残': 'sell_balance_ins', 
            '制度信用買残': 'buy_balance_ins', '一般信用売残': 'sell_balance_gen', 
            '一般信用買残': 'buy_balance_gen'
        }
        
        valid_cols = {csv_name: db_name for csv_name, db_name in col_map.items() if csv_name in df.columns}
        df.rename(columns=valid_cols, inplace=True)
        
        margin_db_cols = ['code', 'date', 'sell_balance_total', 'buy_balance_total', 'ratio', 
                        'sell_balance_ins', 'buy_balance_ins', 'sell_balance_gen', 'buy_balance_gen']
        
        df['code'] = df['code'].astype(str)
        
        for col in margin_db_cols:
            if col not in df.columns:
                df[col] = None
        
        df = df[margin_db_cols]

        records = [tuple(row) for row in df.where(pd.notnull(df), None).itertuples(index=False)]

        conn.executemany(f"""
            INSERT OR REPLACE INTO weekly_margin ({', '.join(margin_db_cols)}) 
            VALUES ({', '.join(['?'] * len(margin_db_cols))})
        """, records)
        print(f"  -> 信用残: {len(records)}件 処理完了 (データ日付: {found_date_str})")
        
    except Exception as e:
        print(f"  -> エラー(信用残): {e}")
        print(f"  -> デバッグ情報(信用残): DFカラム: {list(df.columns)}") # オプション


# --- 4. 指標データ (東証インデックス、セクター別指数) ---
def insert_daily_indices(date_str: str, conn: sqlite3.Connection, session: requests.Session):
    filename = f"tosho-index-data_{date_str}.csv"
    url = f"{KABU_PLUS_BASE_URL}tosho-index-data/daily/{filename}"

    df = fetch_csv_as_dataframe(url, session, skiprows=0)
    if df is None: return

    try:
        # 🌟 ご提示いただいた正しい日本語ヘッダー名を使用
        original_cols = ["SC","指数名","日付","終値","前日比","前日比（％）","前日終値","時価総額（指数用・浮動株ベース）","時価総額前日比（同左）","前日時価総額（同左）","平均時価総額（同左）","基準時価総額","銘柄数","売買単位換算後株式数"]

        # CSVのヘッダー数が合致するか確認
        if len(df.columns) == len(original_cols):
            df.columns = original_cols
        else:
            # ヘッダーの括弧がない可能性も考慮したチェック
            alt_original_cols = ["SC","指数名","日付","終値","前日比","前日比（％）","前日終値","時価総額（指数用・浮動株ベース）","時価総額前日比","前日時価総額","平均時価総額","基準時価総額","銘柄数","売買単位換算後株式数"]
            if len(df.columns) == len(alt_original_cols):
                df.columns = alt_original_cols
            else:
                raise KeyError(f"カラム数不一致: CSV({len(df.columns)}) vs 期待値({len(original_cols)})")

        # DBに格納するカラムとCSVヘッダー名のマッピング
        col_map = {
            'SC': 'code',
            '指数名': 'name',
            '日付': 'date',
            '終値': 'close',
            '前日比（％）': 'change_ratio',
            '時価総額（指数用・浮動株ベース）': 'market_cap_index',
            '売買単位換算後株式数': 'volume', # DBカラム: volume
            '銘柄数': '銘柄数' # DBカラム: 銘柄数
        }

        # 実際のDataFrameのカラム名とDB名のマッピングを構築
        valid_cols = {}
        for csv_name in df.columns:
            if csv_name in col_map:
                valid_cols[csv_name] = col_map[csv_name]
        
        df.rename(columns=valid_cols, inplace=True)
        
        # 最終的なDB格納カラム (db_managerで定義したカラム名)
        index_db_cols = ['code', 'name', 'date', 'close', 'change_ratio', 'market_cap_index', 'volume', '銘柄数']
        
        df['date'] = date_str
        df['code'] = df['code'].astype(str)

        # 欠損値対応
        for col in index_db_cols:
            if col not in df.columns:
                df[col] = None
        
        # DB挿入順に並べ替え
        df = df[index_db_cols]

        records = [tuple(row) for row in df.where(pd.notnull(df), None).itertuples(index=False)]

        conn.executemany(f"""
            INSERT OR REPLACE INTO daily_indices ({', '.join(index_db_cols)}) 
            VALUES ({', '.join(['?'] * len(index_db_cols))})
        """, records)
        print(f"  -> 業種別指数データ: {len(records)}件 処理完了")
        
    except Exception as e:
        print(f"  -> エラー(業種別指数データ): {e}")

def run_daily_batch(start_date_str: str, end_date_str: str):
    """
    指定期間の日次/週次データをダウンロードし、データベースに格納するバッチ処理を実行
    """
    if not all([KABU_PLUS_USER, KABU_PLUS_PASSWORD]):
        print("❌ エラー: .envファイルにKABU_PLUS_USERまたはKABU_PLUS_PASSWORDが設定されていません。")
        return

    session = make_session_with_retries()
    start_date = datetime.strptime(start_date_str, '%Y%m%d')
    end_date = datetime.strptime(end_date_str, '%Y%m%d')
    
    print(f"=== バッチ処理開始: {start_date_str} ~ {end_date_str} ===")
    
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    
    with get_connection() as conn:
        for date in dates:
            date_str = date.strftime('%Y%m%d')
            
            # 土日はスキップ
            if date.weekday() >= 5: continue
            
            # 祝日もスキップ（無駄なアクセスを防ぐ）
            if jpholiday.is_holiday(date):
                print(f"Skipping: {date_str} (Holiday)")
                continue
                
            print(f"Processing: {date_str}")
            insert_daily_prices(date_str, conn, session)
            insert_daily_financials(date_str, conn, session)
            insert_weekly_margin(date_str, conn, session)
            insert_daily_indices(date_str, conn, session)
            
            time.sleep(1) # サーバー負荷軽減
        
        conn.commit()
        print("\n=== ✅ 全処理完了 ===")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Stock Data Batch Loader')
    parser.add_argument('--days', type=int, default=0, help='Past days to fetch (default: 0 = Today only)')
    args = parser.parse_args()

    # 指定日数分を取得
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    run_daily_batch(start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
