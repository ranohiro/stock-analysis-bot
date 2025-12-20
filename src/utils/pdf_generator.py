import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable

# Colors (Dark Theme)
BG_COLOR = colors.HexColor('#0e1117')
PANEL_BG = colors.HexColor('#161b22')
TEXT_MAIN = colors.HexColor('#e6edf3')
TEXT_DIM = colors.HexColor('#8b949e')
ACCENT_BLUE = colors.HexColor('#2f81f7')
ACCENT_RED = colors.HexColor('#da3633')
ACCENT_GOLD = colors.HexColor('#d29922')

def setup_japanese_font():
    """日本語フォントの設定"""
    # プロジェクト内フォントを最優先、次にユーザー環境、最後にLinuxシステムフォント
    font_paths = [
        './dataset/fonts/ipag.ttf',  # プロジェクト内（最優先）
        'dataset/fonts/ipag.ttf',     # 相対パス別パターン
        '~/Library/Fonts/ipag.ttf',  # Mac user fonts
        '/Library/Fonts/ipag.ttf',    # Mac system fonts
        '/usr/share/fonts/ipa-gothic/ipag.ttf',  # Oracle Linux / RHEL
        '/usr/share/fonts/japanese/TrueType/ipag.ttf',  # Debian / Ubuntu
        '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',  # Generic Linux
    ]
    for path in font_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            try:
                pdfmetrics.registerFont(TTFont('Japanese', expanded_path))
                # Boldがない場合はNormalを代用（ReportLabは自動で太字化しないため、本来は別ファイルが必要だが、今回は代用）
                pdfmetrics.registerFont(TTFont('JapaneseBold', expanded_path)) 
                return True
            except:
                continue
    return False

def on_page(canvas, doc):
    """ページ背景を描画"""
    canvas.saveState()
    canvas.setFillColor(BG_COLOR)
    # Landscape A4: Width=297mm (842pt), Height=210mm (595pt)
    width, height = landscape(A4)
    canvas.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Footer removed from here to avoid duplication on every page.
    # Added to story end instead.
    
    canvas.restoreState()

def generate_pdf_report(
    meta_data: dict,      # {code, name, market, industry, price, change, change_pct, score, date}
    chart_image: io.BytesIO,
    dashboard_image: io.BytesIO
) -> io.BytesIO:
    
    font_available = setup_japanese_font()
    bold_font = 'JapaneseBold' if font_available else 'Helvetica-Bold'
    base_font = 'Japanese' if font_available else 'Helvetica'

    buffer = io.BytesIO()
    # 横向き (Landscape) - Single Page Layout
    # Margins minimized to 5mm for maximum chart area
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=5*mm,
        bottomMargin=5*mm,
        leftMargin=5*mm,
        rightMargin=5*mm
    )
    
    story = []
    
    # === Compact Header ===
    # ... (Header code remains mostly same, just ensuring compact)
    code = meta_data.get('code', '0000')
    name = meta_data.get('name', 'Unknown')
    market = meta_data.get('market', '-')
    industry = meta_data.get('industry', '-')
    price = meta_data.get('price', 0)
    change = meta_data.get('change', 0)
    change_pct = meta_data.get('change_pct', 0)
    price_date = meta_data.get('date', None)
    
    if price_date:
        try:
            date_obj = datetime.strptime(str(price_date), '%Y%m%d')
            date_str = date_obj.strftime('%Y/%m/%d')
        except:
            date_str = str(price_date)
    else:
        date_str = "-"

    # Styles
    title_style = ParagraphStyle('T', fontName=bold_font, fontSize=18, textColor=TEXT_MAIN)
    # Info Style Increased to 14 (User Request: "Like this" -> Bigger)
    info_style = ParagraphStyle('I', fontName=base_font, fontSize=14, textColor=TEXT_DIM) 
    price_style = ParagraphStyle('P', fontName=bold_font, fontSize=20, textColor=TEXT_MAIN, alignment=TA_RIGHT)
    
    color_hex = '#ef4444' if change >= 0 else '#3b82f6' 
    sign = '+' if change >= 0 else ''
    change_style = ParagraphStyle('C', fontName=bold_font, fontSize=14, textColor=colors.HexColor(color_hex), alignment=TA_RIGHT)

    # Content
    p_left_top = Paragraph(f"<font size=14 color='#8b949e'>{code}</font>  {name}", title_style)
    p_left_bot = Paragraph(f"{market} | {industry}", info_style)
    # Date Size Increased to 14
    p_right_top = Paragraph(f"¥{price:,.0f} <font size=14 color='#8b949e'>({date_str})</font>", price_style)
    p_right_bot = Paragraph(f"{sign}{change:,.0f} ({sign}{change_pct:.2f}%)", change_style)
    
    data = [
        [p_left_top, p_right_top],
        [p_left_bot, p_right_bot]
    ]
    t = Table(data, colWidths=[180*mm, 100*mm], rowHeights=[9*mm, 7*mm]) # Slightly taller row for fonts
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#30363d'), spaceBefore=1, spaceAfter=2))

    # === Technical Chart (Page 1) ===
    chart_image.seek(0)
    # Page 1: Header takes ~25mm. Available ~185mm. 
    # Use 165mm to be safe and fill space.
    img_tech = Image(chart_image, width=285*mm, height=165*mm) 
    story.append(img_tech)
    
    # 改ページ
    story.append(PageBreak())
    
    # === Supply-Demand Dashboard (Page 2) ===
    # Page 2: Full availability (200mm). Use 190mm.
    # Title overlay is inside the chart, so we don't need extra text here.
    dashboard_image.seek(0)
    img_dash = Image(dashboard_image, width=285*mm, height=185*mm) # Slightly shorter to fit footer
    story.append(img_dash)
    
    # === Footer (End of Document) ===
    # Only one footer at the end
    footer_text = f"Generated on {datetime.now().strftime('%Y/%m/%d %H:%M')} | Data Source: Kabu Plus | by Takiさん"
    footer_style = ParagraphStyle('F', fontName=base_font, fontSize=10, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(footer_text, footer_style))
    
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer
