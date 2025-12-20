# Japanese Stock Analysis Bot (Discord Integration)

## 📌 プロジェクト概要

**Discord上で動作する、日本株分析の完全自動化システム**

Discordで `/analyze [証券コード]` コマンドを送信すると、対象銘柄の**テクニカルチャート**と**需給分析ダッシュボード**を含む高品質なPDFレポートを自動生成して返信します。

Oracle Cloud Infrastructure (OCI) 上で24/7常時稼働し、東証企業のデータベースが毎日自動更新されます。

---

## 🎯 主要機能

### 1. **Discord Bot によるレポート生成**
- `/analyze 7203` のようなコマンド一つで、数十秒でPDFレポートを生成
- A4横向きレイアウト、2ページ構成

### 2. **Page 1: テクニカルチャート**
- **6ヶ月分のローソク足チャート** (月次背景ストライプ付き)
- **移動平均線**: 5日線・25日線
- **出来高グラフ**
- **ストキャスティクス指標** (%K/%D/Slow％D）
- **価格帯別出来高 (Volume Profile)**: 主要な価格帯を可視化

### 3. **Page 2: 需給分析ダッシュボード**
- **株価・信用倍率の推移グラフ**: 直近6ヶ月の動向
- **パフォーマンス比較**: TOPIX比の相対強度
- **信用取引評価**
- **需給スコア**
- **スコア算出過程**

---

## 🏗️ システムアーキテクチャ

### **デプロイ構成 (Oracle Cloud)**

```
┌─────────────────────────────────────────┐
│  Oracle Cloud Infrastructure (OCI)      │
│  ┌───────────────────────────────────┐  │
│  │  Discord Bot (Systemd Service)    │  │
│  │  - 常時稼働 (24/7)                  │  │
│  │  - /analyze コマンド受付             │  │
│  │  - PDF生成・送信　　　　　　　　　　　　　 │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Data Updater (Cron Job)          │  │
│  │  - 毎日定刻実行 (18:00 JST)      　　 │  │
│  │  - 株・プラスAPIからデータ取得          │  │
│  │  - SQLiteデータベース更新       　　   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  SQLite Database                  │  │
│  │  - 日足株価 (約3,800銘柄）　　　　　　　  │  │
│  │  - 週次信用残 (最新26週分)             │  │
│  │  - 財務指標・業種別指数                │　 │
│  │  - 分析履歴                     　   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### **重要な特徴**
- ✅ **完全自律稼働**: サーバー再起動時も自動復旧（Systemdによる管理）
- ✅ **低コスト運用**: Oracle Cloud Free Tierで運用可能
- ✅ **高速レスポンス**: PDFは数十秒で生成

---

## 📂 ディレクトリ構成

```text
個別株分析/
├── data/                        # SQLite Database
│   └── stock_data.db            # 全銘柄データ (日足・信用残・財務・履歴)
├── src/
│   ├── bot/
│   │   └── discord_bot.py       # Discord Bot メインエントリーポイント
│   ├── core/
│   │   ├── db_manager.py        # DB接続・スキーマ管理
│   │   ├── data_loader.py       # データ読み込みユーティリティ
│   │   └── batch_loader.py      # 日次データ更新スクリプト
│   ├── analysis/
│   │   ├── technical_chart.py   # テクニカルチャート生成
│   │   └── supply_demand.py     # 需給分析ダッシュボード生成
│   └── utils/
│       └── pdf_generator.py     # PDFレイアウト・結合エンジン
├── dataset/
│   └── fonts/                   # 日本語フォント (IPAゴシック)
├── requirements.txt             # Python依存ライブラリ
├── main.py                      # Bot起動スクリプト (データ更新→Bot起動)
└── README.md                    # このファイル
```

---

## 🛠️ 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **言語** | Python 3.9+ |
| **Discord API** | discord.py |
| **データベース** | SQLite3 |
| **データ分析** | Pandas, NumPy |
| **可視化** | Matplotlib, mplfinance |
| **PDF生成** | ReportLab |
| **データソース** | 株・プラス (kabu.plus) |
| **インフラ** | Oracle Cloud (Oracle Linux 9) |
| **プロセス管理** | Systemd (Bot常駐), Cron (データ更新) |

---

## 🔄 データフロー

### **日次データ更新フロー**
```
1. Cron Job (毎日18:00 JST) → batch_loader.py 実行
2. 株・プラスAPIから最新データをダウンロード
   - 日足株価 (全銘柄)
   - 週次信用残
   - 財務指標
   - 業種別指数
3. SQLiteデータベースに保存 (INSERT OR REPLACE)
```

### **レポート生成フロー**
```
1. ユーザー: Discord で `/analyze 7203` 入力
2. Bot: リクエスト受信
3. データ取得: SQLiteから対象銘柄の過去6ヶ月データを読み込み
4. 画像生成:
   - technical_chart.py → テクニカルチャート (PNG)
   - supply_demand.py → 需給ダッシュボード (PNG)
5. PDF生成:
   - pdf_generator.py が2つの画像を結合
   - ヘッダー・フッター追加
6. Bot: Discord にPDFファイルをアップロード
```

---

## 📊 データベーススキーマ

### `companies` - 銘柄マスタ
| カラム | 型 | 説明 |
|--------|-------|------|
| code | TEXT | 証券コード (Primary Key) |
| name | TEXT | 銘柄名 |
| market | TEXT | 市場区分 |
| industry | TEXT | 業種 |

### `daily_prices` - 日足株価
| カラム | 型 | 説明 |
|--------|-------|------|
| code | TEXT | 証券コード |
| date | TEXT | 日付 (YYYYMMDD) |
| open / high / low / close | REAL | 四本値 |
| volume | REAL | 出来高 |
| trading_value | REAL | 売買代金 |

### `weekly_margin` - 週次信用残
| カラム | 型 | 説明 |
|--------|-------|------|
| code | TEXT | 証券コード |
| date | TEXT | データ日付 (金曜日) |
| sell_balance_total | REAL | 信用売残 (総計) |
| buy_balance_total | REAL | 信用買残 (総計) |
| ratio | REAL | 信用倍率 (買残/売残) |

### `analysis_history` - 分析履歴
| カラム | 型 | 説明 |
|--------|-------|------|
| id | INTEGER | 自動採番ID (Primary Key) |
| stock_code | TEXT | 証券コード |
| company_name | TEXT | 会社名 |
| analyzed_at | TEXT | 分析日時 (ISO8601) |
| user_name | TEXT | Discordユーザー名 |
| success | INTEGER | 成功フラグ (1=成功, 0=失敗) |

---

## ⚙️ 環境変数 (`.env`)

```bash
# Discord Bot Token
DISCORD_BOT_TOKEN=your_discord_bot_token

# 株・プラス認証情報
KABU_PLUS_USER=your_username
KABU_PLUS_PASSWORD=your_password
```

---

## 📝 使用方法

### Discord上での操作

```
/analyze 7203
```
→ トヨタ自動車のPDFレポートが生成され、チャットに送信されます。

---

## 🔧 ローカル開発

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/ranohiro/stock-analysis-bot.git
cd stock-analysis-bot

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定 (.env ファイルを作成)
# .env を編集して認証情報を追加

# データベース初期化
python -m src.core.db_manager

# データ取得 (直近180日分)
python src/batch_loader.py

# Bot起動
python main.py
```

### テスト用PDF生成

```bash
python test_pdf_generation.py 7203
```
→ `debug/reports/` フォルダにPDFが生成されます。

---

## 🚀 デプロイ (Oracle Cloud)

### 前提条件
- Oracle Cloud アカウント (Free Tier可)
- SSH接続設定済み
- Python 3.9+ インストール済み

### デプロイ手順

1. **プロジェクトファイルをアップロード**
   ```bash
   rsync -avz --exclude 'venv' --exclude '__pycache__' \
     -e "ssh -i ssh-key.key" \
     . opc@<server-ip>:~/stock-bot/
   ```

2. **サーバー上でセットアップ**
   ```bash
   ssh -i ssh-key.key opc@<server-ip>
   cd ~/stock-bot
   
   # 依存関係インストール
   pip3 install --user -r requirements.txt
   
   # フォントインストール
   sudo dnf install -y ipa-gothic-fonts
   
   # .env作成
   nano .env  # 認証情報を入力
   
   # DB初期化
   python3 -m src.core.db_manager
   
   # データ取得
   python3 src/batch_loader.py
   ```

3. **Systemdサービス登録**
   ```bash
   sudo nano /etc/systemd/system/stock-bot.service
   ```
   
   ```ini
   [Unit]
   Description=Stock Analysis Discord Bot
   After=network.target

   [Service]
   Type=simple
   User=opc
   WorkingDirectory=/home/opc/stock-bot
   ExecStart=/usr/bin/python3 main.py
   Restart=always
   RestartSec=10
   Environment="LANG=ja_JP.UTF-8"

   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable stock-bot
   sudo systemctl start stock-bot
   sudo systemctl status stock-bot
   ```

4. **Cronでデータ自動更新**
   ```bash
   crontab -e
   ```
   
   ```cron
   # 毎日18:00に実行
   0 9 * * * cd ~/stock-bot && /usr/bin/python3 src/batch_loader.py >> ~/cron.log 2>&1
   ```

---

## 📋 運用・メンテナンス

### ログ確認
```bash
# Bot稼働ログ
sudo journalctl -u stock-bot -f

# Cron実行ログ
tail -f ~/cron.log
```

### Bot再起動
```bash
sudo systemctl restart stock-bot
```

### データベース確認
```bash
sqlite3 ~/stock-bot/data/stock_data.db
```

---

## 📄 ライセンス



---

## 👤 作者

開発: [@ranohiro](https://github.com/ranohiro)

---

## レファレンス

- データ提供: [株・プラス (kabu.plus)](https://csvex.com/)
- フレームワーク: discord.py, mplfinance, ReportLab
