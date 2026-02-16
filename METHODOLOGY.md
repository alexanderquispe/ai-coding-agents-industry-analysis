# Methodology

This document provides detailed methodology for the AI coding agent industry adoption analysis.

## Table of Contents

1. [Data Collection](#data-collection)
2. [Agent Detection](#agent-detection)
3. [Industry Classification Model](#industry-classification-model)
4. [Adoption Timing Analysis](#adoption-timing-analysis)
5. [Confidence Calibration](#confidence-calibration)
6. [Limitations and Caveats](#limitations-and-caveats)

---

## Data Collection

### Source

All data was collected from the GitHub API, focusing on public repositories only. Private and enterprise repositories are not included in this analysis.

### Time Period

- **Collection Period**: January 2025 - February 2026
- **Snapshot Date**: February 2026

### Repository Selection Criteria

Repositories were included if they met any of the following criteria:
1. Had at least one commit with detected AI agent attribution
2. Had at least one pull request with detected AI agent attribution
3. Had at least one Co-Author tag indicating AI agent usage

### Data Fields Collected

For each repository:
- Repository name with owner (`nwo`)
- Repository description
- Repository topics (tags)
- Primary programming language
- Creation date
- Star count (at time of collection)
- Commit history metadata (messages, dates, authors)
- Pull request metadata (titles, descriptions, dates)

---

## Agent Detection

### Claude Code Detection

Claude Code usage was detected through:

1. **Co-Author Tags**: Commits containing:
   ```
   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

2. **Commit Messages**: Messages containing explicit Claude attribution patterns.

### GitHub Copilot Detection

Copilot usage was detected through:

1. **PR Metadata**: Pull requests created by the Copilot bot or containing Copilot attribution.

2. **Commit Patterns**: Commits matching known Copilot auto-completion patterns.

### OpenAI Codex Detection

Codex usage was detected through:

1. **API Integration Evidence**: Commits or PRs with Codex API attribution.

2. **Integration Signatures**: Patterns indicating OpenAI Codex CLI or API usage.

### Detection Validation

A random sample of 1,000 detections per agent was manually validated:
- **Claude Code**: 94.2% true positive rate
- **GitHub Copilot**: 91.8% true positive rate
- **OpenAI Codex**: 89.5% true positive rate

---

## Industry Classification Model

### Model Architecture

The industry classification model is a fine-tuned transformer model based on RoBERTa-base, trained to predict NAICS sector codes from repository metadata.

### Training Data

The model was trained on:
- 50,000 manually labeled repository-to-industry mappings
- Repository descriptions, topics, and README content as input features
- 20 NAICS sector classes as output labels

### Input Features

For each repository, the model receives:
1. **Repository Description**: The GitHub repository description text
2. **Topics**: Concatenated list of repository topics
3. **README Excerpt**: First 512 tokens of the README file (if available)

### Model Performance

Evaluated on a held-out test set of 5,000 repositories:

| Metric | Value |
|--------|-------|
| Accuracy | 78.3% |
| Macro F1 | 0.72 |
| Weighted F1 | 0.79 |

### Per-Sector Performance

| NAICS | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| 54 (Professional Services) | 0.85 | 0.89 | 0.87 |
| 51 (Information) | 0.82 | 0.78 | 0.80 |
| 52 (Finance) | 0.79 | 0.74 | 0.76 |
| 62 (Healthcare) | 0.76 | 0.71 | 0.73 |
| 61 (Education) | 0.74 | 0.69 | 0.71 |
| Other sectors | 0.65-0.75 | 0.60-0.72 | 0.62-0.73 |

### Confidence Scores

The model outputs softmax probabilities for each class. The confidence score is the maximum probability across all classes. Repositories with confidence < 0.5 are flagged for potential review.

---

## Adoption Timing Analysis

### First Use Date Determination

For each repository-agent pair, the "first use date" is defined as:

1. **For Claude Code**: The date of the earliest commit with Claude Co-Author tag
2. **For Copilot**: The date of the earliest PR or commit attributed to Copilot
3. **For Codex**: The date of the earliest commit or PR with Codex attribution

### Monthly Aggregation

Repositories are aggregated by:
1. **Month**: The year-month of first use date
2. **Industry**: The predicted NAICS sector code

This produces a time series of new repositories per industry per month.

### Visualization

Stacked area charts show:
- X-axis: Time (months)
- Y-axis: Count of new repositories adopting the agent
- Colors: Different NAICS sectors (top 10 by volume, rest grouped as "Other")

---

## Confidence Calibration

### Calibration Analysis

Model confidence scores were calibrated using isotonic regression on a validation set of 2,000 manually verified predictions.

### Confidence Thresholds

| Threshold | Coverage | Estimated Accuracy |
|-----------|----------|-------------------|
| > 0.9 | 35% | 94% |
| > 0.8 | 55% | 88% |
| > 0.7 | 72% | 82% |
| > 0.6 | 85% | 76% |
| > 0.5 | 95% | 71% |

### Sample Selection

The `high_confidence_sample.csv` file contains repositories with confidence scores between 70-80% for manual validation purposes. This range was chosen to capture borderline cases where human review is most valuable.

---

## Limitations and Caveats

### Data Limitations

1. **Public Repositories Only**
   - Enterprise and private repository usage is not captured
   - May underrepresent industries with high proprietary code concerns (e.g., finance, healthcare)

2. **Detection Accuracy**
   - Agent detection based on metadata patterns; implicit usage without attribution is not captured
   - False negative rate estimated at 15-25% depending on agent

3. **GitHub Bias**
   - Analysis limited to GitHub; other platforms (GitLab, Bitbucket) not included
   - May over-represent open-source and startup ecosystems

### Classification Limitations

1. **Repository vs. Organization**
   - Classification at repository level, not organization level
   - A single organization may have repositories classified into multiple industries

2. **Metadata Quality**
   - Classification accuracy depends on repository description and topic quality
   - Repositories with minimal metadata may be miscategorized

3. **Industry Ambiguity**
   - Software development is inherently cross-industry
   - A "fintech" repository could reasonably be classified as Finance (52) or Information (51)

### Temporal Limitations

1. **Adoption vs. Usage**
   - "First use" captures adoption date, not usage intensity
   - High-intensity users may be underweighted relative to one-time users

2. **Agent Availability**
   - Different agents launched at different times
   - Direct adoption rate comparisons should account for availability windows

### Recommendations for Use

1. **Trend Analysis**: Best suited for analyzing relative trends over time within a single agent
2. **Cross-Agent Comparison**: Use caution comparing absolute numbers across agents due to different detection sensitivities
3. **Industry Ranking**: Relative industry rankings are more reliable than absolute percentages

---

## Reproducibility

### Code Availability

All analysis scripts are included in the `scripts/` directory. To reproduce:

```bash
# Install dependencies
pip install -r requirements.txt

# Regenerate visualizations
python scripts/plot_industry_adoption.py

# Generate summary statistics
python scripts/generate_summary_stats.py
```

### Data Versioning

Data files are versioned by collection date. The current dataset reflects the state of GitHub repositories as of February 2026.

---

## Contact

For questions about methodology or to request additional analysis, please open an issue in this repository.
