# Stock Analysis AI Bot (Discord版)

## プロジェクト概要
ユーザーが入力した証券コードに基づき、個別銘柄の多角的な分析レポート（ファンダメンタル・テクニカル・需給・企業概要）を **PDFファイルとして自動生成**し、Discord上で提供するAIチャットボットである。

膨大な財務・需給データを扱うため、バックグラウンドでデータベースを構築し、高速な応答と深い分析を両立させるアーキテクチャを採用している。

---

## アーキテクチャ構成



本システムは「常駐型ボット」と「定期実行バッチ」の2つのプロセスで構成される。

1.  **Discord Bot (常駐):**
    * ユーザーからのコマンドを受信。
    * ローカルDB (SQLite) から高速に過去データを取得する。
    * リアルタイム株価を取得する。
    * AI分析・グラフ生成・PDF作成を行い、ユーザーに返信する。
2.  **Data Batch Job (定期実行):**
    * 1日1回（深夜など）実行する。
    * 「株・プラス」から全銘柄の財務・信用残データを一括ダウンロードする。
    * データを整理し、SQLiteデータベースを更新（Upsert）する。
3.  **Infrastructure:**
    * **Oracle Cloud (Always Free):** 24時間稼働のVPS環境を採用する。

---

## 機能要件

### 1. 入力インターフェース
- **プラットフォーム:** Discord
- **コマンド:** `/analyze <証券コード>`
- **入力例:** `/analyze 7203`

### 2. アウトプット (PDFレポート)
分析結果はプロフェッショナルな **PDFレポート**として生成・添付される。

#### PDF構成要素
* **ヘッダー:** 銘柄名、証券コード、現在株価、分析日時
* **セクション1: 企業概要**
    * 事業内容、Moat（強み）、リスク要因
* **セクション2: チャート分析 (画像埋め込み)**
    * ローソク足チャート (日足/週足) + 移動平均線
    * サブチャート: RSI, ストキャスティクス
* **セクション3: ファンダメンタルズ推移 (グラフ/表)**
    * 過去5年の売上・利益・EPS推移グラフ
    * PER/PBR/ROEの推移（割安感の視覚化）
* **セクション4: 需給状況**
    * 信用倍率の推移、機関空売り状況
* **セクション5: AIアナリストの考察**
    * Geminiによる総合評価（強気/中立/弱気）と詳細コメント

---

## データ取得・管理戦略

パフォーマンス確保のため、**「オンデマンド取得」と「事前蓄積」**を使い分ける。

| データ種別 | 取得元 | 取得タイミング | 保存先 |
| :--- | :--- | :--- | :--- |
| **リアルタイム株価** | 株・プラス (API/CSV) | **オンデマンド** (コマンド実行時) | メモリ (一時利用) |
| **企業概要・ニュース** | Google Search API / Web | **オンデマンド** | メモリ (一時利用) |
| **財務・指標データ** | 株・プラス (Daily CSV) | **バッチ処理** (毎日) | **SQLite Database** |
| **信用残データ** | 株・プラス (Weekly CSV) | **バッチ処理** (週末) | **SQLite Database** |

---

## 技術スタック

### アプリケーション
- **言語:** Python 3.9+
- **Bot Framework:** `discord.py`
- **Database:** `sqlite3` (軽量RDB)
- **PDF Generation:** `reportlab` (高度なPDF描画)
- **Visualization:** `mplfinance`, `matplotlib`
- **AI Model:** Google Gemini API (`gemini-1.5-flash` 推奨)

### インフラ・運用
- **Server:** Oracle Cloud Infrastructure (Always Free / VM.Standard.E2.Micro)
- **OS:** Ubuntu Linux
- **Job Scheduler:** `cron` (Linux標準スケジューラ)

---

## ディレクトリ構成 (Planned)

```text
stock-analysis-bot/
├── data/
│   └── stock_data.db       # SQLiteデータベース (Git除外)
├── src/
│   ├── main.py             # Bot起動・イベントハンドラ
│   ├── batch_loader.py     # 定期実行用データ収集スクリプト
│   ├── db_manager.py       # データベース操作(CRUD)
│   ├── data_loader.py      # Bot用データ読み込み (DB参照)
│   ├── analyzer.py         # Gemini AI分析ロジック
│   ├── chart_generator.py  # グラフ画像生成
│   └── pdf_generator.py    # PDFレポート作成
├── images/                 # 一時画像フォルダ (Git除外)
├── .env                    # APIキー設定
├── .gitignore
├── requirements.txt
└── README.md
