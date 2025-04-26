
def get_unique_dates(conn, table, override_day=None):
    if override_day:
        return [override_day]
    query = f"SELECT DISTINCT DATE(timestamp) as trade_date FROM {table}"
    df = pd.read_sql_query(query, conn)
    return df["trade_date"].tolist()



import sqlite3
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timezone

LOOKBACK_BARS = {
    "1m": 1000,
    "3m": 600,
    "15m": 300,
    "1h": 300,
    "1d": 100
}

TIMEFRAMES = ["1m", "3m", "15m", "1h", "1d"]
METHODS = ["time", "linear", "volume"]
DB_PATH = r"C:\Projects\Trading\Iron Condor Analysis\Polygon Retrieve\sp_data.sqlite"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def build_zone(level, score, touches, first_touched, last_touched, active=True):
    return {
        "zone_level": level,
        "score": score,
        "touch_count": touches,
        "start_time": first_touched,
        "last_touched": last_touched,
        "active": int(active)
    }

def detect_time_zones(data, tf):
    WINDOW = 50
    MIN_TOUCHES = 2
    ZONE_TOLERANCE = 0.5

    data = data.copy()
    zones = []
    histogram = {}

    for i in range(WINDOW, len(data) - WINDOW):
        window = data.iloc[i - WINDOW:i + WINDOW + 1]
        low = data.iloc[i]["low"]
        high = data.iloc[i]["high"]
        is_support = low == window["low"].min()
        is_resistance = high == window["high"].max()

        if is_support or is_resistance:
            level = low if is_support else high
            found = False
            for existing in histogram:
                if abs(existing - level) <= ZONE_TOLERANCE:
                    histogram[existing]["touches"] += 1
                    histogram[existing]["last_touched"] = data.iloc[i]["timestamp"]
                    found = True
                    break
            if not found:
                histogram[level] = {
                    "touches": 1,
                    "first_touched": data.iloc[i]["timestamp"],
                    "last_touched": data.iloc[i]["timestamp"]
                }

    for level, info in histogram.items():
        if info["touches"] >= MIN_TOUCHES:
            age_weight = (data["timestamp"].max() - pd.to_datetime(info["last_touched"])).total_seconds()
            zones.append({
                "zone_level": level,
                "touch_count": info["touches"],
                "start_time": info["first_touched"],
                "last_touched": info["last_touched"],
                "score": info["touches"],
                "weighted_score": info["touches"] * 1000 / (age_weight + 1)
            })

    return sorted(zones, key=lambda x: x["weighted_score"], reverse=True)

def detect_linear_zones(data, tf):
    MIN_TOUCHES = 2
    ZONE_TOLERANCE = 1.0
    zones = []

    for i in range(len(data) - 1):
        for j in range(i + 1, len(data)):
            x1, y1 = i, data.iloc[i]["close"]
            x2, y2 = j, data.iloc[j]["close"]
            if x2 - x1 == 0:
                continue
            slope = (y2 - y1) / (x2 - x1)
            touches = 0
            for k in range(len(data)):
                xk = k
                y_expected = slope * (xk - x1) + y1
                if abs(data.iloc[k]["close"] - y_expected) <= ZONE_TOLERANCE:
                    touches += 1
            if touches >= MIN_TOUCHES:
                zones.append(build_zone(y1, touches, touches, data.iloc[i]["timestamp"], data.iloc[j]["timestamp"]))
    return zones

def detect_volume_zones(data, tf):
    from collections import defaultdict
    BINS = 20
    ZONE_TOLERANCE = 0.5
    zones = []

    bin_edges = np.linspace(data["low"].min(), data["high"].max(), BINS + 1)
    volume_by_price = defaultdict(float)

    for _, row in data.iterrows():
        price_range = np.linspace(row["low"], row["high"], num=10)
        for price in price_range:
            bin_idx = np.digitize(price, bin_edges) - 1
            volume_by_price[bin_idx] += row["spy_volume"] / 10.0

    for bin_idx, volume in volume_by_price.items():
        if volume > 0:
            level = (bin_edges[bin_idx] + bin_edges[bin_idx + 1]) / 2
            touches = len(data[np.isclose(data["close"], level, atol=ZONE_TOLERANCE)])
            if touches >= 2:
                zones.append(build_zone(level, int(volume), touches, data["timestamp"].min(), data["timestamp"].max()))
    return zones

