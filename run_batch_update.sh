#!/bin/bash

# Stock Analysis Bot - Data Update Script
# このスクリプトは株価データの定期更新を実行します

# エラーハンドリング
set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# ログディレクトリの作成
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# ログファイル名（日付付き）
LOG_FILE="$LOG_DIR/batch_update_$(date +%Y%m%d_%H%M%S).log"

echo "=== Stock Data Batch Update ===" | tee -a "$LOG_FILE"
echo "開始時刻: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 仮想環境の有効化とバッチ処理の実行
cd "$PROJECT_DIR"
source venv/bin/activate

# PYTHONPATHを設定してバッチ処理を実行
PYTHONPATH="$PROJECT_DIR" python src/batch_loader.py 2>&1 | tee -a "$LOG_FILE"

# 実行結果の確認
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ データ更新が正常に完了しました" | tee -a "$LOG_FILE"
    echo "完了時刻: $(date)" | tee -a "$LOG_FILE"
    
    # データベースの統計情報を取得
    echo "" | tee -a "$LOG_FILE"
    echo "--- データベース統計 ---" | tee -a "$LOG_FILE"
    sqlite3 "$PROJECT_DIR/data/stock_data.db" "SELECT '企業数: ' || COUNT(*) FROM companies;" | tee -a "$LOG_FILE"
    sqlite3 "$PROJECT_DIR/data/stock_data.db" "SELECT '最新データ: ' || MAX(date) FROM daily_prices;" | tee -a "$LOG_FILE"
else
    echo "" | tee -a "$LOG_FILE"
    echo "❌ データ更新でエラーが発生しました" | tee -a "$LOG_FILE"
    echo "完了時刻: $(date)" | tee -a "$LOG_FILE"
    exit 1
fi

# 古いログファイルの削除（30日以上前）
find "$LOG_DIR" -name "batch_update_*.log" -mtime +30 -delete

echo "" | tee -a "$LOG_FILE"
echo "================================" | tee -a "$LOG_FILE"
