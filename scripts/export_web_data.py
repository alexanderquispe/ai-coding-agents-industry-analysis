#!/usr/bin/env python
"""
Export data for web visualizations.
"""

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PREDICTIONS_DIR = DATA_DIR / "predictions"
ADOPTION_DIR = DATA_DIR / "adoption_timing"
OUTPUT_DIR = PROJECT_ROOT / "web"

NAICS_DESCRIPTIONS = {
    "11": "Agriculture",
    "21": "Mining",
    "22": "Utilities",
    "23": "Construction",
    "31-33": "Manufacturing",
    "42": "Wholesale Trade",
    "44-45": "Retail Trade",
    "48-49": "Transportation",
    "51": "Information",
    "52": "Finance",
    "53": "Real Estate",
    "54": "Professional Services",
    "55": "Management",
    "56": "Admin Services",
    "61": "Education",
    "62": "Healthcare",
    "71": "Entertainment",
    "72": "Accommodation",
    "81": "Other Services",
    "92": "Public Admin",
}

# Colors for all 19 industries (distinct palette)
INDUSTRY_COLORS = {
    "54": "#2E86AB",  # Professional Services - Blue
    "51": "#A23B72",  # Information - Magenta
    "52": "#F18F01",  # Finance - Orange
    "61": "#C73E1D",  # Education - Red
    "71": "#6A0572",  # Entertainment - Purple
    "56": "#95C623",  # Admin Services - Lime
    "81": "#5C8001",  # Other Services - Olive
    "48-49": "#7B2D8E",  # Transportation - Violet
    "44-45": "#00A6A6",  # Retail - Teal
    "62": "#E36397",  # Healthcare - Pink
    "31-33": "#8B4513",  # Manufacturing - Brown
    "92": "#4A7C59",  # Public Admin - Forest
    "11": "#DAA520",  # Agriculture - Goldenrod
    "72": "#FF6B6B",  # Accommodation - Coral
    "53": "#20B2AA",  # Real Estate - Light Sea Green
    "22": "#4169E1",  # Utilities - Royal Blue
    "23": "#CD853F",  # Construction - Peru
    "42": "#708090",  # Wholesale Trade - Slate Gray
    "21": "#2F4F4F",  # Mining - Dark Slate
}


def load_and_process(agent: str) -> pd.DataFrame:
    """Load and process data for an agent."""
    # Load files
    first_use = pd.read_parquet(ADOPTION_DIR / f"{agent}_first_use.parquet")
    predictions = pd.read_parquet(PREDICTIONS_DIR / f"{agent}_predictions.parquet")

    # Normalize columns
    if "repo_nwo" in first_use.columns:
        first_use = first_use.rename(columns={"repo_nwo": "nwo"})
    if "first_claude_commit" in first_use.columns:
        first_use = first_use.rename(columns={"first_claude_commit": "first_use_date"})

    first_use["first_use_date"] = pd.to_datetime(first_use["first_use_date"], utc=True)

    # Merge
    merged = first_use.merge(predictions[["nwo", "predicted_naics"]], on="nwo", how="inner")
    merged["year_month"] = merged["first_use_date"].dt.to_period("M")

    return merged


def generate_cumulative_data(agent: str) -> dict:
    """Generate cumulative monthly data by industry."""
    df = load_and_process(agent)

    # Count by month and industry
    monthly = df.groupby(["year_month", "predicted_naics"]).size().unstack(fill_value=0)
    monthly = monthly.sort_index()

    # Calculate cumulative
    cumulative = monthly.cumsum()

    # Convert to web format
    months = [str(m) for m in cumulative.index]

    industries = []
    for col in cumulative.columns:
        name = f"{col}: {NAICS_DESCRIPTIONS.get(col, col)}"
        color = INDUSTRY_COLORS.get(col, "#666666")

        industries.append({
            "code": col,
            "name": name,
            "color": color,
            "values": cumulative[col].tolist(),
            "monthly": monthly[col].tolist()
        })

    # Sort by final value (largest at bottom for stacking)
    industries.sort(key=lambda x: x["values"][-1], reverse=True)

    return {
        "months": months,
        "industries": industries,
        "total_repos": int(cumulative.iloc[-1].sum())
    }


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    agents = [
        ("claude", "Claude Code"),
        ("copilot", "GitHub Copilot"),
        ("codex", "OpenAI Codex"),
    ]

    for agent_key, agent_name in agents:
        try:
            print(f"\n{'='*50}")
            print(f"Processing {agent_name}...")
            print('='*50)

            agent_data = generate_cumulative_data(agent_key)

            with open(OUTPUT_DIR / f"{agent_key}_cumulative.json", "w") as f:
                json.dump(agent_data, f, indent=2)

            print(f"Exported {agent_name} data: {agent_data['total_repos']:,} repos")
            print(f"Months: {agent_data['months'][0]} to {agent_data['months'][-1]}")
            print(f"Industries: {len(agent_data['industries'])}")

        except Exception as e:
            print(f"Error processing {agent_name}: {e}")

    print("\n" + "="*50)
    print("All data exported to web/ directory")
    print("="*50)


if __name__ == "__main__":
    main()
