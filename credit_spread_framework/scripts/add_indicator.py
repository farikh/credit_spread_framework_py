import typer
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine

app = typer.Typer()

@app.command()
def add_indicator(
    short_name: str = typer.Option(..., help="Short name for the indicator (e.g. 'RSI')"),
    name: str = typer.Option(..., help="Full name/description of the indicator"),
    class_path: str = typer.Option(..., help="Full Python class path (e.g., 'credit_spread_framework.indicators.ta_wrappers.rsi_indicator.RSIIndicator')"),
    lookback: int = typer.Option(0, help="Lookback period (if applicable)"),
    parameters_json: str = typer.Option("{}", help="JSON string for parameters"),
    is_active: bool = typer.Option(True, help="Is the indicator active?")
):
    engine = get_engine()

    insert_stmt = text("""
        INSERT INTO dbo.indicators (Name, ShortName, ClassPath, Lookback, ParametersJson, IsActive)
        VALUES (:name, :short_name, :class_path, :lookback, :parameters_json, :is_active)
    """)

    with engine.begin() as conn:
        conn.execute(insert_stmt, {
            "name": name,
            "short_name": short_name,
            "class_path": class_path,
            "lookback": lookback,
            "parameters_json": parameters_json,
            "is_active": int(is_active)
        })

    print(f"✅ Added indicator '{short_name}' successfully.")

if __name__ == "__main__":
    app()
