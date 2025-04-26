
import sqlite3
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timezone

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeframe', help='Optional: run for one timeframe (e.g. 1m, 3m, 15m, 1h, 1d)')
    parser.add_argument('--weighting', choices=['linear', 'time', 'volume'], help='Optional: weighting method')
    parser.add_argument('--use_atr', action='store_true', help='Use ATR to auto-determine bin width')
    parser.add_argument('--bin_precision', type=int, default=75, help='Number of bins (if not using ATR)')
    parser.add_argument('--debug', action='store_true', help='Debug mode to output to CSV')
    parser.add_argument('--debug_all', action='store_true', help='Include non-recent zones in debug')
    parser.add_argument('--day', help='Day to label output (e.g., 2025-04-04)')
    parser.add_argument('--recent_bars', type=int, default=50, help='Bars to check for zone recency')
    return parser.parse_args()

def load_price_data(conn, tf, start_date, end_date, buffer_bars=500):
    table = f"spx_ohlcv_{tf}"
    # First, get a cutoff timestamp before start_date using a subquery
    lookback_query = f'''
        SELECT timestamp FROM {table}
        WHERE DATE(timestamp) < '{start_date}'
        ORDER BY timestamp DESC LIMIT {buffer_bars}
    '''
    lookback_df = pd.read_sql(lookback_query, conn, parse_dates=["timestamp"])
    if lookback_df.empty:
        lookback_cutoff = start_date + ' 00:00:00'
    else:
        lookback_cutoff = lookback_df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S')

    query = f'''
        SELECT * FROM {table}
        WHERE timestamp >= '{lookback_cutoff}' AND DATE(timestamp) <= '{end_date}'
        ORDER BY timestamp ASC
    '''
    df = pd.read_sql(query, conn, parse_dates=['timestamp'])
    return df
def detect_pivots(data, length):
    highs = data["high"]
    lows = data["low"]
    pivots_high = highs[(highs.shift(length) < highs) & (highs.shift(-length) < highs)]
    pivots_low = lows[(lows.shift(length) > lows) & (lows.shift(-length) > lows)]
    return pivots_high.dropna(), pivots_low.dropna()

def get_weight(data, idx, style):
    if style == "linear":
        return 1
    elif style == "time":
        return idx / len(data)
    elif style == "volume":
        return data.loc[idx, "spy_volume"] if "spy_volume" in data.columns else 1
    return 1

def score_pivots(data, weight_style):
    scores = []
    for length in [5, 10, 20, 50]:
        ph, pl = detect_pivots(data, length)
        for idx in ph.index:
            level = data.loc[idx, "high"]
            score = get_weight(data, idx, weight_style)
            scores.append(("high", idx, level, score))
        for idx in pl.index:
            level = data.loc[idx, "low"]
            score = get_weight(data, idx, weight_style)
            scores.append(("low", idx, level, score))
    return scores

def build_histogram(scores, bin_width=None, bin_count=75):
    levels = [s[2] for s in scores]
    min_price = min(levels)
    max_price = max(levels)
    if bin_width:
        bin_edges = np.arange(min_price, max_price + bin_width, bin_width)
    else:
        bin_edges = np.linspace(min_price, max_price, bin_count)
    hist = np.zeros(len(bin_edges) - 1)
    for _, _, level, weight in scores:
        bin_idx = np.searchsorted(bin_edges, level) - 1
        if 0 <= bin_idx < len(hist):
            hist[bin_idx] += weight
    centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    return centers, hist

def smooth_histogram(hist, window=3):
    return np.convolve(hist, np.ones(window)/window, mode='same')

def detect_peaks(centers, hist, threshold=0.5):
    peaks = []
    for i in range(1, len(hist)-1):
        if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] >= threshold:
            peaks.append((centers[i], hist[i]))
    return peaks

def check_recent_touches(peaks, data, recent_bars=50, proximity=1.0):
    recent_data = data.tail(recent_bars)
    results = []
    if recent_data.empty:
        return [(level, score, None, False) for (level, score) in peaks]
    last_touch_time = recent_data["timestamp"].iloc[-1]
    for level, score in peaks:
        results.append((level, score, last_touch_time, True))
    return results

