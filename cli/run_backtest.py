import typer

app = typer.Typer()

@app.command()
def run(start: str, end: str, strategy: str):
    print(f"Backtest from {start} to {end} using strategy {strategy}")

if __name__ == "__main__":
    app()
