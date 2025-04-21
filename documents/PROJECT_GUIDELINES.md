# 🧾 Project Instructions: Credit Spread Framework (Python Edition)

---

## 🔧 General Development Guidelines

1. **Folder Structure & Modularity**

   - All development should follow the structured project layout as outlined in `README_credit_spread_framework.md`.
   - Avoid mixing concerns — indicators, strategies, snapshots, ML models, and event detectors should remain in their respective modules.

2. **Technical Indicators**

   - Indicators should implement a consistent interface (e.g., `BaseIndicator`) and accept `bars` as input (list of OHLCV records).
   - Use libraries like `pandas_ta`, `ta`, or `ta-lib` via wrapper modules in `indicators/ta_wrappers/`.
   - Ensure proper handling of insufficient lookback bars with logs and graceful skipping.

3. **Strategy Engine**

   - Strategies must subclass a `BaseStrategy` and implement `evaluate(bars, indicators)` or similar.
   - Keep rule-based logic in `strategies/rule_based/` and ML-powered logic in `strategies/ml_based/`.

4. **Machine Learning Support**

   - Place all ML logic under `ml/`:
     - `ml/data/`: Feature generators and label processors
     - `ml/training/`: Model pipelines, evaluation, training
     - `ml/models/`: Serialized `.pkl`, `.joblib`, or `.h5` models
     - `ml/utils/`: Scalers, normalizers, and helper functions
   - Use `scikit-learn`, `pandas`, `numpy` by default; expand to `xgboost`, `tensorflow`, etc. if needed.

5. **Snapshots**

   - All snapshot logic must go through `snapshots/builder.py`.
   - Snapshot "sinks" (dispatchers) should support:
     - File-based output
     - Webhook-based integration
   - Trigger modes:
     - Time-based (e.g., every 30 min)
     - Event-based (e.g., volume spike or pattern detector)

6. **Database Access (SQL Server)**
   - Use **SQLAlchemy** with **pyodbc** for connecting to **SQL Server**.
   - Store the full connection string in `config/settings.py` or a `.env` file.
   - Implement repository classes in `data/repositories/` for DB operations.
   - Schema definitions should reside in `data/schema.py` and follow the structure of `sp_data_schema.md`.
   - Track migrations in `data/migrations/` and avoid schema drift.
   - Example connection setup:

```python
# settings.py
SQLSERVER_CONN_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;DATABASE=CreditSpreadsDB;"
    "UID=user;PWD=password"
)

# db_engine.py
import urllib
from sqlalchemy import create_engine
from config.settings import SQLSERVER_CONN_STRING

conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")
```

7. **Backtesting and Real-Time**

   - Backtests run through `cli/run_backtest.py` or `backtest/__main__.py`.
   - Real-time tasks run via `realtime/__main__.py`.
   - Output must be saved or logged for traceability.

8. **CLI Interface**

   - Use `Typer` (or `Click`) to build CLI tools.
   - Provide arguments like `--start`, `--end`, `--timeframe`, `--indicator`, `--strategy`.
   - Log progress per day, and support restart/resume options.

9. **Scripting & Prototyping**

   - Place standalone scripts in `/scripts/`.
   - These include data tests, strategy previews, and model training stubs.
   - Use module imports to access logic from `credit_spread_framework`.

10. **Testing**

- Use `pytest` and organize test files under `/tests/`:
  - `test_indicators/`
  - `test_strategies/`
  - `test_backtest/`
  - `test_utils/`
- Cover edge cases, including missing data and unexpected timestamps.

11. **Time Handling**

- All timestamps must use `datetime` objects with `timezone.utc`.
- Convert ET input times (e.g., 9:30 AM ET) to UTC during ingestion.

12. **Logging & Fault Tolerance**

- Every core process should include detailed console or file logging.
- Skip bars with insufficient data; do not raise blocking exceptions.
