import os
import io
import mplfinance as mpf
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# グローバルにフォントパスを設定
FONT_PATH = None

def setup_japanese_font_for_chart():
    """チャートで使用する日本語フォントを設定"""
    global FONT_PATH
    
    try:
        # IPAゴシックフォントのパスを探す
        font_paths = [
            '~/Library/Fonts/ipag.ttf',
            '/Library/Fonts/ipag.ttf',
            '~/Library/Fonts/IPAGothic.ttc',
            '/Library/Fonts/IPAGothic.ttc'
        ]
        
        for font_path in font_paths:
            expanded_path = os.path.expanduser(font_path)
            if os.path.exists(expanded_path):
                FONT_PATH = expanded_path
                
                # matplotlibのデフォルト設定
                plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け防止
                
                print(f"✅ チャートフォント設定成功: {font_path}")
                return expanded_path
        
        print("⚠️  IPAフォントが見つかりません。デフォルトフォントを使用します。")
    except Exception as e:
        print(f"⚠️  チャートフォント設定エラー: {e}")
    
    plt.rcParams['axes.unicode_minus'] = False
    return None

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
    font_path = setup_japanese_font_for_chart()
    
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
    
    # rcパラメータの設定
    rc_params = {
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 13,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'axes.unicode_minus': False
    }
    
    # フォントパスが見つかった場合は追加
    if font_path:
        rc_params['font.family'] = fm.FontProperties(fname=font_path).get_name()
    
    s = mpf.make_mpf_style(
        base_mpf_style='yahoo',
        marketcolors=mc,
        gridcolor='#e5e7eb',
        gridstyle='--',
        gridaxis='both',
        facecolor='white',
        figcolor='white',
        rc=rc_params
    )

    # ファイル名を決定
    filename_candle = f"chart_{code}_{datetime.now().strftime('%Y%m%d')}.png"

    # mplfinanceで描画（高解像度）
    # titleパラメータを削除（重複を避けるため、axesで設定）
    fig, axes = mpf.plot(
        plot_data, 
        type='candle', 
        style=s, 
        ylabel='株価（円）',
        volume=True,
        addplot=apd,
        returnfig=True,
        figsize=(12, 8),  # サイズを大きく
        panel_ratios=(3, 1, 1),  # パネル比率調整
        tight_layout=True
    )

    # タイトルを設定（チャート上部のみ、画像内には表示しない）
    if font_path:
        axes[0].set_title(f'{code} - ローソク足 & RSI (直近3ヶ月)', 
                         fontproperties=fm.FontProperties(fname=font_path),
                         fontsize=14, fontweight='bold', pad=15)
    else:
        axes[0].set_title(f'{code} - Candlestick & RSI (Last 3 months)', 
                         fontsize=14, fontweight='bold', pad=15)
    
    # RSIの水平線を追加（買われすぎ/売られすぎのライン）
    axes[4].axhline(y=70, color='#ef4444', linestyle='--', linewidth=0.8, alpha=0.6)
    axes[4].axhline(y=30, color='#3b82f6', linestyle='--', linewidth=0.8, alpha=0.6)
    axes[4].set_ylim(0, 100)

    # 画像をメモリに保存（高解像度）
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    
    # 【開発用】デバッグフォルダにも保存
    debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug', 'charts')
    os.makedirs(debug_dir, exist_ok=True)
    debug_path = os.path.join(debug_dir, filename_candle)
    
    try:
        with open(debug_path, 'wb') as f:
            f.write(buffer.getvalue())
        print(f"📊 デバッグチャート保存: {debug_path}")
        buffer.seek(0)  # バッファ位置をリセット
    except Exception as e:
        print(f"⚠️  デバッグチャート保存失敗: {e}")
    
    plt.close(fig)  # メモリリーク防止

    return {
        "file": buffer, 
        "filename": filename_candle
    }
