
# 📈 Credit Spread Framework — Daily Trading Indicator Setup and Roadmap

## 🎯 Strategy Context
This document summarizes the **indicators**, **planned enhancements**, and **development roadmap** for the Daily Trading setup used for Credit Put Spreads (PCS), Credit Call Spreads (CCS), and Iron Condors (IC). It also includes future plans for machine learning, pattern recognition, and momentum/scalping strategies.

---

## ✅ Current Core Technical Indicators

### Trend & Momentum
- **RSI (Relative Strength Index)**
- **EMA (Exponential Moving Average)**
- **ADX (Average Directional Index)**
- **OBV (On-Balance Volume)**
  - Includes **OBV Divergence Detection** (TFLab OBV Divergence)

### Volatility-Based
- **Keltner Channels (KC)**
- **Bollinger Bands (BB)**
- **Donchian Channels (DC)**

### Custom/Derived Indicators
- **SPX Expected Move by VOLI** (or manual IV override)
- **Rolling ATR / Range Z-Score (Intraday Volatility Score)**
- **Composite Scoring System**
  - `bullish_score`, `bearish_score`, `neutral_score`, `composite_score`, `trade_type` (IC, PCS, CCS, No Trade)

### Support & Resistance Features
- **Dynamic Support/Resistance Zones** (3m, 15m, 1h, optional 2h/4h)
- **Zone Overlap Detection**
- **Zone Expiration Logic**

### Price Action & Session Tags
- **Opening Range High/Low**
- **Closing Range**
- **Market Session (AM, Lunch, PM)**
- **Expected Move Exceeded Flag**
- **Gap Day Detection** (`is_gap_day`, `is_gap_up`, `is_gap_down`)
- **Open Range Breakout**
- **Day Type Classification** (trend day, range day, etc.)

### Event-Based Features
- **Double Top / Double Bottom Detector**
- **Volume Spike Detector**
- _(Planned)_ **External News Event Detection**

---

## 🚀 Planned Indicators for Future Phases

### Machine Learning Features
- ML-powered **feature vectors** from indicators above
- **Trade-type prediction models** (PCS, CCS, IC, No Trade)
- Integrated **model scoring and strategy recommendation**

### Pattern Recognition Features
- **Candlestick Pattern Detection** (Engulfing, Hammer, Doji, etc.)
- **Breakout / Breakdown Detection** at key S/R levels
- Enhanced **Double Top/Bottom detection with ML scoring**

### Scalping & Momentum Indicators (Final Phase)
- **VWAP (Volume Weighted Average Price)**
- **MACD (Moving Average Convergence/Divergence)**
- **CCI (Commodity Channel Index)**
- **Stochastic RSI**
- **Parabolic SAR**
- **SuperTrend**
- **Momentum (Rate of Change, ROC)**
- **EMA Crossovers (e.g., 8/21 crossovers)**
- **VWAP Bands (Standard Deviation VWAP)**

---

## 🛠️ Roadmap Phases

| Phase             | Focus Area                                           |
|-------------------|------------------------------------------------------|
| **Phase 1 (Now)**  | Core indicators for IC / spreads (RSI, EMA, BB, KC, ADX, OBV, EM) |
| **Phase 2 (Next)** | ATR volatility scoring, S/R zone refinement         |
| **Phase 3**        | Machine learning features, composite scoring, and ML-powered trade recommendations |
| **Phase 4**        | Pattern recognition (candlestick patterns, breakout detection) |
| **Phase 5 (Final)**| Scalping/momentum indicators and strategy integration |

