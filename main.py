import os
import sys
import subprocess
from datetime import datetime, timedelta

# プロジェクトルートパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# バッチ処理のインポート
from src.core.batch_loader import run_daily_batch
from src.core.db_manager import initialize_db

def update_data():
    """
    当日分データをチェックし、データベースを更新します。
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === データ更新プロセス開始 ===")
    
    # 起動時は「当日分」のみをチェック（再起動ごとの過剰アクセス防止）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=0)
    
    try:
        # DB初期化（ディレクトリ作成など）
        initialize_db()
        
        # 株・プラスからデータを取得してDB保存
        run_daily_batch(start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
        print("✅ データ更新完了")
    except Exception as e:
        print(f"❌ データ更新エラー: {e}")

def run_bot():
    """
    Discord Botをサブプロセスとして起動します。
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === Discord Bot起動 ===")
    
    bot_path = os.path.join("src", "bot", "discord_bot.py")
    
    if not os.path.exists(bot_path):
        print(f"❌ Critical Error: Botスクリプトが見つかりません ({bot_path})")
        return

    try:
        # 現在の環境変数を取得
        env = os.environ.copy()
        # PYTHONPATHに現在のディレクトリを追加
        current_dir = os.getcwd()
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{current_dir}:{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = current_dir

        # サブプロセスで実行することで、メモリ空間を分離し安定稼働させます
        # sys.executableを使用することで、現在実行中のPythonインタプリタ（venv環境など）を確実に継承します
        subprocess.run([sys.executable, bot_path], check=True, env=env)
    except KeyboardInterrupt:
        print("\n🛑 Botを停止しました。")
    except subprocess.CalledProcessError as e:
        print(f"❌ Botが異常終了しました (Exit Code: {e.returncode})")
    except Exception as e:
        print(f"❌ 予期せぬエラー: {e}")

if __name__ == "__main__":
    # 1. 起動時にデータを最新化
    update_data()
    
    # 2. Botを起動 (常駐)
    run_bot()
