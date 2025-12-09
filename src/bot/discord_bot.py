import os
import discord
import io
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 新しいプロジェクト構造に基づくインポート
from src.core.data_loader import fetch_data
from src.analysis.technical_chart import generate_charts
from src.analysis.supply_demand import SupplyDemandAnalyzer
from src.analysis.company_overview import CompanyOverviewGenerator
from src.utils.pdf_generator import generate_pdf_report

# .envファイルを読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Discord Botの設定
intents = discord.Intents.default()
intents.message_content = True 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Bot Login Successful: {client.user} としてログインしました。')
    print("--- 動作確認用: Discordで /analyze <証券コード> を試してください ---")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # /analyze コマンドの処理
    if message.content.startswith('/analyze'):
        async with message.channel.typing():
            try:
                parts = message.content.split(' ')
                if len(parts) < 2:
                    await message.channel.send('エラー: 証券コードを入力してください。例: `/analyze 7203`')
                    return
                
                code = parts[1]
                await message.channel.send(f'🔍 **{code}** のデータを分析中... (数秒〜数十秒かかります)')

                # --- 1. データ取得 ---
                data = fetch_data(code)
                if data.get("error"):
                    await message.channel.send(f"❌ データ取得エラー: {data['error']}")
                    return
                
                company_name = data['company_name']
                
                # --- 2. AI分析 (Gemini) ---
                # NOTE: 並列処理したいが、まずは直列で実装
                overview_gen = CompanyOverviewGenerator()
                # 業種データは fetch_data の戻り値に含まれていないため、DBや補足情報が必要だが、
                # data_loader が返す company_summary からある程度推測、またはAIに任せる
                # ここでは正確を期すため、簡易的に data['company_summary'] を使用するか、
                # data_loader の戻り値を拡張するのがベストだが、今回は一旦 'Unknown' または data内から探す
                
                # fetch_dataの実装を見ると戻り値は:
                # stock_data, financial_data, margin_data, company_name, company_summary
                
                ai_result = overview_gen.generate_overview(code, company_name, "日本株") # 業種は現在取得フロー外のため仮置き
                
                ai_summary = ai_result.get('summary', '情報なし')
                ai_topics = ai_result.get('topics', '情報なし')

                # --- 3. テクニカルチャート生成 ---
                chart_res = generate_charts(
                    data['stock_data'], 
                    code, 
                    data['financial_data'], 
                    data['margin_data']
                )
                chart_buffer = chart_res['file']

                # --- 4. 需給分析 & メタデータ取得 ---
                sda = SupplyDemandAnalyzer()
                # 一時ファイルとして保存して読み込む (matplotlibの仕様回避)
                temp_dash_path = f"temp_dash_{code}_{datetime.now().timestamp()}.png"
                
                # plot_analysis は同期的に実行される
                meta_data = sda.plot_analysis(code, save_path=temp_dash_path)
                
                if not meta_data:
                    await message.channel.send(f"❌ 需給分析エラー: データの不足によりチャートを生成できませんでした。")
                    if os.path.exists(temp_dash_path): os.remove(temp_dash_path)
                    return

                # 画像をバッファに読み込み
                with open(temp_dash_path, 'rb') as f:
                    dash_buffer = io.BytesIO(f.read())
                
                # 一時ファイル削除
                if os.path.exists(temp_dash_path):
                    os.remove(temp_dash_path)

                # --- 5. PDFレポート生成 ---
                pdf_buffer = generate_pdf_report(
                    meta_data,
                    chart_buffer,
                    dash_buffer
                )
                
                # --- 6. Discord送信 ---
                # AIの要約をメッセージ本文として送信
                response_text = (
                    f"## 📊 {company_name} ({code}) 分析レポート\n"
                    f"**【事業概要】**\n{ai_summary}\n\n"
                    f"**【直近トピック】**\n{ai_topics}\n"
                )
                
                # PDFを添付
                file = discord.File(pdf_buffer, filename=f"Report_{code}.pdf")
                
                await message.channel.send(content=response_text, file=file)
                print(f"✅ Sent report for {code}")

            except Exception as e:
                import traceback
                traceback.print_exc()
                await message.channel.send(f'❌ 予期せぬエラーが発生しました: {str(e)}')

if __name__ == '__main__':
    if TOKEN:
        client.run(TOKEN)
    else:
        print("❌ Error: .envファイルにDISCORD_BOT_TOKENが設定されていません。")
