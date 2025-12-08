import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.core.db_manager import get_company_info, get_stock_prices, get_financial_data, get_margin_balance

# .envから株・プラスの認証情報を取得
load_dotenv()
KABU_PLUS_USER = os.getenv('KABU_PLUS_USER')
KABU_PLUS_PASSWORD = os.getenv('KABU_PLUS_PASSWORD')

def fetch_data(code: str) -> dict:
    """
    指定された証券コードに基づき、株価、財務、需給データを取得する。
    
    Args:
        code: 証券コード (例: '7203')
        
    Returns:
        取得したデータを含む辞書
    """
    
    if not KABU_PLUS_USER or not KABU_PLUS_PASSWORD:
        return {"error": "株plusの認証情報が設定されていません。"}
        
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 証券コード {code} のデータ取得を開始します。")

    # --- 1. 企業情報を取得 ---
    company_info = get_company_info(code)
    
    if not company_info:
        return {"error": f"証券コード {code} は見つかりませんでした。データベースを確認してください。"}
    
    # --- 2. 株価データを取得（直近1年分） ---
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    stock_data = get_stock_prices(
        code=code,
        start_date=start_date.strftime('%Y%m%d'),
        end_date=end_date.strftime('%Y%m%d')
    )
    
    if stock_data.empty:
        return {"error": f"証券コード {code} の株価データが見つかりませんでした。"}
    
    # --- 3. 財務データを取得（過去1年分） ---
    financial_data = get_financial_data(code=code, limit=252)
    
    if financial_data.empty:
        print(f"[警告] 証券コード {code} の財務データが見つかりませんでした。")
        # 財務データが無くても続行（株価データはある）
        financial_data = pd.DataFrame()
        
    # --- 4. 信用残データを取得（過去1年分=約52週） ---
    margin_data = get_margin_balance(code=code, limit=52)
    
    # --- 5. 企業概要（簡易版） ---
    company_summary = f"{company_info['name']}は{company_info['industry']}業界に属する企業です。"
    
    return {
        "stock_data": stock_data,
        "financial_data": financial_data,
        "margin_data": margin_data,
        "company_name": company_info['name'],
        "company_summary": company_summary,
        "error": None
    }

# データ取得のテスト用関数（直接実行時）
if __name__ == '__main__':
    # .envを読み込まないと認証情報がないため、ここでは読み込みを省略
    data = fetch_data('7203')
    if not data.get("error"):
        print("\n--- 株価データ (一部) ---")
        print(data['stock_data'].tail())
        print("\n--- 財務データ ---")
        print(data['financial_data'])
        print(f"\n--- 企業名 ---")
        print(data['company_name'])
    else:
        print(data['error'])
