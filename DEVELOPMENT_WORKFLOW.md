# 開発・デプロイフロー

## 標準的な開発サイクル

### 1. **ローカル開発環境でのテスト**

#### 新機能追加の手順

```bash
# 1. ローカル環境でコード修正
# 例: src/analysis/technical_chart.py を編集

# 2. テスト用PDF生成で動作確認
python test_pdf_generation.py 7203

# 3. 出力PDFを確認
# → debug/reports/ フォルダにPDFが生成される
```

#### 主な編集対象ファイル

| ファイル | 用途 |
|---------|------|
| `src/analysis/technical_chart.py` | テクニカルチャートのデザイン変更 |
| `src/analysis/supply_demand.py` | 需給ダッシュボード、スコアリングロジック変更 |
| `src/core/db_manager.py` | データベーススキーマ追加 |
| `src/batch_loader.py` | データ収集ロジック変更 |
| `src/utils/pdf_generator.py` | PDFレイアウト変更 |

---

### 2. **Git管理**

```bash
# 変更をコミット
git add .
git commit -m "Add new feature: XYZ"

# GitHubにpush
git push origin main
```

---

### 3. **OCI Serverへのデプロイ**

#### Option A: rsyncで差分デプロイ（推奨）

```bash
# 変更ファイルのみ同期
rsync -avz -e "ssh -i ssh-key-2025-12-13.key" \
  --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
  --exclude 'data' --exclude 'debug' \
  src/ opc@161.33.166.186:~/stock-bot/src/

# Bot再起動
ssh -i ssh-key-2025-12-13.key opc@161.33.166.186 "sudo systemctl restart stock-bot"
```

#### Option B: 特定ファイルのみ更新

```bash
# 単一ファイルをコピー
scp -i ssh-key-2025-12-13.key \
  src/analysis/supply_demand.py \
  opc@161.33.166.186:~/stock-bot/src/analysis/

# Bot再起動
ssh -i ssh-key-2025-12-13.key opc@161.33.166.186 "sudo systemctl restart stock-bot"
```

---

### 4. **動作確認**

```bash
# サーバーログ確認
ssh -i ssh-key-2025-12-13.key opc@161.33.166.186 "sudo journalctl -u stock-bot -f"

# またはDiscordで実際にテスト
/analyze 7203
```

---

## よくある変更シナリオ

### シナリオ1: スコアリングロジックの調整

**ファイル**: `src/analysis/supply_demand.py`

1. `calculate_score_v2_1()` 関数の重み付けや閾値を変更
2. ローカルでテスト: `python test_pdf_generation.py 7203`
3. PDF確認後、デプロイ
4. `SCORING_METHODOLOGY.md` も更新

### シナリオ2: チャートデザインの変更

**ファイル**: `src/analysis/technical_chart.py`

1. matplotlib のプロット設定を変更
2. ローカルでテスト
3. デプロイ

### シナリオ3: 新しい指標の追加

**必要な変更:**
1. `src/core/db_manager.py` - 新しいテーブル定義
2. `src/batch_loader.py` - データ収集ロジック
3. `src/analysis/supply_demand.py` - 指標計算とスコアリング
4. ローカルDB初期化: `python -m src.core.db_manager`
5. データ取得: `python src/batch_loader.py`
6. テスト→デプロイ

**デプロイ時の追加手順:**
```bash
# サーバー上でDB初期化
ssh -i ssh-key-2025-12-13.key opc@161.33.166.186 \
  "cd ~/stock-bot && python3 -m src.core.db_manager"

# データ再取得（初回のみ）
ssh -i ssh-key-2025-12-13.key opc@161.33.166.186 \
  "cd ~/stock-bot && python3 src/batch_loader.py"
```

---

## デプロイチェックリスト

- [ ] ローカルで `test_pdf_generation.py` テスト成功
- [ ] Git commit & push 完了
- [ ] 変更ファイルをOCIに転送
- [ ] Bot再起動
- [ ] サーバーログ確認（エラーなし）
- [ ] Discord で実際にテスト
- [ ] ドキュメント更新（必要に応じて）

---

## トラブルシューティング

### Bot起動エラー

```bash
# ログ確認
sudo journalctl -u stock-bot -n 50 --no-pager

# Bot再起動
sudo systemctl restart stock-bot

# ステータス確認
sudo systemctl status stock-bot
```

### データベースエラー

```bash
# DB確認
sqlite3 ~/stock-bot/data/stock_data.db
sqlite3> .tables
sqlite3> SELECT COUNT(*) FROM companies;
```

### フォントエラー

```bash
# フォント確認
fc-list | grep -i gothic

# フォント再インストール（必要時）
sudo dnf install -y ipa-gothic-fonts
```

---

## ベストプラクティス

1. **必ずローカルでテスト** - サーバー上でいきなり修正しない
2. **小さな変更を頻繁に** - 大きな変更は分割してテスト
3. **Git管理を徹底** - 全ての変更をコミット
4. **ログを確認** - デプロイ後は必ずログチェック
5. **バックアップ** - 重要な変更前はDBバックアップ

---

## 開発環境のセットアップ（新PC等）

```bash
# リポジトリクローン
git clone https://github.com/ranohiro/stock-analysis-bot.git
cd stock-analysis-bot

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# .env作成
cp .env.example .env
# .envを編集して認証情報を追加

# DB初期化
python -m src.core.db_manager

# データ取得
python src/batch_loader.py

# テスト
python test_pdf_generation.py 7203
```

---

**最終更新**: 2025-12-20
