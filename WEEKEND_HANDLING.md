# 週末・休日のデータ更新について

## 📅 動作概要

GitHub Actionsは**毎日17時（日本時間）**に実行されますが、株・プラスのデータが公開されていない日（週末・祝日）は、データ取得をスキップして正常終了します。

---

## 🔄 週末・休日の動作フロー

### 1. 通常の営業日（月〜金）

```
17:00 JST → GitHub Actions起動
   ↓
データダウンロード開始
   ↓
✅ 株価データ取得成功（3,780〜3,790件）
✅ 財務データ取得成功
✅ 業種別指数取得成功
✅ 信用残データ取得（週次・該当日のみ）
   ↓
データベース更新
   ↓
Artifactアップロード
   ↓
✅ ワークフロー成功
```

### 2. 週末・祝日

```
17:00 JST → GitHub Actions起動
   ↓
データダウンロード開始
   ↓
⚠️  株価データ: 404 Not Found → スキップ
⚠️  財務データ: 404 Not Found → スキップ
⚠️  業種別指数: 404 Not Found → スキップ
⚠️  信用残データ: 市場休業日 → スキップ
   ↓
データベースは更新されない（前日のまま）
   ↓
Artifactアップロード（変更なし）
   ↓
✅ ワークフロー成功（エラーではない）
```

---

## 📊 実際のログ例

### 土曜日のログ

```
Processing: 20251124
  -> スキップ: japan-all-stock-prices-2_20251124.csv (404 Not Found)
  -> スキップ: japan-all-stock-data_20251124.csv (404 Not Found)
  -> スキップ: 20251124 (市場休業日/祝日)
  -> スキップ: tosho-index-data_20251124.csv (404 Not Found)
```

### 翌営業日（月曜日）のログ

```
Processing: 20251125
  -> 株価・企業情報: 3787件 処理完了
  -> 財務指標: 3787件 処理完了
  -> スキップ: tosho-stock-margin-transactions-2_20251125.csv (404 Not Found)
  -> 業種別指数データ: 110件 処理完了
```

---

## ⚙️ 技術的な実装

### エラーハンドリング

[batch_loader.py](file:///Users/hiranotakahiro/Projects/個別株分析/src/batch_loader.py) では、404エラーを適切に処理しています：

```python
def fetch_csv_as_dataframe(url: str, session: requests.Session, skiprows: int = 0):
    try:
        response = session.get(url, auth=auth_tuple, timeout=TIMEOUT)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content), encoding=ENCODING, skiprows=skiprows)
        return df

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"  -> スキップ: {url.split('/')[-1]} (404 Not Found)")
        # エラーでもNoneを返してスキップ
    return None
```

### 祝日チェック

信用残データの処理では、`jpholiday`ライブラリで祝日を判定：

```python
import jpholiday

download_date = datetime.strptime(date_str, '%Y%m%d').date()
if jpholiday.is_holiday(download_date):
    print(f"  -> スキップ: {date_str} (市場休業日/祝日)")
    return
```

---

## 📈 データ更新の頻度

| 曜日 | データ更新 | 備考 |
|------|----------|------|
| 月曜日 | ✅ あり | 通常営業日 |
| 火曜日 | ✅ あり | 通常営業日 + 信用残公表日（週次） |
| 水曜日 | ✅ あり | 通常営業日 |
| 木曜日 | ✅ あり | 通常営業日 |
| 金曜日 | ✅ あり | 通常営業日 |
| 土曜日 | ❌ なし | 市場休業日 |
| 日曜日 | ❌ なし | 市場休業日 |
| 祝日 | ❌ なし | 市場休業日 |

---

## 🎯 メリット

### 1. 無駄な処理がない

データがない日はスキップされるため、GitHub Actionsの実行時間を節約できます。

**週末の実行時間**: 約30秒〜1分（データ取得スキップのため高速）  
**営業日の実行時間**: 約5〜10分（データダウンロード・処理含む）

### 2. エラー通知が不要

404エラーは正常な動作としてスキップされるため、週末にエラーメール通知が送られることはありません。

### 3. データベースの一貫性

データが取得できない日はデータベースを更新しないため、一貫性が保たれます。

---

## 🔔 通知設定（オプション）

### 営業日のみ通知を受け取りたい場合

週末の実行は無視し、営業日の成功/失敗のみ通知を受け取りたい場合：

1. GitHubの **Settings** → **Notifications**
2. **Actions** セクションで通知設定を調整
3. または、ワークフローに通知ステップを追加（Slack/Discord）

---

## 📝 まとめ

- ✅ **毎日17時（JST）に実行**: 確実にスケジュール通り動作
- ✅ **週末・祝日は自動スキップ**: エラーにならず正常終了
- ✅ **営業日のみデータ更新**: 最新データが確実に取得される
- ✅ **無駄なリソース消費なし**: データがない日は高速終了

この設計により、手動での設定変更やメンテナンスなしで、年間を通じて安定して動作します！🎉
