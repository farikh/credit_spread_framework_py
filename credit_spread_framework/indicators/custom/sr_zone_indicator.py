from credit_spread_framework.indicators.base import BaseIndicator
import pandas as pd
import numpy as np
import json

class SRZoneIndicator(BaseIndicator):
    def __init__(self, parameters_json=None, qualifier=None):
        """
        parameters_json: dict of SR detection settings:
            pivot_lookback (int), filter_len (int), precision (int),
            include_ph (bool), include_pl (bool), lengths (list[int])
        qualifier: one of "time", "linear", "volume"
        """
        self.available_methods = ["time", "linear", "volume"]
        self.methods_to_run = [qualifier] if qualifier in self.available_methods else self.available_methods
        # parse params: accept only dict input (ignore malformed JSON strings)
        self.params = parameters_json if isinstance(parameters_json, dict) else {}
        self.pivot_lookback = self.params.get("pivot_lookback", 50)
        self.filter_len = self.params.get("filter_len", 3)
        self.precision = self.params.get("precision", 75)
        self.include_ph = self.params.get("include_ph", True)
        self.include_pl = self.params.get("include_pl", True)
        self.lengths = self.params.get("lengths", [5,10,20,50])

    def calculate(self, bars: pd.DataFrame) -> pd.DataFrame:
        if bars.empty:
            return pd.DataFrame(columns=[
                "timestamp_start","timestamp_end","value","aux_value","qualifier","parameters_json"
            ])
        ts_start = bars["timestamp"].iloc[0]
        ts_end = bars["timestamp"].iloc[-1]
        records = []
        params_json = json.dumps(self.params)
        # collect pivots
        pivot_lvls, pivot_wts, pivot_ts = [], [], []
        for length in self.lengths:
            if self.include_ph:
                ph = bars["high"][(bars["high"].shift(length) < bars["high"]) & (bars["high"].shift(-length) < bars["high"])]
                for idx, lvl in ph.items():
                    pivot_lvls.append(lvl)
                    pivot_ts.append(bars["timestamp"].iat[idx])
                    pivot_wts.append(self._weight(bars, idx))
            if self.include_pl:
                pl = bars["low"][(bars["low"].shift(length) > bars["low"]) & (bars["low"].shift(-length) > bars["low"])]
                for idx, lvl in pl.items():
                    pivot_lvls.append(lvl)
                    pivot_ts.append(bars["timestamp"].iat[idx])
                    pivot_wts.append(self._weight(bars, idx))
        # if no pivots, fallback extremes
        if not pivot_lvls:
            high = bars["high"].max(); low = bars["low"].min()
            pivot_lvls = [high, low]; pivot_wts = [1,1]; pivot_ts = [ts_start, ts_start]
        # process each method
        for method in self.methods_to_run:
            # build weighted histogram
            centers, hist = self._build_histogram(pivot_lvls, pivot_wts)
            # smooth
            filt = np.convolve(hist, np.ones(self.filter_len)/self.filter_len, mode='same')
            # detect peaks
            peaks = self._detect_peaks(centers, filt)
            # determine touch counts per peak bin
            for lvl, score in peaks:
                # count original pivots near level within bin width
                tol = (centers[1]-centers[0])/2 if len(centers)>1 else 0
                count = sum(abs(np.array(pivot_lvls)-lvl)<=tol)
                records.append({
                    "timestamp_start": ts_start,
                    "timestamp_end": ts_end,
                    "value": float(lvl),
                    "aux_value": int(count),
                    "qualifier": method,
                    "parameters_json": params_json
                })
        return pd.DataFrame(records)

    def _weight(self, bars, idx):
        style = self.methods_to_run[0]  # current qualifier
        if style == "time":
            return (idx / len(bars))
        elif style == "volume":
            return bars["spy_volume"].iat[idx] if "spy_volume" in bars else 1
        return 1

    def _build_histogram(self, levels, weights):
        mn, mx = min(levels), max(levels)
        edges = np.linspace(mn, mx, self.precision+1)
        hist = np.zeros(self.precision)
        for lvl, w in zip(levels, weights):
            idx = np.searchsorted(edges, lvl) - 1
            if 0 <= idx < len(hist):
                hist[idx] += w
        centers = (edges[:-1] + edges[1:]) / 2
        return centers, hist

    def _detect_peaks(self, centers, hist, threshold_ratio=0.3):
        peaks = []
        if not hist.any():
            return peaks
        thresh = threshold_ratio * max(hist)
        for i in range(1, len(hist)-1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] >= thresh:
                peaks.append((centers[i], hist[i]))
        return peaks
