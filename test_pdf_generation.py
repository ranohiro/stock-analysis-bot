#!/usr/bin/env python3
"""
PDF生成テストスクリプト

Usage:
    python test_pdf_generation.py [証券コード]
    
Example:
    python test_pdf_generation.py 7203
"""

import sys
import os
from datetime import datetime
from src.data_loader import fetch_data
from src.chart_generator import generate_charts
from src.analyzer import generate_analysis
from src.pdf_generator import generate_pdf_report

def test_pdf_generation(code: str):
    """
    指定された証券コードのPDFレポートを生成し、ローカルに保存する
    
    Args:
        code: 証券コード（例: '7203'）
    """
    print(f"\n{'='*60}")
    print(f"PDF生成テスト - 証券コード: {code}")
    print(f"{'='*60}\n")
    
    try:
        # --- 1. データ取得 ---
        print("📊 データを取得しています...")
        analysis_data = fetch_data(code)
        
        if analysis_data.get("error"):
            print(f"❌ エラー: {analysis_data['error']}")
            return False
        
        company = analysis_data["company_name"]
        print(f"✅ データ取得成功: {company} ({code})")
        
        # --- 2. チャート生成 ---
        print("\n📈 チャートを生成しています...")
        chart_info = generate_charts(analysis_data['stock_data'], code)
        print("✅ チャート生成完了")
        
        # --- 3. AI分析 ---
        print("\n🧠 AI分析を実行しています...")
        analysis_result = generate_analysis(
            company_name=company,
            code=code,
            summary=analysis_data['company_summary'],
            stock_data=analysis_data['stock_data'],
            financial_data=analysis_data['financial_data'],
            chart_buffer=chart_info['file']
        )
        
        if analysis_result.get("error"):
            print(f"❌ AI分析エラー: {analysis_result['error']}")
            return False
        
        print("✅ AI分析完了")
        
        # --- 4. PDF生成 ---
        print("\n📄 PDFレポートを生成しています...")
        pdf_buffer = generate_pdf_report(
            company_name=company,
            code=code,
            current_price=analysis_data['stock_data']['Close'].iloc[-1],
            summary=analysis_data['company_summary'],
            stock_data=analysis_data['stock_data'],
            financial_data=analysis_data['financial_data'],
            chart_image_buffer=chart_info['file'],
            ai_analysis=analysis_result['report']
        )
        
        # --- 5. ファイル保存 ---
        output_dir = os.path.join(os.path.dirname(__file__), 'debug', 'pdfs')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{code}_{company}_analysis_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF生成完了: {filepath}")
        print(f"\nファイルサイズ: {os.path.getsize(filepath) / 1024:.1f} KB")
        
        # --- 6. プレビューで開く（Mac専用） ---
        print("\n🔍 プレビューで開いています...")
        os.system(f'open "{filepath}"')
        
        print(f"\n{'='*60}")
        print("✅ すべての処理が完了しました！")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    # コマンドライン引数から証券コードを取得
    if len(sys.argv) > 1:
        code = sys.argv[1]
    else:
        # デフォルト: トヨタ自動車
        code = input("証券コードを入力してください (デフォルト: 7203): ").strip() or "7203"
    
    # PDF生成テスト実行
    success = test_pdf_generation(code)
    
    # 終了コード
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
