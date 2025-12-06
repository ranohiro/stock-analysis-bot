# GitHub Actions による自動データ更新セットアップガイド

## 🎯 概要

GitHub Actionsを使用することで、**Macがスリープ状態でも確実にデータを更新**できます。

### メリット

- ✅ Macのスリープ状態に関係なく動作
- ✅ クラウド環境で確実に実行
- ✅ 実行履歴とログの確認が容易
- ✅ 無料枠で十分に対応可能（月2,000分）
- ✅ 手動実行も可能

---

## 📋 セットアップ手順

### ステップ1: Git LFSのインストール

データベースファイル（185MB）を効率的に管理するため、Git LFSを使用します。

```bash
# Homebrewでインストール（macOS）
brew install git-lfs

# Git LFSを有効化
git lfs install
```

### ステップ2: リポジトリにGit LFSを設定

```bash
cd /Users/hiranotakahiro/Projects/個別株分析

# 既存のデータベースをGit LFSで追跡
git lfs track "*.db"
git lfs track "*.sqlite"

# .gitattributesをコミット
git add .gitattributes
git commit -m "chore: configure Git LFS for database files"
```

### ステップ3: データベースをリポジトリに追加

```bash
# データベースファイルを追加
git add data/stock_data.db

# コミット
git commit -m "chore: add initial stock database"

# プッシュ（初回は時間がかかる場合があります）
git push origin main
```

### ステップ4: GitHubにSecretsを設定

GitHub Actionsで認証情報を安全に使用するため、Secretsを設定します。

1. GitHubリポジトリのページを開く
2. **Settings** → **Secrets and variables** → **Actions** をクリック
3. **New repository secret** をクリックし、以下を追加：

| Secret名 | 値 |
|----------|-----|
| `KABU_PLUS_USER` | 株・プラスのユーザー名 |
| `KABU_PLUS_PASSWORD` | 株・プラスのパスワード |
| `GEMINI_API_KEY` | Google Gemini APIキー |

### ステップ5: GitHub Actionsワークフローをプッシュ

```bash
# ワークフローファイルを追加
git add .github/workflows/daily-data-update.yml

# コミット
git commit -m "feat: add GitHub Actions workflow for daily data updates"

# プッシュ
git push origin main
```

---

## 🧪 動作確認

### 手動でワークフローを実行

1. GitHubリポジトリの **Actions** タブを開く
2. 左側のワークフロー一覧から **Daily Stock Data Update** を選択
3. **Run workflow** ボタンをクリック
4. ブランチを選択して **Run workflow** を実行

### 実行ログの確認

1. Actions タブでワークフロー実行をクリック
2. 各ステップのログを確認
3. "Verify database update" ステップでデータベース統計を確認

---

## 📊 実行スケジュール

- **実行時刻**: 毎日午前2時（日本時間）
  - GitHub ActionsはUTCで動作するため、17:00 UTC = 翌日2:00 JST
- **実行内容**: 直近30日分のデータを取得・更新
- **データ保存**:
  - GitHub Artifactsに90日間保持
  - Git LFSでリポジトリにコミット

---

## 🔄 データベースの取得方法

GitHub Actionsで更新されたデータベースをローカルに取得する方法：

### 方法1: Gitからプル（推奨）

```bash
cd /Users/hiranotakahiro/Projects/個別株分析
git pull origin main
```

Git LFSが有効化されていれば、データベースも自動的にダウンロードされます。

### 方法2: GitHub Artifactsからダウンロード

1. GitHubリポジトリの **Actions** タブを開く
2. 最新のワークフロー実行をクリック
3. **Artifacts** セクションから `stock-database` をダウンロード
4. ZIPを解凍して `data/` ディレクトリに配置

---

## 🆚 launchdとの比較

| 項目 | launchd（ローカル） | GitHub Actions |
|------|-------------------|----------------|
| 実行場所 | Mac本体 | GitHub クラウド |
| スリープ時 | ❌ 実行されない | ✅ 実行される |
| 実行確認 | ログファイル確認が必要 | Web UIで簡単に確認 |
| 無料枠 | 制限なし | 月2,000分（十分） |
| セットアップ | ローカル設定のみ | GitHubリポジトリが必要 |

### 推奨構成

**両方を併用する**ことで、最も確実な運用が可能です：

- **平日**: GitHub Actionsで確実に実行
- **バックアップ**: launchdがローカルでも実行（Macが起動している場合）

重複実行を避けるため、launchdを無効化することも可能：

```bash
launchctl unload ~/Library/LaunchAgents/com.stockanalysis.batchupdate.plist
```

---

## ⚠️ 注意事項

### Git LFSの制限

- **無料枠**: 1GB ストレージ、1GB/月 帯域幅
- **現在の使用量**: データベース約185MB
- **6ヶ月後の想定**: 約1GB（問題なし）

### GitHub Actionsの実行時間

- **無料枠**: 月2,000分（パブリックリポジトリは無制限）
- **1回の実行時間**: 約5〜10分
- **月間実行回数**: 30回（毎日1回）
- **月間使用時間**: 150〜300分（余裕あり）

### プライベートリポジトリの場合

認証情報を含むため、リポジトリは**プライベート**にすることを推奨します。

---

## 🔧 トラブルシューティング

### データベースのマージ競合

複数の場所（ローカル、GitHub Actions）でデータベースを更新すると競合が発生する可能性があります。

**解決策**:

```bash
# GitHub Actionsの更新を優先する場合
git fetch origin main
git reset --hard origin/main
git lfs pull
```

### ワークフローが失敗する

1. Actions タブでエラーログを確認
2. Secretsが正しく設定されているか確認
3. 株・プラスの認証情報が有効か確認

---

## 📈 今後の拡張案

1. **Discord通知**: ワークフロー完了時にDiscordへ通知
2. **エラー通知**: 失敗時のみアラート送信
3. **週次レポート**: 毎週末に統計レポートを生成
4. **複数地域**: 異なる時間帯で実行して冗長性を確保

---

## ✅ セットアップチェックリスト

- [ ] Git LFSのインストール
- [ ] `.gitattributes`の設定
- [ ] データベースのGit LFS追跡
- [ ] GitHubにSecretsを設定
- [ ] ワークフローファイルのプッシュ
- [ ] 手動実行でテスト
- [ ] 定期実行の確認（翌日）

---

## 🎉 完了後の確認

セットアップ完了後、翌日の午前2時以降に以下を確認してください：

1. **GitHub Actions**: 実行が成功しているか
2. **データベース**: 最新データが更新されているか
3. **Artifacts**: データベースがアップロードされているか

すべて正常であれば、Macがスリープ状態でも毎日自動的にデータ更新が行われます！
