import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
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
    # ユーザー環境のipag.ttfを最優先
    font_paths = [
        '~/Library/Fonts/ipag.ttf',
        '/Library/Fonts/ipag.ttf',
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
    canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
    canvas.restoreState()

def generate_pdf_report(
    meta_data: dict,      # {code, name, market, industry, price, change, change_pct, score}
    chart_image: io.BytesIO,
    dashboard_image: io.BytesIO
) -> io.BytesIO:
    
    font_available = setup_japanese_font()
    bold_font = 'JapaneseBold' if font_available else 'Helvetica-Bold'
    base_font = 'Japanese' if font_available else 'Helvetica'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=10*mm,
        leftMargin=10*mm,
        rightMargin=10*mm
    )
    
    story = []
    styles = getSampleStyleSheet()

    # === Header Construction ===
    code = meta_data.get('code', '0000')
    name = meta_data.get('name', 'Unknown')
    market = meta_data.get('market', '-')
    industry = meta_data.get('industry', '-')
    price = meta_data.get('price', 0)
    change = meta_data.get('change', 0)
    change_pct = meta_data.get('change_pct', 0)
    
    # Text Styles
    header_title = ParagraphStyle('HT', fontName=bold_font, fontSize=24, textColor=TEXT_MAIN, leading=28)
    header_info = ParagraphStyle('HI', fontName=base_font, fontSize=12, textColor=TEXT_DIM)
    header_price = ParagraphStyle('HP', fontName=bold_font, fontSize=32, textColor=TEXT_MAIN, leading=32)
    
    # Change Color
    color_hex = '#238636' if change >= 0 else '#da3633'
    sign = '+' if change >= 0 else ''
    header_change = ParagraphStyle('HC', fontName=bold_font, fontSize=18, textColor=colors.HexColor(color_hex))

    # Row 1: Code Name | Market Industry
    p_title = Paragraph(f"{name} <font size=16>({code})</font>", header_title)
    p_info = Paragraph(f"{market} | {industry}", header_info)
    
    # Row 2: Price | Change
    p_price = Paragraph(f"¥{price:,.0f}", header_price)
    p_change = Paragraph(f"{sign}{change:,.0f} ({sign}{change_pct:.2f}%)", header_change)
    
    # Table for Header
    # Col 1: Name/Price, Col 2: Info/Change
    # Wait, user wants "Header part... summarized good".
    # Let's put Name/Code on Top. Price/Change below. Industry right aligned?
    # Simple Layout:
    # Left: Name (Large)
    # Below Left: Market/Industry
    # Right: Price (Large)
    # Below Right: Change
    
    data = [
        [p_title, p_price],
        [p_info, p_change]
    ]
    t = Table(data, colWidths=[110*mm, 70*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'), # Price right aligned
        ('RIGHTPADDING', (1,0), (1,-1), 10),
        ('LEFTPADDING', (0,0), (0,-1), 10),
    ]))
    story.append(t)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#30363d'), spaceBefore=5, spaceAfter=10))

    # === Middle: Technical Chart ===
    # User said "Upper section is AI (removed)... stock chart compressed..."
    # Now we have more vertical space.
    section_title = ParagraphStyle('ST', fontName=bold_font, fontSize=14, textColor=ACCENT_BLUE, spaceAfter=5)
    story.append(Paragraph("■ テクニカル分析 (日足 / 6ヶ月)", section_title))
    
    chart_image.seek(0)
    # A4 Height ~297mm. Top/Bot margin 25mm total. Header ~30mm. Available ~240mm.
    # Chart: 100mm, Dashboard: 120mm -> Fits perfectly.
    img_tech = Image(chart_image, width=190*mm, height=110*mm) 
    story.append(img_tech)
    story.append(Spacer(1, 8*mm))

    # === Bottom: Supply-Demand Dashboard ===
    story.append(Paragraph("■ 需給分析ダッシュボード", section_title))
    dashboard_image.seek(0)
    img_dash = Image(dashboard_image, width=190*mm, height=115*mm)
    story.append(img_dash)
    
    # Footer
    story.append(Spacer(1, 5*mm))
    p_foot = Paragraph(f"Generated on {datetime.now().strftime('%Y/%m/%d %H:%M')} | Data Source: Kabu Plus", 
                       ParagraphStyle('F', fontName=base_font, fontSize=8, textColor=colors.grey, alignment=TA_CENTER))
    story.append(p_foot)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer
