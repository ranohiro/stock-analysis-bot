# Stock Analysis Bot - 定期実行セットアップ手順

## 概要
このドキュメントでは、株価データの定期的な自動更新を実現するための手順を説明します。

---

## ✅ 完了済み

以下の作業は既に完了しています：

1. **データベースの最新化**
   - 2024年11月6日〜12月5日のデータを取得
   - 3,911社の企業データを更新
   - 267日分の株価データを保存

2. **自動実行スクリプトの作成**
   - `run_batch_update.sh`: バッチ処理を実行するシェルスクリプト
   - エラーハンドリング、ログ出力、統計情報の表示機能を実装

3. **launchd設定ファイルの作成**
   - `com.stockanalysis.batchupdate.plist`: 定期実行設定ファイル
   - 毎日午前2時に自動実行

---

## 🔧 セットアップ手順（手動実行が必要）

### ステップ1: plistファイルを配置する

プロジェクトディレクトリ内に作成された`com.stockanalysis.batchupdate.plist`を、macOSの`LaunchAgents`ディレクトリにコピーします。

```bash
cp /Users/hiranotakahiro/Projects/個別株分析/com.stockanalysis.batchupdate.plist ~/Library/LaunchAgents/
```

### ステップ2: launchdに登録する

以下のコマンドでlaunchdに登録し、定期実行を有効化します。

```bash
launchctl load ~/Library/LaunchAgents/com.stockanalysis.batchupdate.plist
```

### ステップ3: 登録を確認する

正常に登録されたかを確認します。

```bash
launchctl list | grep stockanalysis
```

以下のような出力が表示されれば成功です：
```
-	0	com.stockanalysis.batchupdate
```

---

## 🧪 テスト実行

### 手動でバッチ処理を実行してテストする

定期実行の設定前に、スクリプトが正常に動作するか確認します。

```bash
cd /Users/hiranotakahiro/Projects/個別株分析
./run_batch_update.sh
```

成功すると、`logs/`ディレクトリにログファイルが生成され、データベースが更新されます。

### launchdから即座に実行してテストする

登録後、次の定期実行を待たずに手動で起動してテストできます。

```bash
launchctl start com.stockanalysis.batchupdate
```

実行結果は以下のログファイルで確認できます：
- 標準出力: `/Users/hiranotakahiro/Projects/個別株分析/logs/launchd.out.log`
- エラー出力: `/Users/hiranotakahiro/Projects/個別株分析/logs/launchd.err.log`

---

## 📊 動作確認

### データベースの最新データを確認

```bash
cd /Users/hiranotakahiro/Projects/個別株分析
sqlite3 data/stock_data.db "SELECT MAX(date) FROM daily_prices;"
```

### ログファイルを確認

最新のバッチ実行ログを表示：
```bash
ls -lt logs/batch_update_*.log | head -1 | awk '{print $9}' | xargs cat
```

---

## 🛑 定期実行を停止する方法

定期実行を一時的に停止したい場合：

```bash
launchctl unload ~/Library/LaunchAgents/com.stockanalysis.batchupdate.plist
```

再度有効化する場合：
```bash
launchctl load ~/Library/LaunchAgents/com.stockanalysis.batchupdate.plist
```

完全に削除する場合：
```bash
launchctl unload ~/Library/LaunchAgents/com.stockanalysis.batchupdate.plist
rm ~/Library/LaunchAgents/com.stockanalysis.batchupdate.plist
```

---

## 📝 実行スケジュール

- **実行時刻**: 毎日午前2時（日本時間）
- **実行内容**: 株・プラスから最新30日分のデータをダウンロード
- **ログ保存**: `/Users/hiranotakahiro/Projects/個別株分析/logs/`
- **ログ保持期間**: 30日間（古いログは自動削除）

---

## ⚠️ 注意事項

1. **Macがスリープ状態の場合**
   - launchdジョブは実行されません
   - 確実に実行するには、午前2時にMacが起動している必要があります
   - または、次回起動時に自動実行されるよう`StartOnMount`を追加することも可能です

2. **株・プラス認証情報**
   - `.env`ファイルに`KABU_PLUS_USER`と`KABU_PLUS_PASSWORD`が正しく設定されている必要があります
   - 認証情報が無効な場合、データ取得に失敗します

3. **ディスク容量**
   - データベースは継続的に増加します
   - 定期的にディスク容量を確認してください

---

## 🎯 次のステップ

定期実行が正常に動作することを確認したら、優先度2のタスク「Discord Botの起動とローカル環境での動作確認」に進むことができます。

1. Discord Botを起動
2. `/analyze 証券コード`コマンドでテスト
3. 最新データを使った分析レポート（PDF）が生成されることを確認
