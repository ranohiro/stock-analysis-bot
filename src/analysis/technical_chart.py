# Technical Chart Generator (Middle Panel)
import os
import io
import mplfinance as mpf
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np

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

def generate_charts(data: pd.DataFrame, code: str, financial_data: pd.DataFrame = None, margin_data: pd.DataFrame = None) -> dict:
    """
    株価データからローソク足チャートと各種テクニカル指標を生成し、
    高品質な画像をBytesIOで返す。
    """
    
    # 日本語フォント設定
    # ユーザー環境にある ipag.ttf を優先
    font_path = os.path.expanduser('~/Library/Fonts/ipag.ttf')
    if not os.path.exists(font_path):
        # フォールバック
        font_path = setup_japanese_font_for_chart()

    # Column normalization for mplfinance
    rename_map = {
        'date': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 
        'close': 'Close', 'volume': 'Volume'
    }
    data = data.rename(columns=rename_map)
    if 'Date' in data.columns and not isinstance(data.index, pd.DatetimeIndex):
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.set_index('Date')
    
    # --- 1. 移動平均線の計算 ---
    data['MA5'] = data['Close'].rolling(window=5).mean()
    data['MA25'] = data['Close'].rolling(window=25).mean()
    data['MA75'] = data['Close'].rolling(window=75).mean()
    
    # --- 2. ストキャスティクスの計算 ---
    low_min = data['Low'].rolling(window=13).min()
    high_max = data['High'].rolling(window=13).max()
    data['%K'] = 100 * (data['Close'] - low_min) / (high_max - low_min)
    data['%D'] = data['%K'].rolling(window=5).mean()
    data['Slow%D'] = data['%D'].rolling(window=4).mean()

    # --- 3. チャート生成用データ準備 ---
    plot_data = data.iloc[-126:] # 直近6ヶ月
    
    # 価格帯別出来高
    volume_data = data.iloc[-252:]
    price_min = volume_data['Low'].min()
    price_max = volume_data['High'].max()
    price_bins = pd.cut(volume_data['Close'], bins=30) 
    volume_profile = volume_data.groupby(price_bins, observed=False)['Volume'].sum()

    # --- 4. AddPlotの作成 ---
    apd = [
        # 移動平均線
        mpf.make_addplot(plot_data['MA5'], panel=0, color='#2f81f7', width=1.5),  # 青
        mpf.make_addplot(plot_data['MA25'], panel=0, color='#d29922', width=1.5), # ゴールド/橙
        mpf.make_addplot(plot_data['MA75'], panel=0, color='#8b949e', width=1.2), # グレー
        # ストキャスティクス (パネル2: Panel 1 is Volume)
        mpf.make_addplot(plot_data['%K'], panel=2, color='#ef4444', width=1.2, label='%K'),
        mpf.make_addplot(plot_data['%D'], panel=2, color='#3b82f6', width=1.2, label='%D'),
        mpf.make_addplot(plot_data['Slow%D'], panel=2, color='#8b5cf6', width=1.5, label='Slow%D'),
    ]
        
    # チャートスタイル設定
    # SupplyDemandAnalyzerに合わせて色を調整
    # bg: #0e1117, text: #e6edf3, grid: #30363d
    # 日本標準: 陽線(Up)=赤, 陰線(Down)=青
    
    mc = mpf.make_marketcolors(
        up='#ef4444', down='#3b82f6', # 赤/青
        edge='inherit', wick='inherit',
        volume='inherit', alpha=1.0 # volume='inherit'でキャンドル色に合わせる
    )
    
    # フォントサイズを全体的に大きく (User Request: 1.2x - 1.5x)
    rc_params = {
        'font.size': 16,          # 14 -> 16
        'axes.labelsize': 16,     # 14 -> 16
        'axes.titlesize': 20,     # 18 -> 20
        'xtick.labelsize': 14,    # 12 -> 14
        'ytick.labelsize': 15,    # 12 -> 15
        'axes.grid': True,
        'axes.grid.axis': 'y',     # 横線のみ
        'grid.alpha': 0.9,         # 0.7 -> 0.9 (Darker)
        'grid.linewidth': 1.0,     # 0.8 -> 1.0
        'grid.linestyle': '-',     # 実線
        'axes.unicode_minus': False,
        'figure.facecolor': '#000000', # Black
        'axes.facecolor': '#000000',   # Black
        'axes.edgecolor': '#30363d',
        'text.color': '#e6edf3',
        'axes.labelcolor': '#8b949e',
        'xtick.color': '#8b949e',
        'ytick.color': '#8b949e',
        'grid.color': '#30363d'
    }
    
    if os.path.exists(font_path):
        # mplfinance/matplotlib sometimes needs just the font family name
        prop = fm.FontProperties(fname=font_path)
        rc_params['font.family'] = prop.get_name()
    
    s = mpf.make_mpf_style(
        base_mpf_style='nightclouds', # Dark base
        marketcolors=mc,
        gridcolor='#30363d',
        gridstyle='-', # 実線
        facecolor='#000000', # Black
        figcolor='#000000',  # Black
        rc=rc_params
    )

    filename_candle = f"chart_{code}_{datetime.now().strftime('%Y%m%d')}.png"

    # 描画
    # Panel構成: 0=Main, 1=Volume, 2=Stoch
    # 高さ比率でMainを大きくする (圧縮解消)
    fig, axes = mpf.plot(
        plot_data, 
        type='candle', 
        style=s, 
        ylabel='', 
        ylabel_lower='', # Manually adding label later
        volume=True,
        volume_panel=1,
        addplot=apd,
        returnfig=True,
        figsize=(25, 14), # Fill Page 1 (Landscape)
        panel_ratios=(10, 3, 3), # Maintain good proportions
        tight_layout=True,
        datetime_format='%Y/%m/%d',
        xrotation=0,
        scale_padding={'left': 0.5, 'top': 0.2, 'right': 1.0, 'bottom': 0.2} # Increase left padding for labels
    )
    
    # --- 軸と見た目の調整 ---
    # Legend text size
    for ax in axes:
        start, end = ax.get_ylim()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6, prune='both'))
        ax.tick_params(axis='y', labelsize=15) # Larger fonts (explicit)
    
    # 全パネルの共通設定
    for i, ax in enumerate(axes):
        # Make axes transparent so stripes (and figure bg) show through
        ax.patch.set_visible(False) 
        
        # グリッド設定 (横線のみ、実線、適度な間隔)
        ax.grid(True, axis='y', linestyle='-', linewidth=0.8, color='#30363d', alpha=0.9, zorder=1) # Grid zorder=1
        ax.grid(False, axis='x') 
        
        # Y軸の目盛り最適化 (MaxNLocatorで自動調整)
        if i == 0: # Main panel
             ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=10, steps=[1, 2, 5, 10]))
        elif i == 4: # Stoch panel
             ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=4))
        
    
    # メインパネル (0)
    ax_main = axes[0]
    fp_mx = fm.FontProperties(fname=font_path, size=16) if font_path else None
    
    # Rotation 0 (Horizontal)
    # y=1.02 moves it above the axis, or y=0.5 moves it to center side.
    # User said "横向き (Side orientation)". 
    # Usually `rotation=0` + `ha='right'` puts it to the left of axis horizontally.
    ax_main.set_ylabel('株価\n(円)', rotation=0, labelpad=50, y=0.5, va='center', ha='center', color='#8b949e', fontproperties=fp_mx)

    # --- Background Stripes (Separate Axis to fix Z-Order) ---
    # Create an axis BEHIND everything for stripes
    # zorder: ax_bg(0) < ax_vol(1) < ax_main(2)
    ax_bg = fig.add_axes(ax_main.get_position(), sharex=ax_main, sharey=ax_main, frameon=False, zorder=0)
    ax_bg.set_xlim(ax_main.get_xlim())
    ax_bg.set_ylim(ax_main.get_ylim())
    ax_bg.axis('off')
    
    # Draw stripes on ax_bg (Main Panel Background)
    dates = pd.to_datetime(plot_data.index)
    months = dates.to_period('M')
    month_changes = np.where(months[:-1] != months[1:])[0] + 1
    boundaries = [0] + list(month_changes) + [len(dates)]
    
    # Define Stripe Drawing Helper
    def draw_stripes(target_ax):
        for j in range(len(boundaries)-1):
            start = boundaries[j]
            end = boundaries[j+1]
            if j % 2 != 0:
                target_ax.axvspan(start, end, facecolor='#21262d', alpha=0.5, zorder=-10)

    # 1. Main Panel Stripes (on ax_bg)
    draw_stripes(ax_bg)

    # 2. Volume & Stoch Stripes
    # Volume is axes[2], Stoch is axes[4]
    if len(axes) > 2:
        draw_stripes(axes[2])
    if len(axes) > 4:
        draw_stripes(axes[4])

    # --- Volume Axis Scaling & Label (TeX) ---
    vol_max = volume_data['Volume'].max()
    exponent = 0
    if vol_max > 0:
        exponent = int(np.floor(np.log10(vol_max)))
    
    scale_factor = 10 ** exponent
    
    # Use Mathtext for nice superscript without unicode issues
    # e.g. $\times 10^6$
    # Need to assume matplotlib mathtext font works (usually Dejavu Sans).
    # If we use Japanese font property for title, checks if it breaks math.
    # Usually fine to mix.
    vol_label = r'出来高' + '\n' + r'($\times 10^{' + str(exponent) + r'}$)'
    
    ax_vol = axes[2] # Volume Axis Panel
    ax_vol.set_ylabel(vol_label, rotation=0, labelpad=50, y=0.5, va='center', ha='center', color='#8b949e', fontproperties=fp_mx)
    
    class ScaledFormatter(ticker.Formatter):
        def __init__(self, scale):
            self.scale = scale
        def __call__(self, x, pos=None):
            return f"{x/self.scale:.1f}"
            
    ax_vol.yaxis.set_major_formatter(ScaledFormatter(scale_factor))


    # --- Price-by-Volume (Volume Profile) ---
    # Create Axis Middle Layer
    ax_volume_profile = ax_main.twiny() # Twins ax_main position
    ax_volume_profile.set_xlim(0, volume_profile.max() * 5)
    
    # Set Z-Orders
    ax_bg.set_zorder(0)
    ax_volume_profile.set_zorder(1) 
    ax_main.set_zorder(2)
    ax_main.patch.set_visible(False) # Transparent Main
    
    price_centers = [interval.mid for interval in volume_profile.index]
    volumes = volume_profile.values
    
    ax_volume_profile.barh(price_centers, volumes, 
                           height=(price_max - price_min) / 30,
                           align='center',
                           color='#6e7681', alpha=0.5) 
    
    ax_volume_profile.xaxis.set_visible(False)
    for spine in ax_volume_profile.spines.values():
        spine.set_visible(False)

    # 凡例 (Legend) - axes[0]=Main, axes[2]=Volume, axes[4]=Stoch (because margin panel was removed)
    # Check axes length just in case
    # With 3 panels (Main, Vol, Stoch):
    # axes[0]: Main
    # axes[1]: Main Twin (if any) - mpf might create for secondary y
    # axes[2]: Volume ? Let's check logic.
    # Usually: Panel 0 -> axes[0], axes[1](secondary)
    # Panel 1 -> axes[2], axes[3]
    # Panel 2 -> axes[4], axes[5]
    
    # ストキャスの凡例 (Panel 2)
    # index 4 should be Stoch main axis
    if len(axes) > 4:
        stoch_handles, stoch_labels = axes[4].get_legend_handles_labels()
        if stoch_handles:
            axes[4].legend(stoch_handles, stoch_labels, loc='upper left', fontsize='small', facecolor='#161b22', edgecolor='#30363d', labelcolor='#e6edf3')

    # ストキャス基準線
    if len(axes) > 4:
        axes[4].axhline(y=80, color='#ef4444', linestyle=':', linewidth=1)
        axes[4].axhline(y=20, color='#3b82f6', linestyle=':', linewidth=1)
        axes[4].set_ylim(0, 100)

    # 保存
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='#0e1117')
    buffer.seek(0)
    
    plt.close(fig)

    return {
        "file": buffer, 
        "filename": filename_candle
    }
