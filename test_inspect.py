import pandas as pd
from pathlib import Path

for file in sorted(Path("data").glob("*_legacy.csv")):
    df = pd.read_csv(file, nrows=3)
    print(f"\n{file.name}")
    print("Columns:", df.columns.tolist())
    print(df.head(2).to_string(index=False))