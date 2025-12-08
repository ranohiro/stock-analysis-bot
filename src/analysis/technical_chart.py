# Technical Chart Generator (Middle Panel)
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
    
    mc = mpf.make_marketcolors(
        up='#2f81f7', down='#da3633', # 青/赤
        edge='inherit', wick='inherit',
        volume='in', alpha=1.0
    )
    
    # フォントサイズを全体的に大きく
    rc_params = {
        'font.size': 14,          # 12 -> 14
        'axes.labelsize': 14,     # 12 -> 14
        'axes.titlesize': 18,     # 14 -> 18
        'xtick.labelsize': 12,    # 10 -> 12
        'ytick.labelsize': 12,    # 10 -> 12
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': ':',
        'axes.unicode_minus': False,
        'figure.facecolor': '#0e1117',
        'axes.facecolor': '#161b22',
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
        gridstyle=':',
        facecolor='#161b22',
        figcolor='#0e1117',
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
        ylabel_lower='',
        volume=True,
        volume_panel=1,
        addplot=apd,
        returnfig=True,
        figsize=(16, 10), # 横長すぎると縦がつぶれるので、比率調整 (またはPDF側で合わせる)
        panel_ratios=(6, 1.5, 1.5), # メインパネルを大きく確保
        tight_layout=True,
        datetime_format='%Y/%m/%d',
        xrotation=0,
        scale_padding={'left': 0.5, 'top': 1.0, 'right': 1.2, 'bottom': 1.0}
    )
    
    # --- 軸と見た目の調整 ---
    
    # 全パネルの右軸を有効化
    for ax in axes:
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.grid(True, linestyle=':', alpha=0.3)
    
    # メインパネル (0)
    ax_main = axes[0]
    ax_main.set_ylabel('株価 (円)', rotation=270, labelpad=20, color='#8b949e')
    
    ax_main.yaxis.get_major_locator().set_params(nbins=10)

    # タイトル (PDFヘッダーにあるため削除)
    # title_text = f'{code} - テクニカル分析 (6ヶ月 / 日足)'
    # if font_path:
    #     ax_main.set_title(title_text, fontproperties=fm.FontProperties(fname=font_path), fontsize=16, fontweight='bold', pad=15, color='#e6edf3')
    # else:
    #     ax_main.set_title(f'{code} - Technical Analysis', fontsize=16, fontweight='bold', pad=15, color='#e6edf3')
    pass

    # 価格帯別出来高 (Axis共有)
    ax_volume_profile = ax_main.twiny() 
    ax_volume_profile.set_xlim(0, volume_profile.max() * 5)
    ax_volume_profile.set_zorder(0)
    ax_main.set_zorder(1)
    ax_main.patch.set_visible(False)
    
    price_centers = [interval.mid for interval in volume_profile.index]
    volumes = volume_profile.values
    
    ax_volume_profile.barh(price_centers, volumes, 
                           height=(price_max - price_min) / 30,
                           align='center',
                           color='#6e7681', alpha=0.2) # グレーで見立たなく
    
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
