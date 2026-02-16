#!/usr/bin/env python
"""
Generate Summary Statistics for AI Agent Industry Adoption.

This script produces summary tables and statistics for economists reviewing
the AI coding agent adoption data.

Usage:
    python scripts/generate_summary_stats.py
"""

import logging
from pathlib import Path

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
OUTPUT_DIR = PROJECT_ROOT / "output"

# NAICS descriptions
NAICS_DESCRIPTIONS = {
    "11": "Agriculture, Forestry, Fishing and Hunting",
    "21": "Mining, Quarrying, and Oil and Gas Extraction",
    "22": "Utilities",
    "23": "Construction",
    "31-33": "Manufacturing",
    "42": "Wholesale Trade",
    "44-45": "Retail Trade",
    "48-49": "Transportation and Warehousing",
    "51": "Information",
    "52": "Finance and Insurance",
    "53": "Real Estate and Rental and Leasing",
    "54": "Professional, Scientific, and Technical Services",
    "55": "Management of Companies and Enterprises",
    "56": "Administrative and Support Services",
    "61": "Educational Services",
    "62": "Health Care and Social Assistance",
    "71": "Arts, Entertainment, and Recreation",
    "72": "Accommodation and Food Services",
    "81": "Other Services",
    "92": "Public Administration",
}


def load_predictions(agent: str) -> pd.DataFrame:
    """Load predictions for an agent."""
    path = PREDICTIONS_DIR / f"{agent}_predictions.parquet"
    logger.info(f"Loading {agent} predictions from {path}")
    return pd.read_parquet(path)


def load_first_use(agent: str) -> pd.DataFrame:
    """Load first use dates for an agent."""
    path = ADOPTION_DIR / f"{agent}_first_use.parquet"
    logger.info(f"Loading {agent} first use from {path}")
    df = pd.read_parquet(path)

    # Normalize columns
    if "repo_nwo" in df.columns:
        df = df.rename(columns={"repo_nwo": "nwo"})
    if "first_claude_commit" in df.columns:
        df = df.rename(columns={"first_claude_commit": "first_use_date"})

    df["first_use_date"] = pd.to_datetime(df["first_use_date"], utc=True)
    return df


def generate_overview_table() -> pd.DataFrame:
    """Generate overview table with counts per agent."""
    agents = ["claude", "copilot", "codex"]
    display_names = ["Claude Code", "GitHub Copilot", "OpenAI Codex"]

    rows = []
    for agent, display in zip(agents, display_names):
        try:
            preds = load_predictions(agent)
            first_use = load_first_use(agent)

            # Merge to get date range
            merged = first_use.merge(preds[["nwo", "predicted_naics"]], on="nwo", how="inner")

            # Get top industry
            top_industry = merged["predicted_naics"].value_counts().idxmax()
            top_pct = merged["predicted_naics"].value_counts(normalize=True).max() * 100

            rows.append({
                "Agent": display,
                "Repos with Predictions": len(preds),
                "Repos with First Use": len(first_use),
                "Merged Repos": len(merged),
                "Date Range": f"{merged['first_use_date'].min().strftime('%Y-%m')} to {merged['first_use_date'].max().strftime('%Y-%m')}",
                "Top Industry": f"{top_industry} ({NAICS_DESCRIPTIONS.get(top_industry, 'Unknown')[:20]}...)",
                "Top Industry %": f"{top_pct:.1f}%"
            })
        except Exception as e:
            logger.warning(f"Error processing {agent}: {e}")

    return pd.DataFrame(rows)


