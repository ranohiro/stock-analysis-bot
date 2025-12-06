import io
import os
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pandas as pd


def setup_japanese_font():
    """日本語フォントを登録する"""
    try:
        # IPA ゴシックフォントを使用
        font_paths = [
            '/Library/Fonts/IPAGothic.ttc',
            '/Library/Fonts/ipag.ttf',
            '~/Library/Fonts/IPAGothic.ttc',
            '~/Library/Fonts/ipag.ttf'
        ]
        
        for font_path in font_paths:
            expanded_path = os.path.expanduser(font_path)
            if os.path.exists(expanded_path):
                pdfmetrics.registerFont(TTFont('Japanese', expanded_path))
                pdfmetrics.registerFont(TTFont('JapaneseBold', expanded_path))
                print(f"✅ 日本語フォント登録成功: {font_path}")
                return True
        
        # フォントが見つからない場合
        print("⚠️  IPAフォントが見つかりません。")
        return False
        
    except Exception as e:
        print(f"⚠️  日本語フォント登録失敗: {e}")
        print("デフォルトフォント（Helvetica）を使用します。")
        return False


def generate_pdf_report(
    company_name: str,
    code: str,
    current_price: float,
    summary: str,
    stock_data: pd.DataFrame,
    financial_data: pd.DataFrame,
    chart_image_buffer: io.BytesIO,
    ai_analysis: str
) -> io.BytesIO:
    """
    株式分析レポートをPDF形式で生成する。
    
    Args:
        company_name: 企業名
        code: 証券コード
        current_price: 現在株価
        summary: 企業概要
        stock_data: 株価データ (DataFrame)
        financial_data: 財務データ (DataFrame)
        chart_image_buffer: チャート画像 (BytesIO)
        ai_analysis: AI分析結果テキスト
        
    Returns:
        PDF データ (BytesIO)
    """
    
    # 日本語フォントを登録
    font_available = setup_japanese_font()
    base_font = 'Japanese' if font_available else 'Helvetica'
    bold_font = 'JapaneseBold' if font_available else 'Helvetica-Bold'
    
    # PDFをメモリ上に作成
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=15*mm, 
        bottomMargin=15*mm,
        leftMargin=15*mm,
        rightMargin=15*mm
    )
    
    # ストーリー（PDFの内容を構成する要素のリスト）
    story = []
    
    # スタイル設定
    styles = getSampleStyleSheet()
    
    # カスタムスタイルを追加（日本語対応）
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName=bold_font,
        leading=28
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName=base_font
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=8,
        spaceBefore=12,
        fontName=bold_font,
        borderWidth=0,
        borderColor=colors.HexColor('#2c5aa0'),
        borderPadding=0,
        leftIndent=0,
        leading=20
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        fontName=base_font,
        leading=16,
        alignment=TA_JUSTIFY
    )
    
    # --- ヘッダーセクション ---
    story.append(Paragraph(f"{company_name} ({code})", title_style))
    story.append(Paragraph("株式分析レポート", subtitle_style))
    
    # 区切り線
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2c5aa0'), spaceAfter=10))
    
    # 現在株価と分析日時を横並びで表示
    current_date = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    header_data = [
        ['証券コード', code, '分析日時', current_date],
        ['現在株価', f'¥{current_price:,.0f}', '市場', stock_data.index[-1].strftime('%Y/%m/%d')]
    ]
    
    header_table = Table(header_data, colWidths=[30*mm, 40*mm, 30*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f4f8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), bold_font),
        ('FONTNAME', (2, 0), (2, -1), bold_font),
        ('FONTNAME', (1, 0), (1, -1), base_font),
        ('FONTNAME', (3, 0), (3, -1), base_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 8*mm))
    
    # --- セクション1: 企業概要 ---
    story.append(Paragraph("1. 企業概要", heading_style))
    story.append(HRFlowable(width="30%", thickness=2, color=colors.HexColor('#2c5aa0'), spaceAfter=6, spaceBefore=0))
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 8*mm))
    
    # --- セクション2: チャート分析 ---
    story.append(Paragraph("2. チャート分析", heading_style))
    story.append(HRFlowable(width="30%", thickness=2, color=colors.HexColor('#2c5aa0'), spaceAfter=6, spaceBefore=0))
    
    # チャート画像を大きく埋め込み
    chart_image_buffer.seek(0)
    img = Image(chart_image_buffer, width=170*mm, height=110*mm)
    story.append(img)
    story.append(Spacer(1, 4*mm))
    
    # チャート統計情報
    latest_close = stock_data['Close'].iloc[-1]
    last_90_days_avg = stock_data['Close'].iloc[-90:].mean()
    change_from_avg = ((latest_close - last_90_days_avg) / last_90_days_avg) * 100
    
    chart_text = f"<b>現在株価:</b> ¥{latest_close:,.0f}　<b>90日平均:</b> ¥{last_90_days_avg:,.0f}　<b>変化率:</b> {change_from_avg:+.1f}%"
    story.append(Paragraph(chart_text, body_style))
    story.append(Spacer(1, 8*mm))
    
    # --- セクション3: ファンダメンタルズ推移 ---
    story.append(Paragraph("3. ファンダメンタルズ推移", heading_style))
    story.append(HRFlowable(width="30%", thickness=2, color=colors.HexColor('#2c5aa0'), spaceAfter=6, spaceBefore=0))
    
    # 財務データをテーブル化
    if not financial_data.empty:
        # データフレームを整形
        display_df = financial_data.copy()
        
        # 日付フォーマット
        display_df['Date'] = display_df['Date'].dt.strftime('%Y/%m/%d')
        
        # 数値フォーマット
        for col in ['PER', 'PBR', 'EPS', 'BPS']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f'{x:.2f}' if pd.notna(x) else '-')
        
        if 'Dividend_Yield' in display_df.columns:
            display_df['Dividend_Yield'] = display_df['Dividend_Yield'].apply(lambda x: f'{x:.2f}%' if pd.notna(x) else '-')
        
        if 'Market_Cap' in display_df.columns:
            display_df['Market_Cap'] = display_df['Market_Cap'].apply(lambda x: f'{x/100:.0f}億円' if pd.notna(x) else '-')
        
        # カラム名を日本語に
        display_df = display_df.rename(columns={
            'Date': '日付',
            'PER': '予想PER',
            'PBR': '実績PBR',
            'EPS': '予想EPS',
            'BPS': '実績BPS',
            'Dividend_Yield': '配当利回り',
            'Market_Cap': '時価総額'
        })
        
        # テーブルデータ作成
        financial_table_data = [display_df.columns.tolist()] + display_df.values.tolist()
        
        col_count = len(display_df.columns)
        col_width = 180 / col_count
        
        financial_table = Table(financial_table_data, colWidths=[col_width*mm] * col_count)
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), bold_font),
            ('FONTNAME', (0, 1), (-1, -1), base_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d0d0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        story.append(financial_table)
    else:
        story.append(Paragraph("財務データが取得できませんでした。", body_style))
    
    story.append(Spacer(1, 10*mm))
    
    # --- セクション4: AI分析結果 ---
    story.append(Paragraph("4. AIアナリストの考察", heading_style))
    story.append(HRFlowable(width="30%", thickness=2, color=colors.HexColor('#2c5aa0'), spaceAfter=6, spaceBefore=0))
    
    # AI分析テキストを段落に分割して追加
    for paragraph in ai_analysis.split('\n\n'):
        if paragraph.strip():
            # HTML特殊文字をエスケープ
            safe_text = paragraph.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # マークダウンの ** を削除
            safe_text = safe_text.replace('**', '')
            # 箇条書きの処理
            safe_text = safe_text.replace('* ', '• ')
            
            try:
                story.append(Paragraph(safe_text, body_style))
                story.append(Spacer(1, 3*mm))
            except Exception as e:
                # パース失敗時はそのまま表示
                print(f"Paragraph parse error: {e}")
                continue
    
    # --- フッター: 免責事項 ---
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=6))
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['BodyText'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_JUSTIFY,
        fontName=base_font,
        leading=11
    )
    
    disclaimer_text = """
    <b>【免責事項】</b>
    本レポートは情報提供を目的としており、投資勧誘を意図したものではありません。
    投資判断はご自身の責任において行ってください。本レポートの内容に基づいて生じた損害について、当方は一切の責任を負いません。
    データは株・プラスより取得し、AI分析はGoogle Gemini APIを使用しています。
    """
    story.append(Paragraph(disclaimer_text, disclaimer_style))
    
    # PDFを構築
    doc.build(story)
    
    # バッファの先頭に戻して返す
    buffer.seek(0)
    return buffer
