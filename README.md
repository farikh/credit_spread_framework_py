# 📈 Credit Spread Framework

A consolidated overview of the **Credit Spread Trading Framework**. For detailed guidance, see the linked documents below.

---

## 🚀 Getting Started

Install dependencies and run the test suite:

```bash
pip install -r requirements.txt
pytest -q
```

## 🎯 Objective

- Analyze, backtest, and live-evaluate SPX credit spread strategies
- Support technical indicators, event detection, and machine learning
- Provide enrichment pipelines (e.g. SR-Zones) and snapshots
- Scale from research prototyping to production deployments

## 📂 Project Structure

```plaintext
.
├── cli/        – Typer-based commands (backtest, enrich, snapshot)
├── config/     – Settings and environment configurations
├── data/       – Repositories, migrations, and DB engine
├── indicators/ – Base, TA wrappers, and custom indicators
├── strategies/ – Rule-based and ML-powered strategies
├── snapshots/  – Snapshot builder and sinks
├── backtest/   – Backtesting engine
├── realtime/   – Live-streaming and real-time worker
├── ml/         – Data pipelines, training, and models
├── scripts/    – Prototyping utilities
├── tests/      – Unit and integration tests
├── setup.py    – Package configuration
├── FEATURES.md – Feature documentation and usage examples
├── README.md   – (this file)
└── credit_spread_framework/
    └── documents/  – Detailed docs (see below)
```

## 📖 Detailed Documentation

All deep-dive docs are located in **credit_spread_framework/documents/**:

- [Architecture & Quickstart](credit_spread_framework/documents/README_credit_spread_framework.md)
- [Implementation Guidelines](credit_spread_framework/documents/PROJECT_GUIDELINES.md)
- [CLI Usage & Instructions](credit_spread_framework/documents/PROJECT_INSTRUCTIONS.md)
- [Schema Rules & Data Model](credit_spread_framework/documents/sp_data_schema.md)
- [Indicator Setup & Roadmap](credit_spread_framework/documents/indicator_setup_and_roadmap.md)

---

## 🗄️ Database Configuration

Before running any CLI commands (enrich, backtest, snapshot), ensure your database connection string is set:

- Windows Authentication (Trusted Connection):

  In PowerShell:

  ```powershell
  $Env:SQLSERVER_CONN_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-DKR7BL4Q\\SQLEXPRESS;DATABASE=CreditSpreadsDB;Trusted_Connection=yes;"
  ```

- SQL Login:

  In PowerShell:

  ```powershell
  $Env:SQLSERVER_CONN_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-DKR7BL4Q\\SQLEXPRESS;DATABASE=CreditSpreadsDB;User Id=credit_spread_user;Password=SuperSecretPass!;"
  ```

Alternatively, place the same `SQLSERVER_CONN_STRING` (or `SQLSERVER_SQL_LOGIN_CONN_STRING`) in a `.env` file at the project root. The framework will automatically load it at runtime.

## 🔧 Development Workflow

1. Follow the **Implementation Guidelines** before writing code.
2. Add new indicators or strategies via `scripts/add_indicator.py`.
3. Use `cli/enrich_data.py` for indicator enrichment (SR-Zones, RSI, etc.).
4. Use `cli/run_backtest.py` for backtesting strategies.
5. Ensure all changes pass `pytest -q` and adhere to style rules.

---
