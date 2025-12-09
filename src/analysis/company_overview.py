import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class CompanyOverviewGenerator:
    def __init__(self):
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.api_key_set = True
            except Exception as e:
                print(f"Gemini Client Initialization Error: {e}")
                self.api_key_set = False
        else:
            self.api_key_set = False
            print("Warning: GEMINI_API_KEY is not set.")

    def generate_overview(self, code: str, name: str, industry: str) -> dict:
        """
        Generates a concise company overview (Business Summary & Recent Topics).
        """
        if not self.api_key_set:
            return {
                "summary": "AI分析機能が無効です (API Key未設定)",
                "topics": "AI分析機能が無効です (API Key未設定)"
            }

        # System Prompt
        system_prompt = (
            "あなたは日本の株式市場の専門家です。指定された企業の「事業内容」と「直近のトピック」を"
            "投資家向けレポートのために簡潔にまとめてください。"
            "ハルシネーション（嘘の生成）を避け、確実な情報のみを記述してください。"
        )

        # User Prompt
        user_prompt = f"""
        以下の日本株銘柄について、レポート用の概要を作成してください。

        **対象銘柄**: {name} (コード: {code})
        **業種**: {industry}

        **【出力フォーマット】**
        以下の2つのセクションに分けて出力してください。各セクションは150文字以内で簡潔にまとめてください。
        
        【事業内容】
        （主な事業、主力製品・サービス、市場シェアや特徴など）

        【直近トピック】
        （直近6ヶ月以内の決算ハイライト、重要なニュース、中期経営計画、または株価に影響を与えた主な出来事）
        """

        try:
            # Initialize model with system instruction
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                system_instruction=system_prompt
            )
            
            response = model.generate_content(
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1
                )
            )
            
            text = response.text
            
            # Simple parsing (robust enough for structured LLM output)
            summary = ""
            topics = ""
            
            if "【事業内容】" in text:
                parts = text.split("【事業内容】")
                if len(parts) > 1:
                    remaining = parts[1]
                    if "【直近トピック】" in remaining:
                        sub_parts = remaining.split("【直近トピック】")
                        summary = sub_parts[0].strip()
                        topics = sub_parts[1].strip()
                    else:
                        summary = remaining.strip()
            
            if not summary:
                 # Fallback if parsing fails
                 summary = text
            
            return {
                "summary": summary,
                "topics": topics
            }

        except Exception as e:
            print(f"Gemini API generation error: {e}")
            return {
                "summary": "情報の取得に失敗しました。",
                "topics": "情報の取得に失敗しました。"
            }

if __name__ == "__main__":
    # Test execution
    generator = CompanyOverviewGenerator()
    result = generator.generate_overview("7203", "トヨタ自動車", "輸送用機器")
    print("--- Summary ---")
    print(result['summary'])
    print("\n--- Topics ---")
    print(result['topics'])
