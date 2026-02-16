#!/usr/bin/env python
"""
Monthly Industry Adoption Charts for AI Agents.

This script creates visualizations showing when repos first adopted each AI agent,
broken down by industry (NAICS code).

Usage:
    python scripts/plot_industry_adoption.py
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PREDICTIONS_DIR = DATA_DIR / "predictions"
ADOPTION_DIR = DATA_DIR / "adoption_timing"
FIGURES_DIR = PROJECT_ROOT / "figures"

# NAICS code descriptions for chart legends
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
    "56": "Admin Services",
    "61": "Education",
    "62": "Healthcare",
    "71": "Entertainment",
    "72": "Accommodation",
    "81": "Other Services",
    "92": "Public Admin",
}


def load_first_use(agent: str) -> pd.DataFrame:
    """
    Load first use dates for an agent.

    Args:
        agent: Agent name ('claude', 'copilot', or 'codex')

    Returns:
        DataFrame with columns ['nwo', 'first_use_date']
    """
    path = ADOPTION_DIR / f"{agent}_first_use.parquet"
    logger.info(f"Loading {agent} first use dates from {path}")

    df = pd.read_parquet(path)

    # Normalize column names
    if "repo_nwo" in df.columns:
        df = df.rename(columns={"repo_nwo": "nwo"})
    if "first_claude_commit" in df.columns:
        df = df.rename(columns={"first_claude_commit": "first_use_date"})

    df["first_use_date"] = pd.to_datetime(df["first_use_date"], utc=True)

    logger.info(f"Loaded {len(df)} {agent} repos")
    return df


def merge_with_predictions(first_use: pd.DataFrame, predictions_path: Path) -> pd.DataFrame:
    """
    Merge first use dates with predictions to get industry classification.

    Args:
        first_use: DataFrame with columns ['nwo', 'first_use_date']
        predictions_path: Path to predictions parquet file

    Returns:
        Merged DataFrame with industry classifications
    """
    logger.info(f"Loading predictions from {predictions_path}")
    predictions = pd.read_parquet(predictions_path)

    # Keep only necessary columns
    predictions = predictions[["nwo", "predicted_naics"]].copy()

    # Merge
    merged = first_use.merge(predictions, on="nwo", how="inner")
    logger.info(f"Merged {len(merged)} repos with industry classifications")

    return merged


def aggregate_by_month_industry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by month and industry.

    Args:
        df: DataFrame with columns ['nwo', 'first_use_date', 'predicted_naics']

    Returns:
        Pivot table with months as index and industries as columns
    """
    # Extract year-month
    df = df.copy()
    df["year_month"] = df["first_use_date"].dt.to_period("M")

    # Count repos per industry per month
    monthly = df.groupby(["year_month", "predicted_naics"]).size().unstack(fill_value=0)

    # Sort by date
    monthly = monthly.sort_index()

    return monthly


def plot_stacked_area(
    data: pd.DataFrame,
    title: str,
    output_path: Path,
    top_n: int = 10
):
    """
    Create a stacked area chart of monthly adoption by industry.

    Args:
        data: Pivot table with months as index and industries as columns
        title: Chart title
        output_path: Path to save the chart
        top_n: Number of top industries to show (rest grouped as "Other")
    """
    # Get top N industries by total count
    industry_totals = data.sum().sort_values(ascending=False)
    top_industries = industry_totals.head(top_n).index.tolist()

    # Group remaining industries as "Other"
    plot_data = data[top_industries].copy()
    other_cols = [c for c in data.columns if c not in top_industries]
    if other_cols:
        plot_data["Other"] = data[other_cols].sum(axis=1)

    # Convert period index to datetime for plotting
    plot_data.index = plot_data.index.to_timestamp()

    # Create labels with descriptions
    columns_with_desc = []
    for col in plot_data.columns:
        if col == "Other":
            columns_with_desc.append("Other")
        else:
            desc = NAICS_DESCRIPTIONS.get(col, col)
            columns_with_desc.append(f"{col}: {desc}")

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot stacked area
    plot_data.columns = columns_with_desc
    plot_data.plot.area(ax=ax, stacked=True, alpha=0.8)

    # Formatting
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("New Repos", fontsize=12)
    ax.legend(loc="upper left", fontsize=9, title="Industry (NAICS)")
    ax.grid(axis="y", alpha=0.3)

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info(f"Saved chart to {output_path}")
    plt.close()


def process_agent(
    agent_name: str,
    agent_key: str,
):
    """
    Process a single agent: load data, merge with predictions, and create chart.

    Args:
        agent_name: Display name of the agent (for chart title)
        agent_key: Key for file names ('claude', 'copilot', or 'codex')
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"Processing {agent_name}")
    logger.info(f"{'='*50}")

    # Load first use data
    first_use_df = load_first_use(agent_key)

    # Merge with predictions
    predictions_path = PREDICTIONS_DIR / f"{agent_key}_predictions.parquet"
    merged = merge_with_predictions(first_use_df, predictions_path)

    # Aggregate by month and industry
    monthly = aggregate_by_month_industry(merged)

    # Print summary
    logger.info(f"\nDate range: {monthly.index.min()} to {monthly.index.max()}")
    logger.info(f"Total repos: {monthly.sum().sum()}")
    logger.info(f"\nTop industries:")
    for naics, count in monthly.sum().sort_values(ascending=False).head(5).items():
        desc = NAICS_DESCRIPTIONS.get(naics, "Unknown")
        logger.info(f"  {naics} ({desc}): {count}")

    # Create visualization
    output_path = FIGURES_DIR / f"industry_adoption_{agent_key}.png"
    plot_stacked_area(
        monthly,
        f"Monthly Industry Adoption - {agent_name}",
        output_path
    )

    return merged


def main():
    """Main function to generate all adoption charts."""
    logger.info("Starting industry adoption analysis")

    # Ensure output directory exists
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Process all agents
    agents = [
        ("Claude Code", "claude"),
        ("GitHub Copilot", "copilot"),
        ("OpenAI Codex", "codex"),
    ]

    for agent_name, agent_key in agents:
        try:
            process_agent(agent_name, agent_key)
        except FileNotFoundError as e:
            logger.warning(f"Data not found for {agent_name}: {e}")

    logger.info("\nDone! Check figures/ for output files.")


if __name__ == "__main__":
    main()
