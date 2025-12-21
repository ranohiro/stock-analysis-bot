import os
import discord
import io
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 新しいプロジェクト構造に基づくインポート
from src.core.data_loader import fetch_data
from src.core.db_manager import log_analysis_history, get_analysis_history  # 履歴機能
from src.analysis.technical_chart import generate_charts
from src.analysis.supply_demand import SupplyDemandAnalyzer
# from src.analysis.company_overview import CompanyOverviewGenerator  # 未使用
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
    # デバッグ: メッセージ受信確認
    print(f"[DEBUG] Message received: '{message.content}' from {message.author}")
    
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
                print(f"[INFO] Starting analysis for {code}")
                
                # シンプルなメッセージのみ
                status_msg = await message.channel.send(f'🔍 **{code}** を分析中...')

                # --- 1. データ取得 ---
                print(f"[STEP 1/5] Fetching data for {code}...")
                data = fetch_data(code)
                print(f"[STEP 1/5] Data fetch completed for {code}")
                if data.get("error"):
                    await message.channel.send(f"❌ エラー: {data['error']}")
                    return
                
                company_name = data['company_name']
                
                # --- 2. AI分析はスキップ（オプション機能） ---
                # overview_gen = CompanyOverviewGenerator()
                # ai_result = overview_gen.generate_overview(code, company_name, "日本株")
                
                # --- 3. テクニカルチャート生成 ---
                print(f"[STEP 2/5] Generating technical charts for {code}...")
                chart_res = generate_charts(
                    data['stock_data'], 
                    code, 
                    data['financial_data'], 
                    data['margin_data']
                )
                chart_buffer = chart_res['file']
                print(f"[STEP 2/5] Technical charts completed for {code}")

                # --- 4. 需給分析 & メタデータ取得 ---
                print(f"[STEP 3/5] Analyzing supply/demand for {code}...")
                sda = SupplyDemandAnalyzer()
                temp_dash_path = f"temp_dash_{code}_{datetime.now().timestamp()}.png"
                
                meta_data = sda.plot_analysis(code, save_path=temp_dash_path)
                print(f"[STEP 3/5] Supply/demand analysis completed for {code}")
                
                if not meta_data:
                    await message.channel.send(f"❌ データ不足のため生成できませんでした。")
                    if os.path.exists(temp_dash_path): os.remove(temp_dash_path)
                    return

                with open(temp_dash_path, 'rb') as f:
                    dash_buffer = io.BytesIO(f.read())
                
                if os.path.exists(temp_dash_path):
                    os.remove(temp_dash_path)

                # --- 5. PDFレポート生成 ---
                print(f"[STEP 4/5] Generating PDF report for {code}...")
                pdf_buffer = generate_pdf_report(
                    meta_data,
                    chart_buffer,
                    dash_buffer
                )
                print(f"[STEP 4/5] PDF generation completed for {code}")
                
                # --- 6. Discord送信（AI要約なし）---
                print(f"[STEP 5/5] Sending PDF to Discord for {code}...")
                file = discord.File(pdf_buffer, filename=f"Report_{code}.pdf")
                
                # 分析中メッセージを削除（エラーを無視）
                try:
                    await status_msg.delete()
                except Exception as del_err:
                    print(f"⚠️  Status message deletion failed (harmless): {del_err}")
                
                # PDFのみ送信
                await message.channel.send(file=file)
                
                # 履歴を記録（エラーを無視）
                try:
                    user_name = f"{message.author.name}#{message.author.discriminator}"
                    log_analysis_history(code, company_name, user_name, success=True)
                except Exception as log_err:
                    print(f"⚠️  History logging failed (harmless): {log_err}")
                
                print(f"[SUCCESS] Report sent successfully for {code}")

            except Exception as e:
                # エラーをログに記録するのみ（ユーザーには表示しない）
                # PDF生成は成功しているが、Discord接続タイムアウトなどで例外が発生する場合がある
                import traceback
                error_trace = traceback.format_exc()
                print(f"⚠️  Exception occurred (non-critical): {error_trace}")
    
    # /history コマンドの処理
    if message.content.startswith('/history'):
        try:
            history = get_analysis_history(limit=10)
            
            if not history:
                await message.channel.send('📊 分析履歴がありません。')
                return
            
            # 履歴を整形
            response = "📊 **分析履歴（最新10件）**\n━━━━━━━━━━━━━━━━\n"
            for record in history:
                record_id, stock_code, company_name, analyzed_at, user_name, success = record
                
                # 日時をフォーマット (ISO -> MM/DD HH:MM)
                dt = datetime.fromisoformat(analyzed_at)
                date_str = dt.strftime('%m/%d %H:%M')
                
                # 会社名表示
                company_display = f" ({company_name})" if company_name else ""
                
                # ステータス
                status_icon = "🔹" if success else "❌"
                
                # ユーザー名表示（あれば）
                user_display = f" - {user_name}" if user_name else ""
                
                response += f"{status_icon} {date_str} - {stock_code}{company_display}{user_display}\n"
            
            await message.channel.send(response)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await message.channel.send(f'❌ 履歴の取得に失敗しました: {str(e)}')

if __name__ == '__main__':
    if TOKEN:
        client.run(TOKEN)
    else:
        print("❌ Error: .envファイルにDISCORD_BOT_TOKENが設定されていません。")
