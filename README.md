# Japanese Stock Analysis Bot (Discord Integration)

## 📌 プロジェクト概要
Discord上で動作する日本株分析Botです。
ユーザーが `/analyze [証券コード]` コマンドを送信すると、対象銘柄の**「企業概要」「テクニカルチャート」「需給分析」**を1枚のPDFレポートにまとめて返信します。
Oracle Cloud等の常時稼働サーバー（Docker運用）での動作を想定しています。

## 🎯 最終成果物 (Output)
**A4サイズ PDFレポート構成**
1.  **上段: 企業概要 (AI Summary)**
    *   Gemini APIを使用し、企業のビジネスモデル、直近のトピック、業績概要を簡潔にまとめたテキスト。
2.  **中段: テクニカル分析チャート (Visual)**
    *   ローソク足（6ヶ月）、移動平均線（5日/25日）、出来高、価格帯別出来高。
3.  **下段: 需給分析ダッシュボード (Supply-Demand)**
    *   信用残推移、セクター比較、需給スコアレーダーチャート、各種需給指標。

## 📂 ディレクトリ構成 (Refactored)

```text
Projects/個別株分析/
├── data/                    # SQLite Database (stock_data.db)
├── src/
│   ├── bot/                 # Discord Bot Interface
│   │   └── discord_bot.py   # Bot Main Entry Point (Slash Commands)
│   ├── core/                # Core Infrastructure
│   │   ├── db_manager.py    # Database Connection & Schema
│   │   ├── data_loader.py   # Data Fetching Logic
│   │   └── batch_loader.py  # Daily Data Update Script
│   ├── analysis/            # Analysis & Visualization Engines
│   │   ├── company_overview.py # [New] AI Company Summary Generator
│   │   ├── technical_chart.py  # [Renamed] Chart Generator (Middle Panel)
│   │   └── supply_demand.py    # Supply-Demand Analyzer (Bottom Panel)
│   └── utils/               # Utilities
│       └── pdf_generator.py # PDF Composition Layout Engine
├── scripts/                 # Shell Scripts (Auto-update, etc.)
└── requirements.txt
```

## 🛠️ 技術スタック
- **Language**: Python 3.11+
- **Platform**: Discord (py-cord / discord.py)
- **Database**: SQLite3
- **Analysis**: Pandas, NumPy
- **Visualization**: Matplotlib, mplfinance
- **AI**: Google Gemini API (Flash 2.0 ideally)
- **Infrastructure**: Oracle Cloud (Free Tier), GitHub Actions (Data Sync)

## 🔄 データフロー
1.  **Data Update**: GitHub Actions or Cron job runs `batch_loader.py` daily to update `stock_data.db`.
2.  **User Request**: User types `/analyze 7203` in Discord.
3.  **Processing**:
    *   `discord_bot.py` receives request.
    *   `company_overview.py` fetches info and generates summary via AI.
    *   `technical_chart.py` generates chart image.
    *   `supply_demand.py` generates dashboard image.
    *   `pdf_generator.py` combines images and text into a single PDF.
4.  **Response**: Bot uploads the PDF to Discord.

## ✅ Next Steps
1.  Refactor folder structure.
2.  Implement `company_overview.py` (AI summarization).
3.  Refine `technical_chart.py` (Middle panel layout).
4.  Update `supply_demand.py` (Bottom panel layout & styles).
5.  Update `pdf_generator.py` (Combine all 3 elements).
6.  Finalize `discord_bot.py`.
