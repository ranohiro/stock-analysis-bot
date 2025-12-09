#!/bin/bash
# スクリプトのあるディレクトリの親ディレクトリ（プロジェクトルート）に移動
cd "$(dirname "$0")/.."

# 環境変数の読み込み確認 (.envファイル)
if [ ! -f .env ]; then
    echo "エラー: .envファイルが見つかりません。"
    exit 1
fi

echo "=== ローカルデータ更新を開始します ==="
export PYTHONPATH=$(pwd)
python3 src/core/batch_loader.py
echo "=== 更新完了 ==="
