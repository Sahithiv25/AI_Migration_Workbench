"""Checks for data inconsistencies like missingness, uniqueness, column types and samples"""


import pandas as pd
import json
from pathlib import Path

DATA_DIR = Path("data")

def profile_dataset(file_path):
    df = pd.read_csv(file_path, low_memory=False)

    report = {
        "dataset": file_path.name,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": {}
    }

    for column in df.columns:
        series = df[column]

        report["columns"][column] = {
            "data_type": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": round(
                series.isna().mean() * 100, 2
            ),
            "unique_values": int(series.nunique(dropna=True)),
            "sample_values": [
                str(value)
                for value in series.dropna().head(3)
            ]
        }

    return report


def main():
    reports = {}

    business_files = [
    "accounts_legacy.csv",
    "contacts_legacy.csv",
    "opportunities_legacy.csv",
    "activities_legacy.csv",
    "users_legacy.csv",
    ]

    for filename in business_files:
        file_path = DATA_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Missing dataset: {file_path}")

        print(f"Profiling {file_path.name}...")
        reports[file_path.stem] = profile_dataset(file_path)

    # for file_path in sorted(DATA_DIR.glob("*.csv")):

    
    #     print(f"Profiling {file_path.name}...")
    #     reports[file_path.stem] = profile_dataset(file_path)

    # if not reports:
    #     raise FileNotFoundError(
    #         f"No CSV files found in {DATA_DIR.resolve()}"
    #     )

    output_path = Path("data_quality_report.json")

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)

    print(f"\nProfiled {len(reports)} datasets.")
    print(f"Report saved to {output_path}")



if __name__ == "__main__":
    main()
