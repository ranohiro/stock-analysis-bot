# Japanese Stock Analysis Bot (Discord Integration)

## 📌 プロジェクト概要

**Discord上で動作する、日本株分析の完全自動化システム**

ユーザーがDiscordで `/analyze [証券コード]` コマンドを送信すると、対象銘柄の**テクニカルチャート**、**需給分析ダッシュボード**、**AI企業概要**を含む高品質なPDFレポートを自動生成して返信します。

Oracle Cloud Infrastructure (OCI) 上で常時稼働し、データベースは毎日自動更新されます。

---

## 🎯 主要機能

### 1. **Discord Bot による即座のレポート生成**
- `/analyze 7203` のようなコマンド一つで、数秒でPDFレポートを生成
- A4横向きレイアウト、2ページ構成
- ダークテーマの美しいデザイン

### 2. **Page 1: テクニカルチャート**
- **6ヶ月分のローソク足チャート** (月次背景ストライプ付き)
- **移動平均線**: 5日線・25日線
- **出来高グラフ** (動的スケーリング表示)
- **ストキャスティクス指標** (%K/%D)
- **価格帯別出来高 (Volume Profile)**: 主要な価格帯を視覚化

### 3. **Page 2: 需給分析ダッシュボード**
- **株価・信用倍率の推移グラフ**: 直近6ヶ月の動向
- **パフォーマンス比較**: TOPIX比の相対強度
- **信用取引評価**: 主要指標（信用倍率、売残/買残、機関投資家動向等）
- **需給スコア**: 複合的な評価指標（A/B/C/D/Eランク）
- **スコア算出過程**: 各項目の詳細な内訳表示

### 4. **AI企業概要生成 (将来実装予定)**
- Google Gemini APIを活用した企業サマリー
- ビジネスモデル、業績トレンド、最新トピックを簡潔に要約

---

## 🏗️ システムアーキテクチャ

### **デプロイ構成 (Oracle Cloud)**

```
┌─────────────────────────────────────────┐
│  Oracle Cloud Infrastructure (OCI)     │
│  ┌───────────────────────────────────┐ │
│  │  Discord Bot (Systemd Service)    │ │
│  │  - 常時稼働 (24/7)                │ │
│  │  - /analyze コマンド受付          │ │
│  │  - PDF生成・送信                  │ │
│  └───────────────────────────────────┘ │
│  ┌───────────────────────────────────┐ │
│  │  Data Updater (Cron Job)          │ │
│  │  - 毎日定刻実行 (18:00)           │ │
│  │  - 株・プラスAPIからデータ取得     │ │
│  │  - SQLiteデータベース更新         │ │
│  └───────────────────────────────────┘ │
│  ┌───────────────────────────────────┐ │
│  │  SQLite Database                  │ │
│  │  - 日足株価 (約3,800銘柄)         │ │
│  │  - 週次信用残 (最新26週分)        │ │
│  │  - 財務指標・業種別指数           │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### **重要な変更点**
- ✅ **GitHub Actionsは不要**: OCI上でデータ更新が完結するため、GitHub Actionsによるデータ同期は廃止されました
- ✅ **完全自律稼働**: サーバー再起動時も自動復旧（Systemdによる管理）
- ✅ **低コスト運用**: Oracle Cloud Free Tierで運用可能

---

## 📂 ディレクトリ構成

```text
個別株分析/
├── data/                        # SQLite Database
│   └── stock_data.db            # 全銘柄データ (日足・信用残・財務)
├── src/
│   ├── bot/
│   │   └── discord_bot.py       # Discord Bot メインエントリーポイント
│   ├── core/
│   │   ├── db_manager.py        # DB接続・スキーマ管理
│   │   └── batch_loader.py      # 日次データ更新スクリプト
│   ├── analysis/
│   │   ├── technical_chart.py   # テクニカルチャート生成
│   │   ├── supply_demand.py     # 需給分析ダッシュボード生成
│   │   └── company_overview.py  # AI企業概要生成 (未実装)
│   └── utils/
│       └── pdf_generator.py     # PDFレイアウト・結合エンジン
├── dataset/
│   └── fonts/                   # 日本語フォント (IPAゴシック等)
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
| **AI** | Google Gemini API (Flash 2.0) *将来* |
| **データソース** | 株・プラス (kabu.plus) |
| **インフラ** | Oracle Cloud (Oracle Linux 8/9) |
| **プロセス管理** | Systemd (Bot常駐), Cron (データ更新) |

---

## 🔄 データフロー

### **日次データ更新フロー**
```
1. Cron Job (毎日18:00) → batch_loader.py 実行
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

## 🚀 デプロイ方法

詳細は [`deployment_guide.md`](./.gemini/antigravity/brain/cd2bc25c-9290-46c3-99e6-e9ef30c4a2b8/deployment_guide.md) を参照してください。

**概要:**
1. Oracle Cloud (OCI) にSSH接続
2. プロジェクトファイルを `rsync` でアップロード
3. 依存ライブラリをインストール (`pip install -r requirements.txt`)
4. Systemdサービスとして登録 (Bot自動起動)
5. Cronでデータ更新を設定 (毎日18:00実行)

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
| sell_balance_ins / buy_balance_ins | REAL | 制度信用 売残/買残 |
| sell_balance_gen / buy_balance_gen | REAL | 一般信用 売残/買残 |

---

## ⚙️ 環境変数 (`.env`)

```bash
# Discord Bot Token
DISCORD_BOT_TOKEN=your_discord_bot_token

# 株・プラス認証情報
KABU_PLUS_USER=your_username
KABU_PLUS_PASSWORD=your_password

# Google Gemini API (将来)
GEMINI_API_KEY=your_gemini_api_key
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
git clone https://github.com/yourusername/stock-analysis-bot.git
cd stock-analysis-bot

# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定 (.env ファイルを作成)
cp .env.example .env
# .env を編集して認証情報を追加

# データベース初期化
python -m src.core.db_manager

# データ取得 (直近180日分)
python -m src.batch_loader

# Bot起動
python main.py
```

### テスト用PDF生成

```bash
python test_pdf_generation.py 7203
```
→ `debug/reports/` フォルダにPDFが生成されます。

---

## 📋 今後の開発予定

- [ ] AI企業概要機能の実装 (Gemini API統合)
- [ ] 複数銘柄の比較レポート機能
- [ ] アラート機能 (特定条件でレポート自動送信)
- [ ] Webダッシュボード (FastAPI + React)

---

## 📄 ライセンス

このプロジェクトは個人利用を目的としています。

---

## 👤 作者

開発: [@hiranotakahiro](https://github.com/hiranotakahiro)

---

## 🙏 謝辞

- データ提供: [株・プラス (kabu.plus)](https://csvex.com/)
- フレームワーク: discord.py, mplfinance, ReportLab
