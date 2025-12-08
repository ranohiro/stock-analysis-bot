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
from src.core.db_manager import get_connection

class SupplyDemandAnalyzer:
    def __init__(self):
        self.conn = get_connection()
        self.font_path = self._setup_font()
        
        # デザインテーマ設定
        self.colors = {
            'bg': '#0e1117',        # 背景: ダークブルー/ブラック
            'panel_bg': '#161b22',  # パネル背景
            'text': '#e6edf3',      # メインテキスト: オフホワイト
            'text_dim': '#8b949e',  # サブテキスト: グレー
            'up': '#238636',        # 上昇/ポジティブ: 緑
            'down': '#da3633',      # 下落/ネガティブ: 赤
            'blue': '#2f81f7',      # 強調青
            'gold': '#d29922',      # スコア/強調: ゴールド
            'grid': '#30363d',      # グリッド線
            'chart_blue': '#4493f8', # チャート用青
            'chart_red': '#f85149',  # チャート用赤
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
        if self.font_path:
             plt.rcParams['font.sans-serif'] = [os.path.basename(self.font_path)]

    def _setup_font(self):
        """日本語フォントの設定"""
        # User defined priority first
        font_paths = [
            '~/Library/Fonts/ipag.ttf',
            '/Library/Fonts/ipag.ttf',
            '~/Library/Fonts/IPAGothic.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
        ]
        
        for path in font_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                fm.fontManager.addfont(expanded_path)
                return expanded_path
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
            'score': scores['Total']
        }
        
        # キャンバス設定
        fig = plt.figure(figsize=(24, 16)) # サイズを大きくして解像度を稼ぐ
        gs = gridspec.GridSpec(10, 24, figure=fig)
        
        # フォント (さらに大きく)
        # Base size increased significantly
        fp = fm.FontProperties(fname=self.font_path, size=16) if self.font_path else None
        fp_bold = fm.FontProperties(fname=self.font_path, size=20, weight='bold') if self.font_path else None
        fp_small = fm.FontProperties(fname=self.font_path, size=14) if self.font_path else None
        fp_num = fm.FontProperties(fname=self.font_path, size=18, weight='bold') if self.font_path else None
        
        # === 1. パネル1: 株価＆信用残 (左上: 60% Width -> 少し広げる) ===
        # Width: 0-14 (approx 58%) -> 0-15 (62%)
        ax1_p = fig.add_subplot(gs[0:4, 0:15]) 
        ax1_m = fig.add_subplot(gs[4:6, 0:15], sharex=ax1_p)
        
        # 株価チャート
        p_data = prices.iloc[-150:]
        width = 0.6; width2 = 0.1
        up = p_data[p_data['close'] >= p_data['open']]
        down = p_data[p_data['close'] < p_data['open']]
        
        ax1_p.bar(up.index, up['close']-up['open'], width, bottom=up['open'], color=self.colors['blue'])
        ax1_p.bar(up.index, up['high']-up['close'], width2, bottom=up['close'], color=self.colors['blue'])
        ax1_p.bar(up.index, up['open']-up['low'], width2, bottom=up['low'], color=self.colors['blue'])
        
        ax1_p.bar(down.index, down['open']-down['close'], width, bottom=down['close'], color=self.colors['down'])
        ax1_p.bar(down.index, down['high']-down['open'], width2, bottom=down['open'], color=self.colors['down'])
        ax1_p.bar(down.index, down['close']-down['low'], width2, bottom=down['low'], color=self.colors['down'])

        ma5 = p_data['close'].rolling(5).mean()
        ma25 = p_data['close'].rolling(25).mean()
        ax1_p.plot(p_data.index, ma5, color=self.colors['chart_cyan'], linewidth=2.0, label='5MA')
        ax1_p.plot(p_data.index, ma25, color=self.colors['chart_orange'], linewidth=2.0, label='25MA')
        
        dates = p_data.index
        past_dates = dates - timedelta(days=180)
        past_prices = prices.reindex(past_dates, method='nearest')
        if not past_prices.empty:
            ax1_p.plot(dates, past_prices['high'].values, color=self.colors['text_dim'], linestyle=':', linewidth=1.5, label='期日(180日)')

        ax1_p.set_title("株価 & 需給節目", fontproperties=fp_bold, color=self.colors['text'], pad=20)
        ax1_p.legend(loc='upper left', prop=fp_small)
        ax1_p.grid(True, alpha=0.3)
        ax1_p.set_xticks([]) 
        ax1_p.tick_params(axis='y', labelsize=14)

        # 信用残チャート
        m_data = margin[margin.index >= p_data.index[0]]
        if not m_data.empty:
            ax1_m.bar(m_data.index, m_data['Buy_Balance'], color=self.colors['blue'], alpha=0.6, label='買残', width=4)
            ax1_m.bar(m_data.index, -m_data['Sell_Balance'], color=self.colors['down'], alpha=0.6, label='売残', width=4)
            ax1_m.axhline(0, color=self.colors['text_dim'], linewidth=0.5)
            
            ax1_m2 = ax1_m.twinx()
            ax1_m2.plot(m_data.index, m_data['Ratio'], color=self.colors['gold'], linewidth=2.5, label='倍率')
            ax1_m2.axhline(1.0, color='white', linestyle='--', linewidth=1, alpha=0.5)
            
            lines, labels = ax1_m.get_legend_handles_labels()
            lines2, labels2 = ax1_m2.get_legend_handles_labels()
            ax1_m.legend(lines + lines2, labels + labels2, loc='upper left', prop=fp_small)
            ax1_m2.set_yticks([])
            ax1_m.tick_params(axis='y', labelsize=12)

        # === 2. パネル2: セクター比較 (右上) ===
        # Width: 15-24 (Reduced slightly to give space to left) -> 16-24
        ax2 = fig.add_subplot(gs[0:3, 16:])
        ax2_b = fig.add_subplot(gs[3:6, 16:], sharex=ax2)
        
        if sector_data and 'data' in sector_data:
            s_data = sector_data['data'].iloc[-60:]
            if not s_data.empty:
                base_idx = s_data.index[0]
                stock_ret = prices.loc[s_data.index]['close'] / prices.loc[base_idx]['close'] * 100
                sector_ret = s_data['Sector_Idx'] / s_data.loc[base_idx, 'Sector_Idx'] * 100
                topix_ret = s_data['TOPIX_Norm'] / s_data.loc[base_idx, 'TOPIX_Norm'] * 100
                
                ax2.plot(s_data.index, stock_ret, color=self.colors['blue'], linewidth=3.0, label="自社")
                ax2.plot(s_data.index, sector_ret, color=self.colors['chart_cyan'], linewidth=2.0, linestyle='--', label="業種")
                ax2.plot(s_data.index, topix_ret, color=self.colors['text_dim'], linewidth=2.0, linestyle=':', label="TOPIX")
                ax2.set_title("セクター相対比較", fontproperties=fp_bold, pad=20)
                ax2.legend(prop=fp_small)
                ax2.grid(True, alpha=0.3)
                ax2.set_xticks([])
                ax2.tick_params(axis='y', labelsize=14)

                colors = [self.colors['blue'] if v > s_data['section_trading_value'].mean() else self.colors['text_dim'] for v in s_data['section_trading_value']]
                ax2_b.bar(s_data.index, s_data['section_trading_value'], color=colors, alpha=0.7)
                mom = sector_data['momentum']
                mom_color = self.colors['up'] if mom > 1.1 else (self.colors['down'] if mom < 0.9 else self.colors['text'])
                
                # Overlap fix: Move text down or make background clearer
                ax2_b.text(0.05, 0.85, f"強弱感: {mom:.2f}倍", transform=ax2_b.transAxes, color=mom_color, fontproperties=fp_bold, fontsize=16,
                           bbox=dict(facecolor=self.colors['panel_bg'], edgecolor=self.colors['grid'], alpha=0.9))
                ax2_b.tick_params(axis='y', labelsize=12)

        # === 3. パネル3: 指標詳細 (左下: さらに幅を狭め、文字を大きく) ===
        # Width: 0-6 (Narrowed from 0-7)
        ax3 = fig.add_subplot(gs[6:, 0:6])
        ax3.axis('off')
        ax3.set_title("◇ 需給指標", fontproperties=fp_bold, color=self.colors['gold'], pad=15, loc='left')
        
        metrics_list = [
            ("信用倍率", indicators['margin_ratio'], "倍", 1.0, 3.0, True),
            ("回転日数", indicators['days_to_cover'], "日", 5.0, 10.0, True),
            ("滞留玉消化", indicators['days_to_absorb'], "日", 5.0, 10.0, True),
            ("空売比率", indicators['inst_short_ratio']*100, "%", 50, 20, False),
            ("浮動株衝撃", indicators['float_impact']*100, "%", 3.0, 5.0, True),
            ("残/出来高", indicators['margin_vol_ratio'], "倍", 1.0, 3.0, True),
        ]
        
        y_pos = 0.85
        fp_table_name = fm.FontProperties(fname=self.font_path, size=18) if self.font_path else None
        fp_table_val = fm.FontProperties(fname=self.font_path, size=20, weight='bold') if self.font_path else None

        for name, val, unit, th_good, th_bad, lower_is_better in metrics_list:
            is_good = val < th_good if lower_is_better else val > th_good
            is_bad = val > th_bad if lower_is_better else val < th_bad
            val_color = self.colors['blue'] if is_good else (self.colors['down'] if is_bad else self.colors['text'])
            val_str = f"{val:.1f}" if val < 100 else f"{val:.0f}"
            
            # Closer spacing: Name at 0.05, Value at 0.90 (in narrower panel)
            ax3.text(0.05, y_pos, name, fontproperties=fp_table_name, color=self.colors['text_dim'], ha='left', transform=ax3.transAxes)
            ax3.text(0.90, y_pos, f"{val_str}{unit}", fontproperties=fp_table_val, color=val_color, ha='right', transform=ax3.transAxes)
            
            line_y = y_pos - 0.03
            ax3.plot([0.05, 0.95], [line_y, line_y], color=self.colors['grid'], linewidth=1.0, transform=ax3.transAxes)
            
            y_pos -= 0.14
            
        if indicators['is_vol_surge']:
            ax3.text(0.5, y_pos, "★ 出来高急増中!", fontproperties=fp_bold, color=self.colors['gold'], size=18, ha='center', transform=ax3.transAxes)

        # === 4. パネル4: レーダー & 内訳 (中央: さらに左へ) ===
        # Width: 6-11 (Radar) - Shifted left to follow Panel 3
        ax4 = fig.add_subplot(gs[6:, 6:11], polar=True)
        self._plot_radar_chart(ax4, scores, fp) # fp is size 16
        
        # Breakdown: 12-17 (Gap at 11-12)
        ax4_t = fig.add_subplot(gs[6:, 12:17])
        ax4_t.axis('off')
        
        breakdown = [("セクター", scores['Sector'], 30), ("信用需給", scores['Margin'], 40), ("トレンド", scores['Trend'], 20), ("特殊", scores['Special'], 10)]
        y_pos = 0.95
        for name, pts, full in breakdown:
            pct = pts / full
            bar = "■" * int(pct*5) + "□" * (5 - int(pct*5))
            # Even larger fonts
            ax4_t.text(0.0, y_pos, name, fontproperties=fp_table_name, color=self.colors['text_dim'])
            ax4_t.text(0.0, y_pos-0.12, bar, fontproperties=fp, color=self.colors['gold'], size=16)
            ax4_t.text(0.8, y_pos-0.05, f"{pts}", fontproperties=fp_table_val, color=self.colors['text'], ha='right')
            y_pos -= 0.23

        # === 5. パネル5: 総合スコア (右下) ===
        # Width: 18-24 (Shifted left to use space)
        ax5 = fig.add_subplot(gs[6:, 18:])
        ax5.axis('off')
        
        rect = FancyBboxPatch((0.05, 0.1), 0.9, 0.8, boxstyle="round,pad=0.02", 
                              fc=self.colors['panel_bg'], ec=self.colors['gold'], lw=3)
        ax5.add_patch(rect)
        
        ax5.text(0.5, 0.85, "総合スコア", ha='center', fontproperties=fp_bold, color=self.colors['text_dim'], size=16)
        ax5.text(0.5, 0.5, f"{scores['Total']}", ha='center', va='center', fontproperties=fp_bold, color=self.colors['text'], size=56)
        ax5.text(0.5, 0.2, "/ 100", ha='center', fontproperties=fp, color=self.colors['text_dim'], size=16)

        plt.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.05, wspace=0.3, hspace=0.4)

        if save_path:
            plt.savefig(save_path, facecolor=self.colors['bg'], edgecolor='none')
        else:
            plt.show()
            
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
            margin_df = margin_df.rename(columns={
                'sell_balance_total': 'Sell_Balance',
                'buy_balance_total': 'Buy_Balance',
                'ratio': 'Ratio',
                'sell_balance_ins': 'Sell_Balance_Ins',
                'buy_balance_ins': 'Buy_Balance_Ins'
            })
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
        start_date = (datetime.strptime(last_date, '%Y%m%d') - timedelta(days=90)).strftime('%Y%m%d') # 3ヶ月分

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

    def calculate_indicators(self, data: dict):
        """指標計算 (強化版)"""
        prices = data['prices']
        margin = data['margin']
        financial = data['financial']
        if prices.empty: return None
        latest_price = prices.iloc[-1]
        
        # 指標初期化
        metrics = {
            'margin_ratio': 999.0,
            'margin_vol_ratio': 0.0, # 新指標: (買残 - 売残) / 25日平均出来高
            'days_to_cover': 0.0,
            'days_to_absorb': 0.0,
            'inst_short_ratio': 0.0,
            'float_impact': 0.0,
            'is_vol_surge': False,
            'uptrend': False,
            'margin_buy_change': 0.0,
            'credit_date_danger': False # 新指標: 6ヶ月期日警戒
        }

        avg_vol_25 = prices['volume'].rolling(25).mean().iloc[-1]
        avg_vol_5 = prices['volume'].rolling(5).mean().iloc[-1]

        if not margin.empty:
            lm = margin.iloc[-1]
            if lm['Sell_Balance'] > 0:
                metrics['margin_ratio'] = lm['Buy_Balance'] / lm['Sell_Balance']
            
            if avg_vol_25 > 0:
                metrics['margin_vol_ratio'] = (lm['Buy_Balance'] - lm['Sell_Balance']) / avg_vol_25
                metrics['days_to_cover'] = lm['Buy_Balance'] / (avg_vol_25 * 2)
            
            if avg_vol_5 > 0:
                metrics['days_to_absorb'] = lm['Buy_Balance'] / avg_vol_5
                
            if lm['Sell_Balance'] > 0 and 'Sell_Balance_Ins' in lm:
                metrics['inst_short_ratio'] = lm['Sell_Balance_Ins'] / lm['Sell_Balance']
            
            if financial is not None and financial['shares_outstanding'] > 0:
                metrics['float_impact'] = lm['Buy_Balance'] / financial['shares_outstanding']
            
            if len(margin) >= 2:
                metrics['margin_buy_change'] = lm['Buy_Balance'] - margin.iloc[-2]['Buy_Balance']

        # 出来高初動
        if avg_vol_25 > 0:
            metrics['is_vol_surge'] = (latest_price['volume'] / avg_vol_25) > 3.0
            
        # トレンド
        ma5 = prices['close'].rolling(5).mean().iloc[-1]
        ma25 = prices['close'].rolling(25).mean().iloc[-1]
        metrics['uptrend'] = ma5 > ma25

        # 期日警戒フラグ (半年前の高値圏に現在の株価があるか)
        six_months_ago = latest_price.name - timedelta(days=180)
        # 半年前の前後1週間の高値を取得
        past_window = prices[(prices.index >= six_months_ago - timedelta(days=7)) & 
                             (prices.index <= six_months_ago + timedelta(days=7))]
        if not past_window.empty:
            past_high = past_window['high'].max()
            current_price = latest_price['close']
            # 現在値が半年前高値の95%〜105%の範囲にあるなら警戒
            if 0.95 <= (current_price / past_high) <= 1.05:
                metrics['credit_date_danger'] = True

        return metrics

    def calculate_score(self, code: str):
        """スコアリング (ロジック調整済み)"""
        data = self.load_stock_data(code)
        if data['prices'].empty: return None, None, None, None
        
        sector_data = self.analyze_sector(data['info']['industry'])
        indicators = self.calculate_indicators(data)
        
        score = 0
        details = {'Sector': 0, 'Margin': 0, 'Trend': 0, 'Special': 0}

        # A. セクター (Max 30)
        if sector_data and sector_data['momentum'] > 1.2: details['Sector'] = 30
        elif sector_data and sector_data['momentum'] > 1.0: details['Sector'] = 20
        elif sector_data and sector_data['momentum'] > 0.8: details['Sector'] = 10
        score += details['Sector']

        # B. 信用バランス (Max 40)
        ms = 0
        if indicators['margin_ratio'] < 1.0: ms += 20
        elif indicators['margin_ratio'] < 3.0: ms += 15
        
        if indicators['days_to_absorb'] <= 5.0: ms += 10
        if indicators['inst_short_ratio'] >= 0.7: ms += 10
        if indicators['credit_date_danger']: ms -= 5 # 減点要因
        
        details['Margin'] = min(40, max(0, ms))
        score += details['Margin']

        # C. 実需トレンド (Max 20)
        ts = 0
        if indicators['uptrend']:
            if indicators['margin_buy_change'] < 0: ts = 20
            elif indicators['margin_buy_change'] >= 0: ts = 10
        details['Trend'] = ts
        score += details['Trend']

        # D. 特殊 (Max 10)
        ss = 0
        if indicators['is_vol_surge']: ss += 10
        if indicators['float_impact'] < 0.03: ss += 5
        details['Special'] = min(10, ss)
        score += details['Special']

        details['Total'] = score
        return details, indicators, data, sector_data



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
