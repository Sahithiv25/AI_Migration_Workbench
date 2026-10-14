
import pandas as pd
import json
from pathlib import Path

DATA_DIR = Path("data")

FILES = {
    "accounts": "accounts_legacy.csv",
    "contacts": "contacts_legacy.csv",
    "opportunities": "opportunities_legacy.csv",
    "activities": "activities_legacy.csv",
    "users": "users_legacy.csv",
}

RELATIONSHIPS = [
    ("accounts", "Acct Rep", "users", "Legacy User Key"),
    ("contacts", "Parent Account", "accounts", "Legacy Acct ID"),
    ("opportunities", "Customer Ref", "accounts", "Legacy Acct ID"),
    ("opportunities", "Deal Owner", "users", "Legacy User Key"),
    ("activities", "Related Account", "accounts", "Legacy Acct ID"),
    ("activities", "Related Contact", "contacts", "Legacy Contact ID"),
    ("activities", "Related Deal", "opportunities", "Deal Key"),
    ("activities", "Performed By", "users", "Legacy User Key"),
]


def load_datasets():
    return {
        name: pd.read_csv(
            DATA_DIR / filename,
            dtype="string",
            keep_default_na=False
        )
        for name, filename in FILES.items()
    }


def validate_relationships(datasets):
    results = []

    for source, source_col, target, target_col in RELATIONSHIPS:
        source_values = datasets[source][source_col].str.strip()
        target_values = datasets[target][target_col].str.strip()

        valid_ids = set(target_values[target_values.ne("")])

        missing = source_values.eq("")
        broken = source_values.ne("") & ~source_values.isin(valid_ids)

        results.append({
            "source": source,
            "field": source_col,
            "references": f"{target}.{target_col}",
            "total_rows": len(source_values),
            "missing_references": int(missing.sum()),
            "broken_references": int(broken.sum()),
            "broken_examples": (
                source_values[broken].head(5).tolist()
            )
        })

    return results


def main():
    datasets = load_datasets()
    results = validate_relationships(datasets)

    output = Path("relationship_report.json")
    output.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8"
    )

    print("\nRELATIONSHIP VALIDATION RESULTS\n")

    for item in results:
        print(
            f"{item['source']}.{item['field']} -> "
            f"{item['references']} | "
            f"Missing: {item['missing_references']} | "
            f"Broken: {item['broken_references']}"
        )

    print(f"\nReport saved to {output}")


if __name__ == "__main__":
    main()
