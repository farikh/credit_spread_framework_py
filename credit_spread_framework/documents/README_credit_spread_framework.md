
# 📈 Credit Spread Framework (Python Edition)

## 📝 Project Name
`credit_spread_framework`

---

## 🎯 Objective

Build a modular, Python-based framework to:

- Analyze, backtest, and live-evaluate **SPX credit spread strategies**
- Support **technical indicators**, **event-driven logic**, and **machine learning**
- Seamlessly scale from rule-based to ML-driven decisions
- Provide **snapshot pipelines** to inform discretionary or automated trade execution

---

## 🔍 Core Capabilities

| Area                | Features |
|---------------------|----------|
| 📊 Indicators        | Custom (RSI, EMA, OBV, Keltner), TA-Lib, pandas-ta |
| 📈 Strategy Engine   | Rule-based + ML-based trade signals (Iron Condors, PCS, CCS) |
| 🧠 ML Support        | Feature engineering, training, scoring, model selection |
| 🧩 Snapshots         | Daily/interval-based summaries of indicator + strategy signals |
| 🧪 Backtesting       | Replay historical OHLCV + indicator + SR zone + ML labels |
| ⚡ Real-Time         | Optionally compute and dispatch snapshots live during trading hours |
| 🔗 Data Layer        | Built for SQLite/Postgres using SQLAlchemy-style repositories |
| 🔄 CLI Interface     | Easy run control (`run_backtest`, `run_snapshot`, `enrich_data`) |
| 🛠️ Dev Flow         | Plugin-style indicators/strategies, rapid prototyping via `/scripts/` |

---

## 📂 Final Folder Structure

```plaintext
credit_spread_framework/
├── core/
│   ├── domain/
│   ├── abstractions/
│   └── utils/
│
├── data/
│   ├── repositories/
│   ├── migrations/
│   └── schema.py
│
├── dataproviders/
│   ├── polygon_provider.py
│   └── broker_provider.py
│
├── indicators/
│   ├── base.py
│   ├── ta_wrappers/
│   └── custom/
│
├── strategies/
│   ├── base.py
│   ├── rule_based/
│   └── ml_based/
│
├── events/
│   ├── double_top.py
│   └── volume_spike.py
│
├── snapshots/
│   ├── builder.py
│   └── sinks/
│       ├── webhook_sink.py
│       └── file_sink.py
│
├── backtest/
│   ├── __main__.py
│   └── engine.py
│
├── realtime/
│   ├── __main__.py
│   └── realtime_worker.py
│
├── ml/
│   ├── data/
│   ├── models/
│   ├── training/
│   └── utils/
│
├── cli/
│   ├── run_backtest.py
│   ├── enrich_data.py
│   └── run_snapshot.py
│
├── config/
│   └── settings.py
│
├── scripts/
│   ├── test_strategy_on_date.py
│   └── train_dummy_model.py
│
└── tests/
    ├── test_indicators/
    ├── test_strategies/
    ├── test_backtest/
    └── test_utils/
```

---

## 🚀 Getting Started

You can prototype quickly using:

```bash
python scripts/test_strategy_on_date.py
python scripts/train_dummy_model.py
```

Or run full pipelines with:

```bash
python cli/run_backtest.py --start 2023-01-01 --end 2023-03-31 --strategy IronCondorML
python cli/run_snapshot.py --day 2025-04-21
```

---

## 📌 Notes

- Fully aligned with your original `CreditSpreadFramework_Design_v2.md` and `sp_data_schema.md`
- Modular and scalable for both research and production
- Fast prototyping enabled via `scripts/` and CLI
- ML-compatible with `scikit-learn`, `xgboost`, or `tensorflow`

