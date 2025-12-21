import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle
from datetime import datetime, timedelta
import io
import os
import sys

# プロジェクトルートへのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.db_manager import get_connection, get_margin_balance

class SupplyDemandAnalyzer:
    def __init__(self):
        self.conn = get_connection()
        self.font_family = self._setup_font()
        
        # デザインテーマ設定
        self.colors = {
            'bg': '#0e1117',        # 背景: ダークブルー/ブラック
            'panel_bg': '#161b22',  # パネル背景
            'text': '#e6edf3',      # メインテキスト: オフホワイト
            'text_dim': '#8b949e',  # サブテキスト: グレー
            'up': '#f85149',        # 上昇/ポジティブ: 赤 (日本標準)
            'down': '#2f81f7',      # 下落/ネガティブ: 青 (日本標準)
            'blue': '#2f81f7',      # 強調青
            'gold': '#d29922',      # スコア/強調: ゴールド
            'grid': '#30363d',      # グリッド線
            'chart_blue': '#2f81f7', # チャート用青 (変更)
            'chart_red': '#f85149',  # チャート用赤 (変更)
            'chart_orange': '#d19a66', # チャート用オレンジ
            'chart_cyan': '#56d4dd'  # チャート用シアン
        }
        
        # Matplotlibのスタイル設定
        plt.style.use('dark_background')
        plt.rcParams.update({
            'figure.facecolor': self.colors['bg'],
            'axes.facecolor': self.colors['panel_bg'],
            'axes.edgecolor': self.colors['grid'],
            'text.color': self.colors['text'],
            'axes.labelcolor': self.colors['text_dim'],
            'xtick.color': self.colors['text_dim'],
            'ytick.color': self.colors['text_dim'],
            'grid.color': self.colors['grid'],
            'grid.linestyle': ':',
            'font.family': 'sans-serif'
        })
        if self.font_family:
             plt.rcParams['font.sans-serif'] = [self.font_family]

    def _setup_font(self):
        """日本語フォントの設定"""
        # プロジェクト内フォントを最優先
        font_configs = [
            ('./dataset/fonts/ipag.ttf', 'IPAGothic'),
            ('dataset/fonts/ipag.ttf', 'IPAGothic'),
            ('~/Library/Fonts/ipag.ttf', 'IPAGothic'),
            ('/Library/Fonts/ipag.ttf', 'IPAGothic'),
            ('~/Library/Fonts/IPAGothic.ttc', 'IPAGothic'),
            ('/System/Library/Fonts/Hiragino Sans GB.ttc', 'Hiragino Sans GB'),
        ]
        
        for path, family_name in font_configs:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                fm.fontManager.addfont(expanded_path)
                return family_name  # フォントファミリー名を返す
        return None

    # ... (Keep existing methods until plot_analysis) ...

    def plot_analysis(self, code: str, save_path: str = None):
        """プロフェッショナルダッシュボード描画 (PDFレポート用最適化版)"""
        scores, indicators, data, sector_data = self.calculate_score(code)
        if not scores: return None

        prices = data['prices']
        margin = data['margin']
        info = data['info']
        
        # メタデータ計算
        latest = prices.iloc[-1]
        prev = prices.iloc[-2]
        change = latest['close'] - prev['close']
        change_pct = (change / prev['close']) * 100
        
        result_meta = {
            'code': code,
            'name': info['name'],
            'market': info['market'],
            'industry': info['industry'],
            'price': latest['close'],
            'change': change,
            'change_pct': change_pct,
            'score': scores['Total'],
            'date': latest.name.strftime('%Y%m%d') if hasattr(latest.name, 'strftime') else str(latest.name)
        }
        
        
        # 横向き (Landscape) - Full Page 2
        # Maximize height: (25, 18)
        fig = plt.figure(figsize=(25, 18), constrained_layout=False) 
        gs = gridspec.GridSpec(15, 30, figure=fig)
        plt.subplots_adjust(left=0.03, right=0.98, top=0.95, bottom=0.05, wspace=0.3, hspace=0.6)
        
        # Fonts (Scaled up for full page visibility)
        fp = fm.FontProperties(family=self.font_family, size=16) if self.font_family else None
        fp_bold = fm.FontProperties(family=self.font_family, weight='bold', size=16) if self.font_family else None
        fp_title = fm.FontProperties(family=self.font_family, weight='bold', size=20) if self.font_family else None
        fp_small = fm.FontProperties(family=self.font_family, size=12) if self.font_family else None
        fp_num = fm.FontProperties(family=self.font_family, size=20, weight='bold') if self.font_family else None
        
        # === ROW 1: Charts (Height: 0-9) ===
        
        # --- Top Left: Price & Margin (gs 0:9, 0:14) ---
        ax1_p = fig.add_subplot(gs[0:6, 0:14]) 
        ax1_m = fig.add_subplot(gs[6:9, 0:14], sharex=ax1_p)
        
        # Price Chart
        p_data = prices.iloc[-150:]
        width = 0.6; width2 = 0.1
        up = p_data[p_data['close'] >= p_data['open']]
        down = p_data[p_data['close'] < p_data['open']]
        
        ax1_p.bar(up.index, up['close']-up['open'], width, bottom=up['open'], color=self.colors['up'])
        ax1_p.bar(up.index, up['high']-up['close'], width2, bottom=up['close'], color=self.colors['up'])
        ax1_p.bar(up.index, up['open']-up['low'], width2, bottom=up['low'], color=self.colors['up'])
        
        ax1_p.bar(down.index, down['open']-down['close'], width, bottom=down['close'], color=self.colors['down'])
        ax1_p.bar(down.index, down['high']-down['open'], width2, bottom=down['open'], color=self.colors['down'])
        ax1_p.bar(down.index, down['close']-down['low'], width2, bottom=down['low'], color=self.colors['down'])
        
        # MA
        ma25 = prices['close'].rolling(25).mean().iloc[-150:]
        ax1_p.plot(ma25.index, ma25, color=self.colors['gold'], linewidth=2.0, label='MA25')
        
        ax1_p.set_title("◇ 株価 & 信用残推移", fontproperties=fp_title, color=self.colors['gold'], pad=10, loc='left')
        ax1_p.grid(True, alpha=0.2)
        ax1_p.tick_params(labelbottom=False)
        ax1_p.tick_params(axis='y', labelsize=12)
        
        dates = p_data.index
        past_dates = dates - timedelta(days=180)
        past_prices = prices.reindex(past_dates, method='nearest')
        if not past_prices.empty:
            ax1_p.plot(dates, past_prices['high'].values, color=self.colors['text_dim'], linestyle=':', linewidth=1.5, label='期日(180日)')

        ax1_p.legend(loc='upper left', prop=fp_small)

        # Margin Balance
        margin_view = margin.copy()
        margin_view = margin_view[margin_view.index >= p_data.index[0]]
        
        if not margin_view.empty:
            m_idx = margin_view.index
            # Data is already swapped correctly in load_stock_data
            col_buy = 'Buy_Balance'
            col_sell = 'Sell_Balance'
            
            b_bal = margin_view[col_buy] / 1000
            s_bal = margin_view[col_sell] / 1000
            
            # Balance Plot
            # Buy is positive (Up color), Sell is negative (Down color)
            ax1_m.fill_between(m_idx, b_bal, 0, color=self.colors['up'], alpha=0.3, label='買残')
            ax1_m.fill_between(m_idx, 0, -s_bal, color=self.colors['down'], alpha=0.3, label='売残')
            ax1_m.axhline(0, color='gray', linewidth=0.5)
            
            ax1_m.set_ylabel('千株', fontproperties=fp_small, color=self.colors['text'])
            ax1_m.tick_params(axis='y', labelsize=12)
            
            # X-axis cleanup
            tick_interval = max(1, len(p_data) // 6)
            xticks = p_data.index[::tick_interval]
            ax1_m.set_xticks(xticks)
            ax1_m.set_xticklabels([d.strftime('%y/%m') for d in xticks], rotation=0, fontsize=12) # Changed from 9 to 10
            
            # Ratio Calculation & Plot (Right Axis)
            ratios = margin_view['Ratio']
            
            ax1_r = ax1_m.twinx()
            ax1_r.plot(m_idx, ratios, color=self.colors['gold'], linewidth=1.5, linestyle='-', marker='o', markersize=3, label='倍率')
            ax1_r.set_ylabel('倍', fontproperties=fp_small, color=self.colors['gold'])
            ax1_r.tick_params(axis='y', labelcolor=self.colors['gold'], labelsize=12)
            ax1_r.grid(False) 
            
            # Combine Legends
            lines1, labels1 = ax1_m.get_legend_handles_labels()
            lines2, labels2 = ax1_r.get_legend_handles_labels()
            ax1_m.legend(lines1 + lines2, labels1 + labels2, prop=fp_small, loc='upper left', ncol=3)

            ax1_m.grid(True, alpha=0.2)
            
            # Latest Ratio for Meta
            result_meta['margin_ratio_ins'] = ratios.iloc[-1] if not ratios.empty else 0
        else:
            if 'margin_ratio_ins' not in result_meta:
                result_meta['margin_ratio_ins'] = np.nan
            ax1_m.tick_params(axis='y', labelsize=12) # Changed from 12 to 10

        # --- Top Right: Performance & Trading Value (gs 0:9, 16:30) ---
        ax2 = fig.add_subplot(gs[0:6, 16:])
        ax2_b = fig.add_subplot(gs[6:9, 16:])
        
        if sector_data and 'data' in sector_data:
            s_data = sector_data['data'].iloc[-100:]
            base_idx = s_data.index[0]
            x_pos = np.arange(len(s_data.index))

            stock_ret = prices.loc[s_data.index]['close'] / prices.loc[base_idx]['close'] * 100
            sector_ret = s_data['Sector_Idx'] / s_data.loc[base_idx, 'Sector_Idx'] * 100
            topix_ret = s_data['TOPIX_Norm'] / s_data.loc[base_idx, 'TOPIX_Norm'] * 100
            
            sector_name = result_meta.get('industry', '業種')

            ax2.plot(x_pos, stock_ret, color=self.colors['blue'], linewidth=2.0, label=f"{code}")
            ax2.plot(x_pos, sector_ret, color=self.colors['chart_cyan'], linewidth=1.5, linestyle='--', label=f"{sector_name}")
            ax2.plot(x_pos, topix_ret, color=self.colors['text_dim'], linewidth=1.0, linestyle=':', label="TOPIX")
            ax2.set_title("◇ パフォーマンス & 売買代金", fontproperties=fp_title, pad=5, loc='left', color=self.colors['gold'])
            ax2.legend(prop=fp_small, loc='upper left')
            ax2.grid(True, alpha=0.2)
            ax2.set_xticks([])
            ax2.set_xlim(x_pos[0]-1, x_pos[-1]+1)
            ax2.tick_params(axis='y', labelsize=12) # Changed from 9 to 10
            
            stock_tv = prices.loc[s_data.index]['trading_value']
            sector_tv = s_data['section_trading_value']
            
            bar_width = 0.8
            # Ax2_b2 (Right Axis: Sector TV)
            ax2_b2 = ax2_b.twinx()
            ax2_b2.bar(x_pos, sector_tv / 1e9, width=bar_width, color=self.colors['chart_cyan'], alpha=0.3, label=f'{sector_name}(右)', zorder=1)
            ax2_b2.set_ylabel('業種売買代金(十億円)', fontproperties=fp_small, color=self.colors['chart_cyan'])
            ax2_b2.tick_params(axis='y', labelcolor=self.colors['chart_cyan'], labelsize=12) # Changed from 8 to 10

            # Ax2_b (Left Axis: Stock TV)
            ax2_b.bar(x_pos, stock_tv / 1e6, width=bar_width, color='none', edgecolor=self.colors['blue'], linewidth=1.0, label=f'{code}(左)', zorder=2)
            ax2_b.set_ylabel('個別売買代金(百万円)', fontproperties=fp_small, color=self.colors['blue'])
            ax2_b.tick_params(axis='y', labelcolor=self.colors['blue'], labelsize=12) # Changed from 8 to 10
            
            ax2_b.set_zorder(ax2_b2.get_zorder() + 1)
            ax2_b.patch.set_visible(False)
            ax2_b.set_xlim(x_pos[0]-1, x_pos[-1]+1)
            
            # Combine Legends for TV
            h1, l1 = ax2_b.get_legend_handles_labels()
            h2, l2 = ax2_b2.get_legend_handles_labels()
            ax2_b.legend(h1+h2, l1+l2, prop=fp_small, loc='upper left', ncol=2)
            
            tick_interval = max(1, len(s_data.index) // 6)
            ax2_b.set_xticks(x_pos[::tick_interval])
            ax2_b.set_xticklabels([d.strftime('%m/%d') for d in s_data.index[::tick_interval]], rotation=0, fontsize=12) # 10->12
            ax2_b.grid(True, alpha=0.2)
        
        # === ROW 2: Indicators, Radar, Score (Height: 10-15) ===
        
        # --- Bottom Left: Indicators (gs 10:15, 0:14) - Widened for 2 columns ---
        ax3 = fig.add_subplot(gs[10:, 0:14])
        ax3.axis('off')
        ax3.set_title("◇ 需給・環境指標 (詳細)", fontproperties=fp_bold, color=self.colors['gold'], pad=15, loc='center', size=18)
        
        # 10 Key Metrics (5 per column)
        m = indicators
        mp = scores.get('metric_points', {})
        
        # Dynamic Labels
        ind_name = info['industry']
        
        # Truncate long names if needed
        ind_label = ind_name[:5] + ".." if len(ind_name) > 6 else ind_name
        
        # Helper to format score
        def fmt_score(pts):
            if pts > 0: return f"(+{pts})"
            elif pts < 0: return f"({pts})"
            return "(0)"
            
        def fmt_val_normal(val, unit, key):
            """Normal Value (No Score)"""
            s = f"{val:.2f}{unit}" if isinstance(val, (int, float)) and not np.isnan(val) else "-"
            # Score is added in loop, so don't add here to avoid duplicate
            return s
            
        def fmt_flow_val(val, unit, key, consec_key):
            """Flow Value + Consecutive Days + Score"""
            s = f"{val:.2f}{unit}" if isinstance(val, (int, float)) else "-"
            # Only add if consecutive days > 0
            consec = m.get(consec_key, 0) if consec_key else 0
            if consec > 0:
                s += f" (連続{consec}日)"
            return s

        # Format: (Label, Value+Unit, Key, ScoreKey)
        items_left = [
            ("信用倍率", fmt_val_normal(m['margin_ratio'], "倍", 'margin_ratio'), 'margin_ratio'),
            ("信用残売買高レシオ", fmt_val_normal(m['days_to_cover'], "日", 'days_to_cover'), 'days_to_cover'),
            ("回転率", fmt_val_normal(m['turnover_rate'], "%", 'turnover_rate'), 'turnover_rate'),
            (f"【{ind_name}】 騰落率", fmt_val_normal(m['sector_return'], "%", 'sector_return'), 'sector_return'),
            (f"【{ind_name}】 5日/20日売買代金", fmt_flow_val(m['sector_flow_ratio'], "倍", 'sector_flow_ratio', 'sector_flow_consecutive'), 'sector_flow_ratio'),
        ]
        
        items_right = [
            (f"【{code}】 騰落率", fmt_val_normal(m.get('ind_return',0), "%", 'ind_return'), 'ind_return'),
            (f"【{code}】 5日/20日売買代金", fmt_flow_val(m['ind_flow_ratio'], "倍", 'ind_flow_ratio', 'flow_consecutive'), 'ind_flow_ratio'),
            ("MA乖離率", fmt_val_normal(m['ma_deviation'], "%", 'ma_deviation'), 'ma_deviation'),
            ("VWAP乖離率", fmt_val_normal(m['vwap_deviation'], "%", 'vwap_deviation'), 'vwap_deviation'),
            ("25日騰落率 (プライム市場)", fmt_val_normal(m['market_ad_ratio'], "%", 'market_ad_ratio'), 'market_ad_ratio'),
        ]
        
        # Adjust Start Y down to avoid Title overlap (Title is center, but large)
        start_y = 0.78 
        step_y = 0.14 # Tighten spacing (0.20 -> 0.14)
        
        # Left Column (x=0.0-0.45)
        for i, (label, val_str, key) in enumerate(items_left):
            y = start_y - (i * step_y)
            # Label
            ax3.text(0.02, y, label, fontproperties=fp, color=self.colors['text_dim'], ha='left', size=12) 
            # Value
            sc = mp.get(key, 0)
            score_str = fmt_score(sc)
            ax3.text(0.48, y, f"{val_str} {score_str}", fontproperties=fp_bold, color=self.colors['text'], ha='right', size=14) 
            # Divider
            ax3.axhline(y=y-0.08, xmin=0.02, xmax=0.48, color=self.colors['grid'], linewidth=0.5, alpha=0.5)

        # Right Column (x=0.52-1.0)
        for i, (label, val_str, key) in enumerate(items_right):
            y = start_y - (i * step_y)
            ax3.text(0.52, y, label, fontproperties=fp, color=self.colors['text_dim'], ha='left', size=12)
            sc = mp.get(key, 0)
            if key == 'market_ad_ratio' and sc == 0:
                 if m['market_ad_ratio'] > 120: sc = -4 # Manual handling for penalty visibility
            score_str = fmt_score(sc)
            ax3.text(0.98, y, f"{val_str} {score_str}", fontproperties=fp_bold, color=self.colors['text'], ha='right', size=14)
            ax3.axhline(y=y-0.08, xmin=0.52, xmax=0.98, color=self.colors['grid'], linewidth=0.5, alpha=0.5)

        # --- Bottom Center: Calculation Details (gs 10:, 15:24) ---
        # Replaces Radar Chart
        # Widen the area for details (15:27 instead of 15:24)
        ax4 = fig.add_subplot(gs[10:, 15:27])
        ax4.axis('off')
        ax4.set_title("◇ スコア算出過程", fontproperties=fp_bold, color=self.colors['gold'], pad=10, loc='center', size=20) # 1.2x++
        
        details = scores.get('details_list', [])
        if not details:
            details = ["特記事項なし"]
            
        # 2-Column Layout (Wider now)
        col1_x = 0.25
        col2_x = 0.75
        
        start_y = 0.88
        step_y = 0.15 # Increased spacing for larger font
        
        # Split: First 6 lines left, rest right
        split_idx = 7 # Adjust based on content (A+B usually ~7 lines including headers)
        
        for i, d_str in enumerate(details):
            # Determine Column
            if i < split_idx:
                x = col1_x
                y = start_y - (i * step_y)
            else:
                x = col2_x
                y = start_y - ((i - split_idx) * step_y)
                
            # Detect Header
            if d_str.startswith("["):
                d_color = self.colors['gold']
                d_fp = fp_bold
                d_size = 18 # 1.2x++
            else:
                d_color = self.colors['text']
                d_fp = fp
                d_size = 15 # 1.2x++
                if "(+" in d_str: d_color = self.colors['up']
                elif "(-" in d_str: d_color = self.colors['down']
            
            # Check for overflow
            if y < 0: continue
            
            ax4.text(x, y, d_str, fontproperties=d_fp, color=d_color, ha='center', size=d_size)

        # --- Bottom Right: Vertical Score Gauge (gs 10:, 27:) ---
        # Narrower vertical strip
        ax5 = fig.add_subplot(gs[10:, 27:])
        ax5.axis('off')
        
        # Data
        final_score = scores.get('Total', 50) 
        raw_score = scores.get('raw_score', 0)
        assess = scores.get('Assessment', '')
        
        # 1. Assessment (Top)
        assess_short = assess.split(' ')[0] if ' ' in assess else assess # "B" from "B (中立)"
        # Or keep full if fits? Vertical space is ample.
        
        ax5.text(0.5, 0.95, "総合評価", fontproperties=fp, color=self.colors['text_dim'], ha='center', size=14) # 1.2x
        
        assess_color = self.colors['text']
        if "強気" in assess: assess_color = self.colors['up']
        elif "弱気" in assess: assess_color = self.colors['down']
        elif "中立" in assess: assess_color = self.colors['gold']
        
        # HUGE Assessment Text (2.5x)
        ax5.text(0.5, 0.85, assess_short, fontproperties=fp_bold, color=assess_color, ha='center', size=55) # 2.5x (was 24)
        ax5.text(0.5, 0.76, assess.replace(assess_short,'').strip(' ()'), fontproperties=fp, color=assess_color, ha='center', size=11) # "中立"
        
        # 2. Vertical Gauge
        # Position: x=0.35, width=0.3, y=0.1 to 0.75
        g_x = 0.35
        g_w = 0.3
        g_y_start = 0.10
        g_height = 0.60 # Reduced height to make room for huge text
        
        # Draw Background Bar
        rect_bg = Rectangle((g_x, g_y_start), g_w, g_height, 
                           facecolor=self.colors['panel_bg'], edgecolor=self.colors['grid'], linewidth=1, transform=ax5.transAxes)
        # Gradient effect by drawing segments?
        # Simple solid for now.
        rect_fill = Rectangle((g_x, g_y_start), g_w, g_height, 
                           facecolor=self.colors['grid'], alpha=0.5, transform=ax5.transAxes)
        ax5.add_patch(rect_fill)
        
        # Calc Positions
        theo_min = -18.0
        theo_max = 19.5
        score_range = theo_max - theo_min
        
        # Zero Pos
        zero_ratio = (0 - theo_min) / score_range
        zero_y = g_y_start + (g_height * zero_ratio)
        
        # Draw Zero Line
        ax5.plot([g_x, g_x+g_w], [zero_y, zero_y], color=self.colors['text_dim'], linestyle=':', linewidth=1, transform=ax5.transAxes)
        ax5.text(g_x - 0.05, zero_y, "0", color=self.colors['text_dim'], ha='right', va='center', size=11, transform=ax5.transAxes)
        
        # Current Position
        curr_ratio = (raw_score - theo_min) / score_range
        curr_ratio = max(0.0, min(1.0, curr_ratio))
        curr_y = g_y_start + (g_height * curr_ratio)
        
        # Marker (Triangle pointing Left at right edge)
        marker_x = g_x + g_w
        ax5.plot(marker_x, curr_y, marker='<', color=self.colors['gold'], markersize=14, transform=ax5.transAxes, clip_on=False)
        
        # Score Text (Right of marker) - HUGE (2.5x)
        score_label = f"{raw_score:+.1f}"
        ax5.text(marker_x + 0.10, curr_y, score_label, fontproperties=fp_bold, color=self.colors['text'], ha='left', va='center', size=36, transform=ax5.transAxes) # 2.5x
        
        # Max/Min Labels
        ax5.text(g_x + g_w/2, g_y_start + g_height + 0.02, f"Max\n+{theo_max}", color=self.colors['text_dim'], ha='center', va='bottom', size=11, transform=ax5.transAxes)
        ax5.text(g_x + g_w/2, g_y_start - 0.02, f"Min\n{theo_min}", color=self.colors['text_dim'], ha='center', va='top', size=11, transform=ax5.transAxes)

        # Footer (Removed to avoid duplication with PDF Generator)
        # fig.text(0.5, 0.02, f"Generated on {datetime.now().strftime('%Y/%m/%d %H:%M')} | Data Source: Kabu Plus | by Takiさん", 
        #          ha='center', color=self.colors['text_dim'], fontproperties=fp, fontsize=10)

        plt.tight_layout()
        plt.subplots_adjust(left=0.03, right=0.97, top=0.95, bottom=0.05, wspace=0.3, hspace=0.3)
        
        # Save
        try:
            plt.savefig(save_path, dpi=150, facecolor=self.colors['bg'])
            print(f"DEBUG: Saved to {save_path}")
        except Exception as e:
            print(f"ERROR: Failed to save figure: {e}")
        finally:
            plt.close(fig)
            
        return result_meta

    def load_stock_data(self, code: str):
        """データロード (前回と同様)"""
        # 1. 基本情報
        companies_df = pd.read_sql_query("SELECT * FROM companies WHERE code = ?", self.conn, params=[code])
        if companies_df.empty:
            raise ValueError(f"Code {code} not found in companies table.")
        company_info = companies_df.iloc[0]

        # 2. 日足データ (直近1.5年分 - 期日通過ライン用)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=550) 
        date_str = start_date.strftime('%Y%m%d')
        
        prices_df = pd.read_sql_query(
            "SELECT date, open, high, low, close, volume, trading_value FROM daily_prices WHERE code = ? AND date >= ? ORDER BY date",
            self.conn, params=[code, date_str]
        )
        if not prices_df.empty:
            prices_df['date'] = pd.to_datetime(prices_df['date'], format='%Y%m%d')
            prices_df = prices_df.set_index('date')

        # 3. 信用残データ
        margin_df = pd.read_sql_query(
            "SELECT date, sell_balance_total, buy_balance_total, ratio, sell_balance_ins, buy_balance_ins FROM weekly_margin WHERE code = ? AND date >= ? ORDER BY date",
            self.conn, params=[code, date_str]
        )
        if not margin_df.empty:
            margin_df['date'] = pd.to_datetime(margin_df['date'], format='%Y%m%d')
            
            # DBは修正済みなので、正しいマッピングを使用
            # buy_balance_total (DB) → 信用買い残 (Buy_Balance)
            # sell_balance_total (DB) → 信用売り残 (Sell_Balance)
            margin_df['Buy_Balance'] = margin_df['buy_balance_total']
            margin_df['Sell_Balance'] = margin_df['sell_balance_total']
            margin_df['Ratio'] = margin_df['ratio']
            margin_df['Buy_Balance_Ins'] = margin_df['buy_balance_ins']
            margin_df['Sell_Balance_Ins'] = margin_df['sell_balance_ins']
            
            margin_df = margin_df.set_index('date')

        # 4. 財務データ
        financial_df = pd.read_sql_query(
            "SELECT date, shares_outstanding FROM daily_financials WHERE code = ? AND date >= ? ORDER BY date DESC LIMIT 1",
            self.conn, params=[code, date_str]
        )
        
        return {
            'info': company_info,
            'prices': prices_df,
            'margin': margin_df,
            'financial': financial_df.iloc[0] if not financial_df.empty else None
        }

    def analyze_sector(self, target_industry: str):
        """セクター分析"""
        last_date_df = pd.read_sql_query("SELECT MAX(date) as date FROM daily_prices", self.conn)
        if last_date_df.empty or last_date_df.iloc[0]['date'] is None:
            return None
        last_date = last_date_df.iloc[0]['date']
        start_date = (datetime.strptime(last_date, '%Y%m%d') - timedelta(days=100)).strftime('%Y%m%d') # 100日分（約60営業日確保のため）

        # セクターデータ
        query = """
        SELECT p.date, SUM(p.trading_value) as section_trading_value, AVG((p.close - p.open)/p.open) as avg_change_rate
        FROM daily_prices p JOIN companies c ON p.code = c.code
        WHERE c.industry = ? AND p.date >= ? GROUP BY p.date ORDER BY p.date
        """
        sector_df = pd.read_sql_query(query, self.conn, params=[target_industry, start_date])
        
        if sector_df.empty: return None
        sector_df['date'] = pd.to_datetime(sector_df['date'], format='%Y%m%d')
        sector_df = sector_df.set_index('date')

        # モメンタム
        sector_df['TV_MA5'] = sector_df['section_trading_value'].rolling(5).mean()
        sector_df['TV_MA20'] = sector_df['section_trading_value'].rolling(20).mean()
        sector_df['Momentum'] = sector_df['TV_MA5'] / sector_df['TV_MA20']

        # TOPIX (RS用), 対象銘柄平均
        try:
            topix_df = pd.read_sql_query("SELECT date, close FROM daily_indices WHERE code = '0000' AND date >= ? ORDER BY date", self.conn, params=[start_date])
            if not topix_df.empty:
                topix_df['date'] = pd.to_datetime(topix_df['date'], format='%Y%m%d')
                topix_df = topix_df.set_index('date')
                
                combined = sector_df.join(topix_df, rsuffix='_topix')
                # 指数化 (Base=100)
                combined = combined.dropna()
                if not combined.empty:
                    base_idx = combined.index[0]
                    combined['Sector_Idx'] = (1 + combined['avg_change_rate']).cumprod() * 100
                    # TOPIXも100スタートに正規化
                    combined['TOPIX_Norm'] = combined['close'] / combined.loc[base_idx, 'close'] * 100
                    combined['RS'] = combined['Sector_Idx'] / combined['TOPIX_Norm']

                    return {'momentum': sector_df['Momentum'].iloc[-1], 'data': combined}
        except Exception as e:
            print(f"Sector analysis error: {e}")
            
        return {'momentum': sector_df['Momentum'].iloc[-1], 'data': sector_df}

    # ==========================================
    # 投資判断スコアリングロジック v2.0 Implementation
    # ==========================================
    def calculate_score_v2(self, metrics: dict):
        """ユーザー定義のスコアリングロジックV2.0"""
        total_score = 0
        details = []
        metric_points = {} # Key: metric_name, Value: points
        
        # Category Sub-scores (for Radar)
        cat_scores = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

        # Helper to log details
        def add(pts, reason, cat, metric_key=None):
            nonlocal total_score
            total_score += pts
            cat_scores[cat] += pts
            if pts > 0: details.append(f"{reason} (+{pts})")
            elif pts < 0: details.append(f"{reason} ({pts})")
            
            if metric_key:
                metric_points[metric_key] = pts

        # Input Data Mapping (Data Object Simulation)
        class Data:
            def __init__(self, m):
                self.credit_mult = m.get('margin_ratio', 999.0)
                self.credit_days = m.get('days_to_cover', 0.0)
                self.turnover_rate = m.get('turnover_rate', 0.0)
                self.sector_return = m.get('sector_return', 0.0)
                self.ind_return = m.get('ind_return', 0.0)
                self.sector_flow_ratio = m.get('sector_flow_ratio', 1.0)
                self.ind_flow_ratio = m.get('ind_flow_ratio', 1.0)
                self.flow_consecutive = m.get('flow_consecutive', 0)
                self.ma_deviation = m.get('ma_deviation', 0.0)
                self.vwap_deviation = m.get('vwap_deviation', 0.0)
                self.market_ad_ratio = m.get('market_ad_ratio', 100.0)

        data = Data(metrics)
        
        # Initialize default points for all keys to 0
        all_keys = [
            'margin_ratio', 'days_to_cover', 'turnover_rate', 'sector_return', 'sector_flow_ratio',
            'ind_return', 'ind_flow_ratio', 'flow_consecutive', 'ma_deviation', 'vwap_deviation', 'market_ad_ratio'
        ]
        for k in all_keys: metric_points[k] = 0

        # --------------------------------------
        # A. 需給・流動性 (Supply & Demand)
        # --------------------------------------
        # 1. 信用倍率
        if   data.credit_mult < 1.0:  add(2, "信用倍率<1.0倍", 'A', 'margin_ratio') 
        elif data.credit_mult < 3.0:  add(1, "信用倍率<3.0倍", 'A', 'margin_ratio')
        elif data.credit_mult > 10.0: add(-2, "信用倍率>10倍", 'A', 'margin_ratio')

        # 2. 信用残レシオ (回転日数)
        if   data.credit_days < 5.0:  add(1, "回転日数<5日", 'A', 'days_to_cover')
        elif data.credit_days > 20.0: add(-1, "回転日数>20日", 'A', 'days_to_cover')

        # 3. 回転率
        if   data.turnover_rate > 5.0: add(2, "回転率>5%(大商い)", 'A', 'turnover_rate')
        elif data.turnover_rate > 2.0: add(1, "回転率>2%(活況)", 'A', 'turnover_rate')
        elif data.turnover_rate < 0.2: add(-1, "回転率<0.2%(閑散)", 'A', 'turnover_rate')

        # --------------------------------------
        # B. セクターモメンタム (Sector Trend)
        # --------------------------------------
        # 4. セクター資金流入
        if data.sector_flow_ratio >= 1.2:
            add(2, "セクター資金流入", 'B', 'sector_flow_ratio')
        elif data.sector_flow_ratio < 0.8:
            add(-2, "セクター資金流出", 'B', 'sector_flow_ratio')

        # 5. セクターの強さ
        if data.sector_return > 5.0: add(1, "セクター上昇率>5%", 'B', 'sector_return')

        # --------------------------------------
        # C. テクニカル・強さ (Technical)
        # --------------------------------------
        # 6. 個別の資金流入トレンド
        if data.ind_flow_ratio >= 1.5:
             metric_points['ind_flow_ratio'] = 2
             add(2, "個別資金急流入", 'C')
        elif data.ind_flow_ratio >= 1.1:
             if data.flow_consecutive >= 3:
                 metric_points['flow_consecutive'] = 2 
                 add(2, "資金流入トレンド継続", 'C')
             else:
                 metric_points['ind_flow_ratio'] = 1 
                 add(1, "資金流入傾向", 'C')

        # Ind return not explicitly scored in user snippet?
        # User snippet: "ind_return: 個別銘柄騰落率" included in display but NO scoring rule in calculate_score_v2 orig snippet?
        # Orig snippet lines 437-467 didn't use ind_return.
        # Check carefully. "4. セクター騰落... 5. 個別の資金流入...". No "個別騰落" scoring rule.
        # But user wants display. I will leave points as 0.
        # metric_points['ind_return'] is already initialized to 0.

        # 7. VWAP乖離
        if   data.vwap_deviation > 1.0:  add(2, "VWAP上抜け(強気)", 'C', 'vwap_deviation')
        elif data.vwap_deviation > 0:    add(1, "VWAPサポート", 'C', 'vwap_deviation')
        elif data.vwap_deviation < -1.0: add(-2, "VWAP下抜け(弱気)", 'C', 'vwap_deviation')

        # 8. 移動平均線乖離率
        if   data.ma_deviation > 20.0: add(-2, "MA乖離過熱", 'C', 'ma_deviation')
        elif data.ma_deviation > 0:    add(1, "MA上昇トレンド", 'C', 'ma_deviation')

        # --------------------------------------
        # D. 地合いフィルター (Market Filter)
        # --------------------------------------
        final_decision = ""
        m_score = 0
        if 80 <= data.market_ad_ratio <= 110:
            m_score = 5 
            final_decision = "【順行】地合い良好"
        elif 70 <= data.market_ad_ratio <= 120:
             m_score = 4 
             final_decision = "【中立】地合い中立"
        elif data.market_ad_ratio < 70:
            m_score = 2 
            final_decision = "【警戒】全体相場底値圏"
        elif data.market_ad_ratio > 120:
            m_score = 1 
            final_decision = "【危険】全体相場過熱"
            total_score -= 3 
            details.append("地合い過熱(-3)")
            metric_points['market_ad_ratio'] = -3
        
        cat_scores['D'] = m_score
        
        # Ensure market score (non-penalty part) is not stored in metric_points 
        # because metric_points tracks 'Additions to Total Score'.
        # Market AD only subtracts if overheated.
        # But user wants to see 'Score' for Market? No, 'Points'.
        # So 0 is correct if not penalized.
        
        return total_score, details, final_decision, cat_scores, metric_points

    def load_stock_data(self, code: str):
        """データロード (V2.1: Margin Limit=60)"""
        # 1. 基本情報
        companies_df = pd.read_sql_query("SELECT * FROM companies WHERE code = ?", self.conn, params=[code])
        if companies_df.empty:
            raise ValueError(f"Code {code} not found in companies table.")
        company_info = companies_df.iloc[0]

        # 2. 日足データ (直近1.5年分 - 期日通過ライン用)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=550) 
        date_str = start_date.strftime('%Y%m%d')
        
        prices_df = pd.read_sql_query(
            "SELECT date, open, high, low, close, volume, trading_value FROM daily_prices WHERE code = ? AND date >= ? ORDER BY date",
            self.conn, params=[code, date_str]
        )
        if not prices_df.empty:
            prices_df['date'] = pd.to_datetime(prices_df['date'], format='%Y%m%d')
            prices_df = prices_df.set_index('date').sort_index()

        # 3. 信用残データ (V2.1: Limit=60 for Z-Score)
        margin_df = get_margin_balance(code, limit=60)
        
        # Explicitly map columns if needed (assuming DB Manager returns standard DF)
        if not margin_df.empty:
             # DBは修正済みなので、そのまま使用（スワップ不要）
             # データはload_stock_dataで正しくマッピング済み
             
             # Ratioの整合性確認（念のため）
             if 'Buy_Balance' in margin_df.columns and 'Sell_Balance' in margin_df.columns:
                  # Avoid division by zero
                  mask = margin_df['Sell_Balance'] > 0
                  margin_df.loc[mask, 'Ratio'] = margin_df.loc[mask, 'Buy_Balance'] / margin_df.loc[mask, 'Sell_Balance']
                  margin_df.loc[~mask, 'Ratio'] = 999.0
             pass

        # 4. 決算・財務情報
        fin_df = pd.read_sql_query("SELECT * FROM daily_financials WHERE code = ? ORDER BY date DESC LIMIT 1", self.conn, params=[code])
        financial_data = fin_df.iloc[0] if not fin_df.empty else None

        return {
            'prices': prices_df,
            'margin': margin_df,
            'info': company_info,
            'financial': financial_data
        }

    def calculate_indicators(self, data: dict, sector_data: dict = None):
        """指標計算 (V2.1対応: Credit Z-Score追加)"""
        prices = data['prices']
        margin = data['margin']
        financial = data['financial']
        if prices.empty: return {}
        
        latest_price = prices.iloc[-1]
        p_len = len(prices)
        
        # 1. 信用倍率 & 信用残売買高レシオ & Z-Score
        margin_ratio = 999.0
        credit_days = 0.0
        credit_z_score = 0.0
        
        if not margin.empty:
            last_m = margin.iloc[-1]
            last_buy = last_m.get('Buy_Balance', 0)
            last_sell = last_m.get('Sell_Balance', 0)
            if last_sell > 0:
                margin_ratio = last_buy / last_sell
            else:
                 margin_ratio = 999.0 
            
            # Credit Days
            avg_vol_25 = prices['volume'].tail(25).mean() if p_len >= 25 else prices['volume'].mean()
            if avg_vol_25 > 0:
                credit_days = last_buy / avg_vol_25
                
            # Z-Score (Past 6 months = 26 weeks)
            if len(margin) >= 2:
                # Use tail(26)
                hist_ratios = margin['Ratio'].tail(26)
                mean_r = hist_ratios.mean()
                std_r = hist_ratios.std()
                if std_r > 0:
                    current_r = margin_ratio
                    credit_z_score = (current_r - mean_r) / std_r

        # 2. 回転率
        turnover_rate = 0.0
        shares_out = 0
        if financial is not None:
             shares_out = financial.get('shares_outstanding', 0)
             
        if shares_out > 0:
            turnover_rate = (latest_price['volume'] / shares_out) * 100
        
        # 3. 騰落率 (20日)
        ind_return = 0.0
        if p_len >= 20:
            prev_20 = prices.iloc[-20]
            if prev_20['close'] > 0:
                ind_return = ((latest_price['close'] - prev_20['close']) / prev_20['close']) * 100
        
        # 4. セクター
        sector_return = 0.0
        sector_flow_ratio = 1.0
        sector_flow_consecutive = 0
        
        if sector_data and 'data' in sector_data:
             s_df = sector_data['data']
             if not s_df.empty and len(s_df) >= 20:
                # Sector Return (Using Sector_Idx calculated in analyze_sector)
                curr_idx = s_df['Sector_Idx'].iloc[-1]
                prev_idx = s_df['Sector_Idx'].iloc[-20]
                sector_return = ((curr_idx - prev_idx) / prev_idx) * 100
                
                # Sector Flow Ratio
                s_df['TV_MA5'] = s_df['section_trading_value'].rolling(5).mean()
                s_df['TV_MA20'] = s_df['section_trading_value'].rolling(20).mean()
                s_df['Flow_Ratio'] = s_df['TV_MA5'] / s_df['TV_MA20']
                
                if not s_df['Flow_Ratio'].empty:
                    sector_flow_ratio = s_df['Flow_Ratio'].iloc[-1]
                    
                    # Sector Consecutive
                    check_high = (sector_flow_ratio >= 1.0)
                    consecutive = 0
                    vals = s_df['Flow_Ratio'].fillna(1.0).values
                    for r in reversed(vals):
                        if check_high:
                            if r >= 1.0: consecutive += 1
                            else: break
                        else:
                            if r < 1.0: consecutive += 1
                            else: break
                    sector_flow_consecutive = consecutive

        # 5. 個別資金 (倍率)
        ind_flow_ratio = 1.0
        flow_consecutive = 0
        
        # Calculate Flow (TV MA5/MA20)
        # DB 'trading_value' is in 1000s Yen usually on classic systems (Kabu+ specific?)
        # But Ratio is unitless so it doesn't matter.
        prices['tv_ma5'] = prices['trading_value'].rolling(5).mean()
        prices['tv_ma20'] = prices['trading_value'].rolling(20).mean()
        prices['flow_ratio'] = prices['tv_ma5'] / prices['tv_ma20']
        
        if not prices['flow_ratio'].empty:
            ind_flow_ratio = prices['flow_ratio'].iloc[-1]
            check_high = (ind_flow_ratio >= 1.0)
            consecutive = 0
            vals = prices['flow_ratio'].fillna(1.0).values
            for r in reversed(vals):
                if check_high:
                    if r >= 1.0: consecutive += 1
                    else: break
                else:
                    if r < 1.0: consecutive += 1
                    else: break
            flow_consecutive = consecutive

        # 6. MA乖離
        ma_deviation = 0.0
        if p_len >= 25:
             ma25 = prices['close'].tail(25).mean()
             if ma25 > 0:
                 ma_deviation = ((latest_price['close'] - ma25) / ma25) * 100
        
        # 7. VWAP乖離
        # VWAP = TradingValue / Volume
        # IMPORTANT: DB trading_value is in 1000s Yen. Volume is in Shares.
        # Need to multiply TV by 1000.
        vwap_deviation = 0.0
        if latest_price['volume'] > 0:
            vwap = (latest_price['trading_value'] * 1000) / latest_price['volume']
            if vwap > 0:
                vwap_deviation = ((latest_price['close'] - vwap) / vwap) * 100

        # 8. 市場騰落 (Prime Only)
        from src.core.db_manager import get_market_advance_decline
        ad_df = get_market_advance_decline(limit=25, market_filter='東証PR')
        market_ad_ratio = 100.0
        if not ad_df.empty:
            sum_up = ad_df['up_count'].sum()
            sum_down = ad_df['down_count'].sum()
            if sum_down > 0:
                market_ad_ratio = (sum_up / sum_down) * 100

        metrics = {
            'margin_ratio': margin_ratio,
            'credit_z_score': credit_z_score,
            'days_to_cover': credit_days,
            'turnover_rate': turnover_rate,
            'sector_return': sector_return,
            'ind_return': ind_return,
            'sector_flow_ratio': sector_flow_ratio,
            'sector_flow_consecutive': sector_flow_consecutive,
            'ind_flow_ratio': ind_flow_ratio,
            'flow_consecutive': flow_consecutive,
            'ma_deviation': ma_deviation,
            'vwap_deviation': vwap_deviation,
            'market_ad_ratio': market_ad_ratio,
        }
        return metrics

    def calculate_score_v2_1(self, metrics: dict):
        """ユーザー定義スコアリングロジック V2.1 (Weighted + Z-Score)"""
        
        # Metric Points Storage
        metric_points = {}
        all_keys = [
            'margin_ratio', 'days_to_cover', 'turnover_rate', 'sector_return', 'sector_flow_ratio',
            'ind_return', 'ind_flow_ratio', 'flow_consecutive', 'ma_deviation', 'vwap_deviation', 'market_ad_ratio'
        ]
        for k in all_keys: metric_points[k] = 0
        
        details = []
        
        # Helper Class for clean attribute access
        class Data:
            def __init__(self, m):
                self.credit_mult = m.get('margin_ratio', 999.0)
                self.credit_z_score = m.get('credit_z_score', 0.0)
                self.credit_days = m.get('days_to_cover', 0.0)
                self.turnover_rate = m.get('turnover_rate', 0.0)
                self.sector_return = m.get('sector_return', 0.0)
                self.ind_return = m.get('ind_return', 0.0)
                self.sector_flow_ratio = m.get('sector_flow_ratio', 1.0)
                self.ind_flow_ratio = m.get('ind_flow_ratio', 1.0)
                self.flow_consecutive = m.get('flow_consecutive', 0)
                self.ma_deviation = m.get('ma_deviation', 0.0)
                self.vwap_deviation = m.get('vwap_deviation', 0.0)
                self.market_ad_ratio = m.get('market_ad_ratio', 100.0)
        
        data = Data(metrics)
        
        # --- A. 信用バランス (Weight: 1.0) ---
        details.append("[A] 需給・流動性 (x1.0)")
        score_credit = 0
        
        # 1. 信用倍率 (Z-Score)
        z_pts = 0
        if data.credit_z_score <= -1.5: 
            z_pts = 3
            details.append(f"  信用倍率:解消(Z≦-1.5) (+{z_pts})")
        elif data.credit_z_score <= -0.5:
            z_pts = 1
            details.append(f"  信用倍率:好転(Z≦-0.5) (+{z_pts})")
        elif data.credit_z_score >= 1.5:
            z_pts = -2
            details.append(f"  信用倍率:過熱(Z≧1.5) ({z_pts})")
        else:
            details.append(f"  信用倍率:中立 (+{z_pts})")
        
        score_credit += z_pts
        metric_points['margin_ratio'] = z_pts
        
        # 2. 信用回転日数
        d_pts = 0
        if data.credit_days < 5.0:
            d_pts = 1
            details.append(f"  回転日数<5日 (+{d_pts})")
        elif data.credit_days > 20.0:
            d_pts = -1
            details.append(f"  回転日数>20日 ({d_pts})")
        else:
            details.append(f"  回転日数:標準 (+{d_pts})")
            
        score_credit += d_pts
        metric_points['days_to_cover'] = d_pts
        
        # 3. 回転率
        t_pts = 0
        if data.turnover_rate > 5.0:
            t_pts = 2
            details.append(f"  回転率>5% (+{t_pts})")
        elif data.turnover_rate > 2.0:
            t_pts = 1
            details.append(f"  回転率>2% (+{t_pts})")
        elif data.turnover_rate < 0.2:
            t_pts = -1
            details.append(f"  回転率<0.2% ({t_pts})")
        else:
            details.append(f"  回転率:普通 (+{t_pts})")
            
        score_credit += t_pts
        metric_points['turnover_rate'] = t_pts
        
        
        # --- B. セクターモメンタム (Weight: 2.0) ---
        details.append("[B] セクター (x2.0)")
        score_sector = 0
        
        # 4. 業種別資金流入 (Sector Flow)
        sf_pts = 0
        if data.sector_flow_ratio >= 1.2:
            sf_pts = 2
            details.append(f"  業種別資金流入 (+{sf_pts})")
        elif data.sector_flow_ratio < 0.8:
            sf_pts = -2
            details.append(f"  業種別資金流出 ({sf_pts})")
        else:
            details.append(f"  業種別資金:中立 (+{sf_pts})")
            
        score_sector += sf_pts
        metric_points['sector_flow_ratio'] = sf_pts
        
        # 5. 騰落率 (Sector Return)
        sr_pts = 0
        if data.sector_return > 5.0:
            sr_pts = 1
            details.append(f"  業種騰落率:好調 (+{sr_pts})")
        else:
            details.append(f"  業種騰落率:中立 (+{sr_pts})")
            
        score_sector += sr_pts
        metric_points['sector_return'] = sr_pts
        
        
        # --- C. テクニカル (Weight: 1.5) ---
        details.append("[C] テクニカル (x1.5)")
        score_tech = 0
        
        # 6. 個別の資金流入 (Ind Flow)
        if_pts = 0
        if data.ind_flow_ratio >= 1.5:
            if_pts = 2
            details.append(f"  個別資金急増 (+{if_pts})")
        elif data.ind_flow_ratio >= 1.1:
            if data.flow_consecutive >= 3:
                if_pts = 2
                details.append(f"  資金流入継続 (+{if_pts})")
            else:
                if_pts = 1
                details.append(f"  資金流入傾向 (+{if_pts})")
        else:
             details.append(f"  個別資金:中立 (+{if_pts})")
        
        score_tech += if_pts
        metric_points['ind_flow_ratio'] = if_pts
        
        # 7. VWAP乖離率
        v_pts = 0
        if data.vwap_deviation > 1.0:
            v_pts = 2
            details.append(f"  VWAP乖離:上抜け (+{v_pts})")
        elif data.vwap_deviation > 0:
            v_pts = 1
            details.append(f"  VWAP乖離:サポート (+{v_pts})")
        elif data.vwap_deviation < -1.0:
            v_pts = -2
            details.append(f"  VWAP乖離:下抜け ({v_pts})")
        else:
            details.append(f"  VWAP乖離:中立 ({v_pts})")
            
        score_tech += v_pts
        metric_points['vwap_deviation'] = v_pts
        
        # 8. MA乖離率
        m_pts = 0
        if data.ma_deviation > 20.0:
            m_pts = -2
            details.append(f"  MA乖離:過熱 ({m_pts})")
        elif data.ma_deviation > 0:
            m_pts = 1
            details.append(f"  MA乖離:上昇 ({m_pts})")
        else:
            details.append(f"  MA乖離:下降/中立 ({m_pts})")
            
        score_tech += m_pts
        metric_points['ma_deviation'] = m_pts
        
        
        # --- Total Calculation ---
        WEIGHT_CREDIT = 1.0
        WEIGHT_SECTOR = 2.0
        WEIGHT_TECH = 1.5
        
        raw_total = (score_credit * WEIGHT_CREDIT) + \
                    (score_sector * WEIGHT_SECTOR) + \
                    (score_tech * WEIGHT_TECH)
                    
        # --- Market Penalty ---
        # 25-day AD Ratio > 120% -> -4.0 pts
        final_score = raw_total
        if data.market_ad_ratio > 120:
             final_score -= 4.0
             details.append("[D] 地合い過熱 (-4.0)")
        
        # Scaling to 0-100 Range (Exact Mapping)
        # Theoretical Range:
        # Max: A(6) + B(6) + C(7.5) + D(0) = 19.5
        # Min: A(-4) + B(-4) + C(-6) + D(-4) = -18.0
        
        THEORETICAL_MAX = 19.5
        THEORETICAL_MIN = -18.0
        SCORE_RANGE = THEORETICAL_MAX - THEORETICAL_MIN
        
        # Linear Mapping
        if SCORE_RANGE > 0:
            scaled_score = ((final_score - THEORETICAL_MIN) / SCORE_RANGE) * 100
        else:
            scaled_score = 50 # Fallback
            
        scaled_score = max(0, min(100, int(scaled_score)))
        
        # Assessment
        assessment = "中立"
        if scaled_score >= 80: assessment = "S (強気)" # Top 20%
        elif scaled_score >= 60: assessment = "A (やや強気)" # 60-80%
        elif scaled_score >= 40: assessment = "B (中立・保ち合い)" # 40-60%
        elif scaled_score >= 20: assessment = "C (やや弱気)" # 20-40%
        else: assessment = "D (弱気・要警戒)" # Bottom 20%
        
        cat_scores = {'A': score_credit, 'B': score_sector, 'C': score_tech, 'D': 0}
        
        return final_score, details, assessment, cat_scores, metric_points

    def calculate_score(self, code: str):
        """分析実行のメインメソッド (V2.1統合)"""
        data = self.load_stock_data(code)
        company_info = data['info']
        
        sector_data = self.analyze_sector(company_info['industry'])
        
        # Calculate Indicators V2.1
        indicators = self.calculate_indicators(data, sector_data)
        
        # Calculate Score V2.1
        score, details, assessment, cat_scores, metric_points = self.calculate_score_v2_1(indicators) # V2.1 call
        
        # Re-calc scaled score for dict (Consistency)
        THEORETICAL_MAX = 19.5
        THEORETICAL_MIN = -18.0
        scaled_score = ((score - THEORETICAL_MIN) / (THEORETICAL_MAX - THEORETICAL_MIN)) * 100
        scaled_score = max(0, min(100, int(scaled_score)))
        
        scores = {
            'Total': scaled_score,
            'A': cat_scores['A'],
            'B': cat_scores['B'],
            'C': cat_scores['C'],
            'D': cat_scores['D'],
            'Assessment': assessment,
            'details_list': details,
            'raw_score': score, # Weighted Raw Score
            'market_ad_ratio': indicators['market_ad_ratio'],
            'metric_points': metric_points
        }
        
        return scores, indicators, data, sector_data



    def _plot_radar_chart(self, ax, scores, fp):
        labels = ['セクター', '信用需給', '実需', '特殊要因']
        values = [scores['Sector'], scores['Margin'], scores['Trend'], scores['Special']]
        max_values = [30, 40, 20, 10]
        
        # 正規化
        norm_values = [v / m * 100 for v, m in zip(values, max_values)]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        norm_values += norm_values[:1]
        angles += angles[:1]
        
        ax.plot(angles, norm_values, color=self.colors['gold'], linewidth=2)
        ax.fill(angles, norm_values, color=self.colors['gold'], alpha=0.3)
        
        ax.set_xticks(angles[:-1])
        # PADDING increased to prevent custom overlap
        # Resize from 12 to 14/16
        ax.set_xticklabels(labels, fontproperties=fp, fontsize=16, color=self.colors['text_dim'])
        ax.tick_params(pad=18) # Move labels further out
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels([])
        ax.grid(True, color=self.colors['grid'])
        ax.spines['polar'].set_visible(False)
        ax.set_facecolor(self.colors['panel_bg'])

if __name__ == '__main__':
    analyzer = SupplyDemandAnalyzer()
    analyzer.plot_analysis('7203', 'debug/analysis/dashboard_7203.png')
