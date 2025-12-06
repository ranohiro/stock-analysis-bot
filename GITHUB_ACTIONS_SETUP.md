# GitHub Actions セットアップ - 実行ガイド

このドキュメントは、GitHub Actionsによる自動データ更新を実際に稼働させるための手順書です。

---

## 📋 前提条件

- [x] GitHubアカウントを持っている
- [x] プロジ​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​ェクトをGitHubリポジトリにプッシュ済み（またはこれから行う）
- [x] 株・プラスのユーザー名とパスワードを把握している
- [x] Gemini APIキーを把握している

---

## ステップ1: 変更をGitHubにプッシュ

### 1-1. 変更ファイルを確認

```bash
cd /Users/hiranotakahiro/Projects/個別株分析
git status
```

### 1-2. 必要なファイルを追加

```bash
# GitHub Actionsワークフロー
git add .github/workflows/daily-data-update.yml

# 修正した依存関係ファイル
git add requirements.txt

# ドキュメント
git add GITHUB_ACTIONS_SETUP.md
git add AUTOMATION_SETUP.md

# その他の新規ファイル（必要に応じて）
git add run_batch_update.sh
```

### 1-3. コミット

```bash
git commit -m "feat: add GitHub Actions automation for daily data updates

- Add GitHub Actions workflow for daily stock data updates
- Remove unused pandas-ta dependency
- Update Python version to 3.11 for compatibility
- Disable launchd in favor of GitHub Actions
- Add comprehensive setup documentation"
```

### 1-4. プッシュ

```bash
git push origin main
```

---

## ステップ2: GitHub Secretsの設定

### 2-1. GitHubリポジトリページを開く

ブラウザで以下にアクセス：
```
https://github.com/<あなたのユーザー名>/stock-analysis-bot
```

### 2-2. Settingsタブに移動

1. リポジトリページ上部の **Settings** タブをクリック
2. 左サイドバーの **Secrets and variables** → **Actions** をクリック

### 2-3. Secretsを追加

**New repository secret** ボタンをクリックし、以下の3つを登録：

#### Secret 1: KABU_PLUS_USER

- **Name**: `KABU_PLUS_USER`
- **Secret**: 株・プラスのユーザー名
- **Save secret** をクリック

#### Secret 2: KABU_PLUS_PASSWORD

- **Name**: `KABU_PLUS_PASSWORD`
- **Secret**: 株・プラスのパスワード
- **Save secret** をクリック

#### Secret 3: GEMINI_API_KEY

- **Name**: `GEMINI_API_KEY`
- **Secret**: Google Gemini APIキー（`.env`ファイルから取得）
- **Save secret** をクリック

### 2-4. 設定完了の確認

**Repository secrets** セクションに以下の3つが表示されていることを確認：

- ✅ `GEMINI_API_KEY`
- ✅ `KABU_PLUS_PASSWORD`
- ✅ `KABU_PLUS_USER`

---

## ステップ3: ワークフローの手動テスト実行

### 3-1. Actionsタブに移動

1. リポジトリページ上部の **Actions** タブをクリック
2. 左サイドバーから **Daily Stock Data Update** を選択

### 3-2. 手動実行

1. 右側の **Run workflow** ボタンをクリック
2. ブランチ（通常は `main`）を選択
3. 緑色の **Run workflow** ボタンをクリック

### 3-3. 実行状況を確認

1. ワークフロー実行が開始されます（黄色のアイコン🟡）
2. クリックして詳細ページに移動
3. 各ステップの実行状況をリアルタイムで確認できます

### 3-4. 期待される結果

すべてのステップが緑色のチェックマーク✅で完了すること：

```
✅ Checkout repository
✅ Set up Python
✅ Install dependencies
✅ Download latest database (初回は失敗OK)
✅ Create database if not exists
✅ Run batch data update
✅ Verify database update
✅ Upload updated database
```

**"Verify database update"** の出力例：
```
=== データベース統計 ===
企業数: 3911
最新データ: 20251206
データ期間: 268日分
```

---

## ステップ4: Artifactの確認

### 4-1. Artifactsセクションを確認

ワークフロー実行ページの下部に **Artifacts** セクションがあります。

### 4-2. データベースをダウンロード（オプション）

1. `stock-database` をクリックしてダウンロード
2. ZIPファイルを解凍
3. `stock_data.db` を確認

---

## ステップ5: 定期実行の確認（翌日）

### 5-1. 待機

翌日の午前2時（日本時間）以降まで待ちます。

### 5-2. Actionsタブで確認

1. GitHubの **Actions** タブを開く
2. 自動実行されたワークフローを確認
3. 実行が成功していることを確認（緑色のチェックマーク✅）

---

## 🎉 完了！

すべてのステップが成功すれば、以下が実現されます：

- ✅ 毎日午前2時に自動的にデータが更新される
- ✅ Macがスリープ状態でも確実に実行される
- ✅ 実行履歴とログがGitHub上で確認できる
- ✅ データベースは90日間保持される

---

## 📊 日常的な使い方

### ローカルで最新データを使う方法

#### 方法1: GitHub Artifactからダウンロード

1. GitHubの **Actions** タブを開く
2. 最新のワークフロー実行をクリック
3. **Artifacts** から `stock-database` をダウンロード
4. 解凍して `data/stock_data.db` に配置

#### 方法2: 手動でバッチを実行

```bash
cd /Users/hiranotakahiro/Projects/個別株分析
./run_batch_update.sh
```

---

## ⚠️ トラブルシューティング

### ワークフローが失敗する

1. **Actions** タブで失敗したワークフローをクリック
2. 赤い❌マークのステップをクリックしてエラーログを確認
3. よくあるエラー：
   - **認証エラー**: Secretsが正しく設定されているか確認
   - **404エラー**: 株・プラスのデータが公開されていない日（休日など）

### データが更新されない

1. ワークフローが実行されているか確認（**Actions** タブ）
2. 実行が成功しているか確認（緑色✅）
3. "Verify database update" のログで最新日付を確認

### メール通知を受け取りたい

1. GitHubアカウントの **Settings** → **Notifications**
2. **Actions** セクションで通知設定を有効化

---

## 🔄 launchdとの比較

| 項目 | launchd | GitHub Actions |
|------|---------|----------------|
| 実行場所 | Mac本体 | GitHubクラウド |
| スリープ時 | ❌ 実行されない | ✅ 実行される |
| 無料枠 | 無制限 | 月2,000分 |
| 現在の状態 | **無効化済み** | **✅ 有効** |

launchdを再度有効化したい場合：

```bash
launchctl load ~/Library/LaunchAgents/com.stockanalysis.batchupdate.plist
```

---

## 📝 次のステップ

GitHub Actionsが正常に動作することを確認したら、次は：

1. **Discord Botの起動** （優先度2）
2. `/analyze 7203` などでテスト実行
3. 最新データを使ったPDFレポート生成を確認

お疲れ様でした！🎉
