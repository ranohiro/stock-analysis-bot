
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
import pandas as pd
from datetime import datetime

# Add project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.db_manager import get_connection
# from src.analysis.company_overview import CompanyOverviewGenerator  # Not used
from src.analysis.technical_chart import generate_charts
from src.analysis.supply_demand import SupplyDemandAnalyzer
from src.utils.pdf_generator import generate_pdf_report

def test_full_report_generation(code='7203'):
    print(f"Testing report generation for {code}...")
    
    conn = get_connection()
    
    try:
        # 1. Get Company Info
        df_comp = pd.read_sql(f"SELECT * FROM companies WHERE code='{code}'", conn)
        if df_comp.empty:
            print("Company not found")
            return False
        name = df_comp.iloc[0]['name']
        industry = df_comp.iloc[0]['industry']
        print(f"Target: {name} ({industry})")

        # 2. Skip AI Overview (Removed)
        # overview_gen = CompanyOverviewGenerator()
        # overview = overview_gen.generate_overview(code, name, industry)
        
        # 3. Generate Technical Chart
        print("Generating Technical Chart...")
        sda = SupplyDemandAnalyzer()
        stock_data = sda.load_stock_data(code)
        
        chart_res = generate_charts(stock_data['prices'], code, stock_data['financial'], stock_data['margin'])
        chart_buffer = chart_res['file']

        # 4. Generate Supply-Demand Dashboard AND Get Metadata
        print("Generating Supply-Demand Dashboard...")
        dash_path = f"debug/temp_dash_{code}.png"
        os.makedirs("debug", exist_ok=True)
        
        # plot_analysis now returns metadata dict
        meta_data = sda.plot_analysis(code, save_path=dash_path)
        
        import io
        with open(dash_path, 'rb') as f:
            dash_buffer = io.BytesIO(f.read())
        os.remove(dash_path)
        
        # 5. Generate PDF
        print("Combining into PDF...")
        pdf_buffer = generate_pdf_report(
            meta_data, # Pass metadata instead of separate args
            chart_buffer, 
            dash_buffer
        )
        
        # Save PDF
        out_dir = "debug/reports"
        os.makedirs(out_dir, exist_ok=True)
        out_path = f"{out_dir}/Report_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        with open(out_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
            
        print(f"✅ Report saved to: {out_path}")
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
    success = test_full_report_generation(code)
    
    # 終了コード
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
