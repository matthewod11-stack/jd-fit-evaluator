#!/usr/bin/env python3

import typer
from pathlib import Path

app = typer.Typer(help="Test CLI")

@app.command()
def score(jd: str = typer.Option(..., help="Path to JD text file"),
          sample: bool = typer.Option(False, help="Use sample candidate JSON")):
    print(f"JD: {jd}, Sample: {sample}")

if __name__ == '__main__':
    app()