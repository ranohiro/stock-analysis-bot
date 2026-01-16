# データベース内容と参照元情報

このプロジェクトで使用されているSQLiteデータベース（`data/stock_data.db`）の内容と、そのデータ参照元についての情報は以下の通りです。

## データベース内容

データベースには以下のテーブルが含まれています。

### 1. companies (企業マスタ)
企業情報の基本データを格納します。
- `code`: 証券コード (PRIMARY KEY)
- `name`: 企業名
- `market`: 市場区分
- `industry`: 業種

### 2. daily_prices (日足株価)
毎日の株価情報を格納します。
- `code`: 証券コード
- `date`: 日付 (YYYYMMDD形式)
- `open`: 始値
- `high`: 高値
- `low`: 安値
- `close`: 終値
- `volume`: 出来高
- `trading_value`: 売買代金
- `market_cap_total`: 時価総額

### 3. daily_financials (日足財務指標)
毎日の財務指標を格納します。
- `code`: 証券コード
- `date`: 日付 (YYYYMMDD形式)
- `market_cap`: 時価総額
- `shares_outstanding`: 発行済株式数
- `per_forecast`: PER（予想）
- `pbr_actual`: PBR（実績）
- `eps_forecast`: EPS（予想）
- `bps_actual`: BPS（実績）
- `dividend_yield`: 配当利回り
- `min_investment`: 最低投資金額

### 4. weekly_margin (週次信用残)
週次の信用取引残高情報を格納します。
- `code`: 証券コード
- `date`: 日付 (YYYYMMDD形式)
- `sell_balance_total`: 信用売残合計
- `buy_balance_total`: 信用買残合計
- `ratio`: 貸借倍率
- `sell_balance_ins`: 制度信用売残
- `buy_balance_ins`: 制度信用買残
- `sell_balance_gen`: 一般信用売残
- `buy_balance_gen`: 一般信用買残

### 5. daily_indices (指数データ)
東証インデックスやセクター別指数を格納します。
- `code`: 指数コード
- `name`: 指数名
- `date`: 日付 (YYYYMMDD形式)
- `close`: 終値
- `change_ratio`: 前日比（％）
- `market_cap_index`: 時価総額（指数用・浮動株ベース）
- `volume`: 売買単位換算後株式数
- `銘柄数`: 構成銘柄数

### 6. analysis_history (分析履歴)
ユーザーによる分析リクエストの履歴を記録します。
- `id`: ID
- `stock_code`: 証券コード
- `company_name`: 会社名
- `analyzed_at`: 分析日時
- `user_name`: ユーザー名
- `success`: 成功フラグ

## 参照元データ (Reference Source)

このデータベースのデータは、**「株・プラス (Kabu Plus)」** のCSVデータ配信サービスから取得されています。

- **提供元サイト**: [株・プラス](https://csvex.com/kabu.plus/csv/)
- **データ取得処理**: `src/core/batch_loader.py`
- **使用されているCSVファイル**:
    - `japan-all-stock-prices-2`: 日本全銘柄株価（日次） -> `daily_prices`, `companies`
    - `japan-all-stock-data`: 日本全銘柄各種指標（日次） -> `daily_financials`
    - `tosho-stock-margin-transactions-2`: 東証信用残（週次） -> `weekly_margin`
    - `tosho-index-data`: 東証指数（日次） -> `daily_indices`

※ ルートディレクトリにある `stock_analysis.db` は初期構成時の名残または未使用のファイルであり、実際のアプリケーションロジックは `data/stock_data.db` を使用しています。