def ensure_score_column(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if 'score' not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN score REAL")
        conn.commit()

def save_zones(peaks, tf, method, conn, debug=False, debug_file=None, debug_all=False, effective_date=None):
    now = datetime.now(timezone.utc).isoformat()
    zones = []
    for level, score, last_touch, is_recent in peaks:
        if not is_recent and not debug_all:
            continue
        zones.append({
            'zone_level': level,
            'method': method,
            'bounce_count': 0,
            'rounded_level': round(level, 1),
            'method_count': 1,
            'multi_method_overlap': 0,
            'start_time': None,
            'last_touched': str(last_touch) if last_touch else None,
            'touch_count': 0,
            'active': 1,
            'created_at': now,
            'timeframe': tf,
            'score': score,
            'effective_date': effective_date
        })
    df = pd.DataFrame(zones)
    if debug and debug_file:
        if df.empty:
            print(f"[DEBUG] No zones to save for {method} at {tf} on {effective_date}. Writing empty CSV with headers.")
            pd.DataFrame(columns=df.columns).to_csv(debug_file, index=False)
        else:
            df.to_csv(debug_file, index=False)
            print(f"[DEBUG] Zones saved to {debug_file}")
    else:
        if not df.empty:
            table = f"spx_ohlcv_{tf}_sr_zones"
            ensure_score_column(conn, table)
            if 'effective_date' not in df.columns:
                df['effective_date'] = effective_date
            df.to_sql(table, conn, if_exists='append', index=False)
            print(f"[DB] Inserted {len(df)} zones into {table} for {effective_date}")

# These include: load_price_data, detect_pivots, get_weight, score_pivots, build_histogram,
# smooth_histogram, detect_peaks, check_recent_touches, ensure_score_column, save_zones


def get_all_dates(conn, tf):
    table = f"spx_ohlcv_{tf}"
    query = f"SELECT DISTINCT DATE(timestamp) as trade_date FROM {table} ORDER BY trade_date"
    return pd.read_sql(query, conn)["trade_date"].tolist()

def main():
    args = parse_args()
    conn = sqlite3.connect("C:/Projects/Trading/Iron Condor Analysis/Polygon Retrieve/sp_data.sqlite")
    timeframes = ['1m', '3m', '15m', '1h', '1d']
    selected_timeframes = [args.timeframe] if args.timeframe else timeframes
    weightings = [args.weighting] if args.weighting else ['linear', 'time', 'volume']

    for tf in selected_timeframes:
        all_days = [args.day] if args.day else get_all_dates(conn, tf)
        data = load_price_data(conn, tf, min(all_days), max(all_days))
        all_days = [args.day] if args.day else get_all_dates(conn, tf)
        for effective_date in all_days:
            day_data = data[data['timestamp'].dt.date <= pd.to_datetime(effective_date).date()]
            atr = (day_data['high'] - day_data['low']).rolling(14).mean().iloc[-1]

            for weighting in weightings:
                bin_width = atr / 2 if args.use_atr else None
                scores = score_pivots(day_data, weighting)
                centers, hist = build_histogram(scores, bin_width=bin_width, bin_count=args.bin_precision)
                smoothed = smooth_histogram(hist)
                max_score = max(smoothed) if len(smoothed) else 1

                if tf == '1h':
                    peak_threshold = 0.3 * max_score
                elif tf == '1d':
                    peak_threshold = 0.4 * max_score
                elif tf == '15m':
                    peak_threshold = 0.25 * max_score
                else:
                    peak_threshold = 0.2 * max_score

                peaks = detect_peaks(centers, smoothed, threshold=peak_threshold)
                peaks = check_recent_touches(peaks, data, recent_bars=args.recent_bars)
                debug_file = f"zones_debug_pivot_{effective_date}_{tf}_{weighting}.csv" if args.debug else None
                print(f"[INFO] {tf}-{weighting} on {effective_date}: {len(peaks)} zones detected.")
                save_zones(peaks, tf, weighting, conn, debug=args.debug, debug_file=debug_file, debug_all=args.debug_all, effective_date=effective_date)

if __name__ == '__main__':
    main()