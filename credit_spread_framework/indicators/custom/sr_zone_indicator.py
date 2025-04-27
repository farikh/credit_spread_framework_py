from credit_spread_framework.indicators.base import BaseIndicator
import pandas as pd
import numpy as np
import json

class SRZoneIndicator(BaseIndicator):
    def __init__(self, parameters_json=None, qualifier=None):
        """
        parameters_json: dict of SR detection settings:
            pivot_lookback (int): maximum number of pivots to consider
            filter_len (int): smoothing filter size
            precision (int): number of histogram bins
            include_ph (bool): include pivot highs
            include_pl (bool): include pivot lows
            lengths (list[int]): pivot detection window sizes
            threshold_ratio (float): relative strength needed for a level to be considered SR (0.0-1.0)
        qualifier: one of "time", "linear", "volume"
        """
        self.available_methods = ["time", "linear", "volume"]
        self.methods_to_run = [qualifier] if qualifier in self.available_methods else self.available_methods
        
        # Parse params: accept only dict input (ignore malformed JSON strings)
        self.params = parameters_json if isinstance(parameters_json, dict) else {}
        
        # Core parameters (exactly matching TradingView)
        self.pivot_lookback = self.params.get("pivot_lookback", 50)  # Exact match to TradingView
        self.filter_len = self.params.get("filter_len", 3)  # Exact match to TradingView
        self.precision = self.params.get("precision", 75)  # Exact match to TradingView
        self.threshold_ratio = self.params.get("threshold_ratio", 0.25)  # Exact match to TradingView
        
        # Collection parameters
        self.include_ph = self.params.get("include_ph", True)
        self.include_pl = self.params.get("include_pl", True)
        self.lengths = self.params.get("lengths", [5, 10, 20, 50])  # Same as TradingView default

    def calculate(self, bars: pd.DataFrame) -> pd.DataFrame:
        # For debugging, we'll print information about what data we're getting
        debug_output = True

        # return empty frame if no bars
        if bars.empty:
            if debug_output:
                print("DEBUG: No bars provided")
            return pd.DataFrame(columns=[
                "timestamp_start","timestamp_end","value",
                "aux_value","qualifier","parameters_json"
            ])

        ts_start = bars["timestamp"].iloc[0]
        ts_end = bars["timestamp"].iloc[-1]
        records = []
        params_json = json.dumps(self.params)

        if debug_output:
            print(f"DEBUG: Analyzing {len(bars)} bars from {ts_start} to {ts_end}")
            print(f"DEBUG: Using methods: {self.methods_to_run}")

        # collect pivots - similar to TradingView's approach
        pivot_lvls, pivot_wts, pivot_ts = [], [], []
        for length in self.lengths:
            if self.include_ph:
                # Find pivot highs (current high > prior/future highs)
                ph = bars["high"][(bars["high"].shift(length) < bars["high"]) &
                                  (bars["high"].shift(-length) < bars["high"])]
                for idx, lvl in ph.items():
                    pivot_lvls.append(lvl)
                    pivot_ts.append(bars["timestamp"].iat[idx])
                    pivot_wts.append(self._weight(bars, idx))
                    
            if self.include_pl:
                # Find pivot lows (current low < prior/future lows)
                pl = bars["low"][(bars["low"].shift(length) > bars["low"]) &
                                 (bars["low"].shift(-length) > bars["low"])]
                for idx, lvl in pl.items():
                    pivot_lvls.append(lvl)
                    pivot_ts.append(bars["timestamp"].iat[idx])
                    pivot_wts.append(self._weight(bars, idx))
        
        if debug_output:
            print(f"DEBUG: Found {len(pivot_lvls)} pivots")
            if pivot_lvls:
                print(f"DEBUG: Pivot levels: {pivot_lvls[:5]}...")
                print(f"DEBUG: Pivot weights: {pivot_wts[:5]}...")
            
        # fallback to extremes if no pivots
        if not pivot_lvls:
            if debug_output:
                print("DEBUG: No pivots found, using extremes")
            high = bars["high"].max()
            low = bars["low"].min()
            pivot_lvls = [high, low]
            pivot_wts = [1,1]
            pivot_ts = [ts_start, ts_start]
            
            # Add debug output to help diagnose the issue
            print(f"WARNING: No pivots found for {ts_start} to {ts_end}, using extremes: high={high}, low={low}")

        # enforce pivot_lookback limit (number of total pivots = highs + lows)
        if self.pivot_lookback and pivot_lvls:
            max_pivots = self.pivot_lookback * 2
            if len(pivot_lvls) > max_pivots:
                if debug_output:
                    print(f"DEBUG: Too many pivots ({len(pivot_lvls)}), keeping only {max_pivots}")
                # Keep most recent pivots, sorted by timestamp
                pivot_data = list(zip(pivot_ts, pivot_lvls, pivot_wts))
                pivot_data.sort(key=lambda x: x[0], reverse=True)  # Sort by timestamp, most recent first
                pivot_data = pivot_data[:max_pivots]  # Keep most recent pivots
                pivot_ts, pivot_lvls, pivot_wts = zip(*pivot_data)  # Unpack

        # normalize time weights exactly like TradingView (TradingView uses w = bar_index - pivot_bar)
        if "time" in self.methods_to_run and pivot_wts:
            min_w = min(pivot_wts)
            pivot_wts = [w - min_w + 1 for w in pivot_wts]  # Exact match to Pine script

        # build and detect peaks for each qualifier
        for method in self.methods_to_run:
            if debug_output:
                print(f"DEBUG: Processing method {method}")
            
            # Override weights based on current method
            method_weights = self._get_weights_for_method(method, pivot_wts, pivot_ts, bars)
            
            # Calculate centers and histogram as in TradingView
            centers, hist = self._build_histogram(pivot_lvls, method_weights)
            
            # Apply smoothing filter (similar to TradingView's sinc_filter)
            filt = np.convolve(hist, np.ones(self.filter_len)/self.filter_len, mode='same')
            
            # Detect peaks similar to TradingView's peak_detection
            peaks = self._detect_peaks(centers, filt, self.threshold_ratio)
            
            if debug_output:
                print(f"DEBUG: {method} - Detected {len(peaks)} peaks")
            
            # If no peaks detected, use a fallback value
            if not peaks:
                mid_value = (min(pivot_lvls) + max(pivot_lvls)) / 2
                records.append({
                    "timestamp_start": ts_start,
                    "timestamp_end": ts_end,
                    "value": float(mid_value),
                    "aux_value": 0,
                    "qualifier": method,
                    "parameters_json": params_json
                })
                if debug_output:
                    print(f"DEBUG: {method} - No peaks detected, using fallback value {mid_value}")
                continue
            
            # Process detected peaks (similar to TradingView)
            for lvl, score in peaks:
                # Count pivots near this level (for visualizing "strength")
                tol = (centers[1] - centers[0]) / 2 if len(centers) > 1 else 0
                count = sum(abs(np.array(pivot_lvls) - lvl) <= tol)
                
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
        """Calculate the base weight for a pivot based on its position in the data"""
        # raw time weight = distance from pivot to last bar (matching TradingView exactly)
        return len(bars) - 1 - idx

    def _get_weights_for_method(self, method, base_weights, timestamps, bars):
        """Calculate the weights specific to the weighting method"""
        if method == "time":
            return base_weights  # Already calculated correctly during normalization
        elif method == "volume":
            # Try to access volume directly from bar data
            volume_weights = []
            for ts in timestamps:
                # Find the bar with this timestamp
                matching_bars = bars[bars["timestamp"] == ts]
                if not matching_bars.empty and "spy_volume" in matching_bars:
                    volume_weights.append(float(matching_bars["spy_volume"].iloc[0]))
                else:
                    volume_weights.append(1.0)  # Default if volume not available
            return volume_weights
        else:  # "linear"
            return [1.0] * len(base_weights)  # Equal weights

    def _build_histogram(self, levels, weights):
        """Build a histogram of pivot levels, weighted by the provided weights"""
        if not levels:
            return [], []
            
        mn, mx = min(levels), max(levels)
        print(f"DEBUG: Histogram range: min={mn}, max={mx}")
        
        # Add a small buffer to avoid edge effects
        buffer = (mx - mn) * 0.05
        mn -= buffer
        mx += buffer
        
        print(f"DEBUG: Histogram range with buffer: min={mn}, max={mx}")
        
        edges = np.linspace(mn, mx, self.precision + 1)
        hist = np.zeros(self.precision)
        
        for lvl, w in zip(levels, weights):
            idx = np.searchsorted(edges, lvl) - 1
            if 0 <= idx < len(hist):
                hist[idx] += w
                
        centers = (edges[:-1] + edges[1:]) / 2
        
        # Print some histogram stats
        if len(hist) > 0:
            print(f"DEBUG: Histogram stats: min={hist.min()}, max={hist.max()}, mean={hist.mean()}")
            print(f"DEBUG: Centers range: min={centers.min()}, max={centers.max()}")
            
            # Print the top 5 histogram values and their centers
            top_indices = np.argsort(hist)[-5:]
            for i in reversed(top_indices):
                print(f"DEBUG: Histogram peak: center={centers[i]}, value={hist[i]}")
        
        return centers, hist

    def _detect_peaks(self, centers, hist, threshold_ratio=0.25):
        """
        Detect peaks in the histogram, similar to TradingView's approach.
        
        This implementation is designed to match TradingView's peak detection algorithm
        as closely as possible, including the handling of multiple peaks and their
        relative strengths.
        """
        peaks = []
        if not hist.any():
            return peaks
            
        # Use a percentage of max as threshold (TradingView uses similar approach)
        max_hist = max(hist)
        thresh = threshold_ratio * max_hist
        print(f"DEBUG: Peak detection threshold: {thresh} (ratio={threshold_ratio})")
        
        # Find all local maxima that exceed the threshold
        for i in range(1, len(hist)-1):
            if hist[i] > hist[i-1] and hist[i] > hist[i+1] and hist[i] >= thresh:
                peaks.append((centers[i], hist[i]))
                print(f"DEBUG: Found peak at center={centers[i]}, value={hist[i]}")
        
        # If no peaks found, try with a lower threshold
        if not peaks and threshold_ratio > 0.1:
            lower_threshold = threshold_ratio / 2
            print(f"DEBUG: No peaks found, trying with lower threshold: {lower_threshold}")
            return self._detect_peaks(centers, hist, lower_threshold)
        
        # If still no peaks, use extremes (min and max values)
        if not peaks:
            # Find indices of min and max values in the histogram
            min_idx = np.argmin(hist)
            max_idx = np.argmax(hist)
            
            # Add min and max as peaks
            peaks.append((centers[min_idx], hist[min_idx]))
            if min_idx != max_idx:  # Avoid duplicates
                peaks.append((centers[max_idx], hist[max_idx]))
            
            print(f"DEBUG: Using extremes as peaks: {peaks}")
        
        # TradingView sorts peaks by score (highest first)
        peaks.sort(key=lambda x: x[1], reverse=True)
        
        if peaks:
            print(f"DEBUG: Top peak value: {peaks[0][0]}")
            
            # TradingView typically shows 2-3 major SR zones
            # Limit to top 3 peaks for clarity
            if len(peaks) > 3:
                print(f"DEBUG: Limiting to top 3 peaks out of {len(peaks)}")
                peaks = peaks[:3]
        
        return peaks