def save_zones(conn, zones, tf):
    if not zones:
        return
    df = pd.DataFrame(zones)
    df["timeframe"] = tf
    df["created_at"] = datetime.now(timezone.utc).isoformat()
    table = f"spx_ohlcv_{tf}_sr_zones"
    try:
        df.to_sql(table, conn, if_exists="append", index=False)
        log(f"✅ Saved {len(df)} zones to DB table {table}")
    except Exception as e:
        log(f"❌ Failed to save zones to {table}: {e}")

def delete_existing_zones(conn, tf, method, start_date, end_date):
    table = f"spx_ohlcv_{tf}_sr_zones"
    query = f"DELETE FROM {table} WHERE method = ? AND DATE(start_time) BETWEEN ? AND ?"
    try:
        conn.execute(query, (method, start_date, end_date))
        conn.commit()
        log(f"🧹 Deleted zones for {method} {tf} from {start_date} to {end_date}")
    except Exception as e:
        log(f"❌ Failed to delete from {table}: {e}")

def get_date_range(conn, tf):
    table = f"spx_ohlcv_{tf}"
    query = f"SELECT MIN(DATE(timestamp)) as start, MAX(DATE(timestamp)) as end FROM {table}"
    df = pd.read_sql_query(query, conn)
    return df.iloc[0]["start"], df.iloc[0]["end"]

def load_bars_by_count(conn, table, target_date, bar_count):
    end_ts = f"{target_date} 23:59:59"
    query = f"""
        SELECT * FROM {table}
        WHERE timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(end_ts, bar_count), parse_dates=["timestamp"])
    return df.sort_values("timestamp")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe")
    parser.add_argument("--method")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--day")
    return parser.parse_args()

def main():
    args = parse_args()
    conn = sqlite3.connect(DB_PATH)
    tf_list = [args.timeframe] if args.timeframe else TIMEFRAMES
    method_list = [args.method] if args.method else METHODS

    for tf in tf_list:
        table = f"spx_ohlcv_{tf}"
        start_date, end_date = get_date_range(conn, tf)
        dates_to_process = get_unique_dates(conn, table, override_day=args.day)

        for method in method_list:
            delete_existing_zones(conn, tf, method, start_date, end_date)

        for current_date in dates_to_process:
            data = load_bars_by_count(conn, table, current_date, LOOKBACK_BARS[tf])
            if data.empty:
                log(f"⚠️ Skipped {tf} {current_date} — no bars loaded")
                continue
            log(f"📅 Processing {tf} for {current_date} ({len(data)} bars loaded)")

            for method in method_list:
                try:
                    if method == "time":
                        zones = detect_time_zones(data, tf)
                    elif method == "linear":
                        zones = detect_linear_zones(data, tf)
                    elif method == "volume":
                        zones = detect_volume_zones(data, tf)
                    else:
                        continue

                    for z in zones:
                        z["method"] = method  # ensure method field exists

                    log(f"📊 {method.upper()} zones found: {len(zones)} for {tf} on {current_date}")

                    if args.debug:
                        df = pd.DataFrame(zones)
                        if not df.empty:
                            out_file = f"zones_debug_{current_date}_{tf}_{method}.csv"
                            df.to_csv(out_file, index=False)
                            log(f"📝 Debug: saved {len(df)} zones to {out_file}")
                    else:
                        save_zones(conn, zones, tf)

                except Exception as e:
                    log(f"❌ Error on {current_date} {tf} {method}: {e}")

if __name__ == "__main__":
    main()