def generate_industry_breakdown(agent: str) -> pd.DataFrame:
    """Generate industry breakdown for a single agent."""
    preds = load_predictions(agent)
    first_use = load_first_use(agent)

    merged = first_use.merge(preds[["nwo", "predicted_naics"]], on="nwo", how="inner")

    # Count by industry
    industry_counts = merged["predicted_naics"].value_counts()
    industry_pcts = merged["predicted_naics"].value_counts(normalize=True) * 100

    rows = []
    for naics in industry_counts.index:
        rows.append({
            "NAICS Code": naics,
            "Industry": NAICS_DESCRIPTIONS.get(naics, "Unknown"),
            "Repo Count": industry_counts[naics],
            "Percentage": f"{industry_pcts[naics]:.1f}%"
        })

    return pd.DataFrame(rows)


def generate_monthly_adoption(agent: str) -> pd.DataFrame:
    """Generate monthly adoption counts for an agent."""
    preds = load_predictions(agent)
    first_use = load_first_use(agent)

    merged = first_use.merge(preds[["nwo", "predicted_naics"]], on="nwo", how="inner")
    merged["month"] = merged["first_use_date"].dt.to_period("M")

    monthly = merged.groupby("month").size().reset_index(name="new_repos")
    monthly["month"] = monthly["month"].astype(str)
    monthly["cumulative_repos"] = monthly["new_repos"].cumsum()

    return monthly


def generate_confidence_stats(agent: str) -> pd.DataFrame:
    """Generate confidence score statistics."""
    preds = load_predictions(agent)

    if "confidence" not in preds.columns:
        logger.warning(f"No confidence column in {agent} predictions")
        return pd.DataFrame()

    stats = {
        "Mean Confidence": preds["confidence"].mean(),
        "Median Confidence": preds["confidence"].median(),
        "Std Confidence": preds["confidence"].std(),
        "Min Confidence": preds["confidence"].min(),
        "Max Confidence": preds["confidence"].max(),
        "Repos > 0.9 conf": (preds["confidence"] > 0.9).sum(),
        "Repos > 0.8 conf": (preds["confidence"] > 0.8).sum(),
        "Repos > 0.7 conf": (preds["confidence"] > 0.7).sum(),
    }

    return pd.DataFrame([stats])


def main():
    """Generate all summary statistics."""
    logger.info("Generating summary statistics")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Overview table
    logger.info("\n" + "="*60)
    logger.info("OVERVIEW TABLE")
    logger.info("="*60)
    overview = generate_overview_table()
    print(overview.to_string(index=False))
    overview.to_csv(OUTPUT_DIR / "overview.csv", index=False)

    # Industry breakdown per agent
    agents = ["claude", "copilot", "codex"]
    display_names = {"claude": "Claude Code", "copilot": "GitHub Copilot", "codex": "OpenAI Codex"}

    for agent in agents:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"INDUSTRY BREAKDOWN - {display_names[agent]}")
            logger.info("="*60)
            breakdown = generate_industry_breakdown(agent)
            print(breakdown.to_string(index=False))
            breakdown.to_csv(OUTPUT_DIR / f"industry_breakdown_{agent}.csv", index=False)
        except Exception as e:
            logger.warning(f"Error generating breakdown for {agent}: {e}")

    # Monthly adoption
    for agent in agents:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"MONTHLY ADOPTION - {display_names[agent]}")
            logger.info("="*60)
            monthly = generate_monthly_adoption(agent)
            print(monthly.tail(12).to_string(index=False))
            monthly.to_csv(OUTPUT_DIR / f"monthly_adoption_{agent}.csv", index=False)
        except Exception as e:
            logger.warning(f"Error generating monthly adoption for {agent}: {e}")

    # Confidence statistics
    for agent in agents:
        try:
            conf_stats = generate_confidence_stats(agent)
            if not conf_stats.empty:
                logger.info(f"\n{'='*60}")
                logger.info(f"CONFIDENCE STATS - {display_names[agent]}")
                logger.info("="*60)
                print(conf_stats.to_string(index=False))
                conf_stats.to_csv(OUTPUT_DIR / f"confidence_stats_{agent}.csv", index=False)
        except Exception as e:
            logger.warning(f"Error generating confidence stats for {agent}: {e}")

    logger.info(f"\nAll statistics saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
