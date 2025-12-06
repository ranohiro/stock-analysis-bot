import os
import io
import mplfinance as mpf
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

def setup_japanese_font_for_chart():
    """チャートで使用する日本語フォントを設定"""
    try:
        # Macのヒラギノフォントを使用 (Hiragino Sans GB)
        font_path = '/System/Library/Fonts/Hiragino Sans GB.ttc'
        if os.path.exists(font_path):
            # Hiragino Sans GBをmatplotlibに設定
            from matplotlib.font_manager import FontProperties
            font_prop = FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
            return True
    except Exception as e:
        print(f"チャートフォント設定エラー: {e}")
    
    # デフォルトフォント
    plt.rcParams['font.family'] = 'sans-serif'
    return False

def generate_charts(data: pd.DataFrame, code: str) -> dict:
    """
    株価データからローソク足チャートとRSIチャートを生成し、
    高品質な画像をBytesIOで返す。

    Args:
        data: 株価データ (DataFrame, インデックスは日付)
        code: 証券コード

    Returns:
        生成されたチャート画像のバイナリデータとファイル名を含む辞書
    """
    
    # 日本語フォント設定
    setup_japanese_font_for_chart()
    
    # --- 1. RSIの計算 ---
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 14日間の移動平均（Wilder's smoothing）
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()

    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # --- 2. チャート生成 ---
    
    # データを最新の約3ヶ月分に絞る
    plot_data = data.iloc[-90:]

    # RSIサブプロットを作成
    apd = mpf.make_addplot(
        plot_data['RSI'], 
        panel=2, 
        color='#3b82f6',  # より鮮やかな青
        ylabel='RSI (14)',
        secondary_y=False,
        width=1.5
    )

    # チャートのスタイル設定（より洗練されたデザイン）
    mc = mpf.make_marketcolors(
        up='#ef4444',      # 陽線: 赤
        down='#3b82f6',    # 陰線: 青
        edge='inherit',
        wick='inherit',
        volume='in',
        alpha=0.9
    )
    
    s = mpf.make_mpf_style(
        base_mpf_style='yahoo',
        marketcolors=mc,
        gridcolor='#e5e7eb',
        gridstyle='--',
        gridaxis='both',
        facecolor='white',
        figcolor='white',
        rc={
            'font.size': 10,
            'axes.labelsize': 11,
            'axes.titlesize': 13,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'axes.grid': True,
            'grid.alpha': 0.3
        }
    )

    # ファイル名を決定
    filename_candle = f"chart_{code}_{datetime.now().strftime('%Y%m%d')}.png"

    # mplfinanceで描画（高解像度）
    fig, axes = mpf.plot(
        plot_data, 
        type='candle', 
        style=s, 
        title=f'{code} - ローソク足 & RSI (直近3ヶ月)',
        ylabel='株価（円）',
        volume=True,
        addplot=apd,
        returnfig=True,
        figsize=(12, 8),  # サイズを大きく
        panel_ratios=(3, 1, 1),  # パネル比率調整
        tight_layout=True
    )

    # タイトルのフォントサイズ調整
    axes[0].set_title(f'{code} - ローソク足 & RSI (直近3ヶ月)', fontsize=14, fontweight='bold', pad=15)
    
    # RSIの水平線を追加（買われすぎ/売られすぎのライン）
    axes[4].axhline(y=70, color='#ef4444', linestyle='--', linewidth=0.8, alpha=0.6)
    axes[4].axhline(y=30, color='#3b82f6', linestyle='--', linewidth=0.8, alpha=0.6)
    axes[4].set_ylim(0, 100)

    # 画像をメモリに保存（高解像度）
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)  # メモリリーク防止

    return {
        "file": buffer, 
        "filename": filename_candle
    }
