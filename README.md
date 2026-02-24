# AI Coding Agents: Industry Adoption Analysis

> Research dashboard analyzing how **886,000+ GitHub repositories** adopt AI coding assistants across **19 NAICS industry sectors**.

This is the **static HTML/CSS/JS** version of the dashboard. For the full-stack Next.js version with a daily-updating pipeline, see [ai-coding-agents-next](https://github.com/raulsedano2410/ai-coding-agents-next).

---

## What This Project Does

We analyzed adoption patterns of AI coding agents across public GitHub repositories, classifying each repository by industry using the NAICS (North American Industry Classification System) framework.

| Agent | Repos Analyzed | Top Industry | Growth Rank |
|-------|---------------|-------------|-------------|
| Claude Code | 391K | Professional Services (28%) | #1 |
| OpenAI Codex | 249K | Professional Services (22%) | #3 |
| GitHub Copilot | 247K | Professional Services (25%) | #2 |
| Cursor AI | 129K | Professional Services (24%) | #4 |

---

## Data Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  GitHub API  │───→│  Repo        │───→│  RoBERTa     │───→│  Aggregate   │
│              │    │  Metadata    │    │  Classifier  │    │  by Month    │
│ Commits, PRs │    │ desc, topics │    │ 19 NAICS     │    │ & Industry   │
│ Co-Author    │    │ README       │    │ sectors      │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                    │
                                                                    ▼
                                                            ┌──────────────┐
                                                            │  JSON Files  │
                                                            │              │
                                                            │ *_cumulative │
                                                            │    .json     │
                                                            └──────────────┘
                                                                    │
                                                                    ▼
                                                            ┌──────────────┐
                                                            │ Static Site  │
                                                            │              │
                                                            │ HTML + CSS   │
                                                            │ + Chart.js   │
                                                            └──────────────┘
```

### Detection Methods

| Agent | How We Detect It |
|-------|-----------------|
| Claude Code | `Co-Authored-By: Claude <noreply@anthropic.com>` in commits |
| GitHub Copilot | Copilot attribution patterns in commits and PRs |
| OpenAI Codex | `Co-Authored-By: *@openai.com` in commits |
| Cursor AI | `head:cursor/` branch prefix in PRs + `cursoragent@cursor.com` |

### Classification

A **fine-tuned RoBERTa model** classifies each repository into one of 19 NAICS sectors based on:
- Repository name and description
- Topics/tags
- README content (first 512 tokens)

Model performance: **78.3% accuracy**, **0.79 weighted F1** on a test set of 5,000 repos.

---

## Key Findings

1. **Professional Services Dominates** — NAICS sector 54 leads adoption across all agents (22–28% of repositories)
2. **Information Sector Strong Second** — NAICS 51 consistently ranks #2 (tech companies, publishers, data processors)
3. **Claude Code Fastest Growth** — Steepest adoption curve; 111K+ new repos in January 2026 alone
4. **Finance & Healthcare Accelerating** — Growing trust in AI coding tools for regulated industries

---

## Features

### Per-Agent Pages
- **Animated Bar Race** with Play/Pause/Reset, speed control (0.5x–4x), month selector
- **Cumulative Adoption Chart** — Line chart with Top 5/10/All filter + Linear/Log scale
- **Monthly New Repos Chart** — Toggle between Line and Stacked Bar
- **Clickable Legends** — Click industries to show/hide series
- **4 Stat Cards** — Total repos, industries tracked, current period, leading industry

### Overview Page
- Hero stats (886K+, 19 industries, 4 agents)
- Agent cards with 4 metrics each (repos, % professional services, months of data, growth rank)
- Comparison chart (all 4 agents)
- Key findings section

### Reference Pages
- **Industries** — 19 NAICS sector cards with descriptions and example repo types
- **Methodology** — Table of Contents, detection validation, per-sector performance, confidence calibration

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | HTML5, CSS3 (custom dark theme) |
| **Charts** | Chart.js |
| **Data** | Static JSON files |
| **Fonts** | Mona Sans (Google Fonts) |
| **Hosting** | GitHub Pages |

---

## Repository Structure

```
ai-coding-agents-industry-analysis/
├── docs/                           # Static site (GitHub Pages root)
│   ├── index.html                  # Overview: stats, cards, comparison
│   ├── claude.html                 # Claude Code detail page
│   ├── copilot.html                # GitHub Copilot detail page
│   ├── codex.html                  # OpenAI Codex detail page
│   ├── cursor.html                 # Cursor AI detail page
│   ├── industries.html             # 19 NAICS sector cards
│   ├── methodology.html            # Full methodology documentation
│   ├── claude_cumulative.json      # Claude time-series data
│   ├── copilot_cumulative.json     # Copilot time-series data
│   ├── codex_cumulative.json       # Codex time-series data
│   └── cursor_cumulative.json      # Cursor time-series data
├── data/
│   ├── predictions/                # Industry classifications (Parquet)
│   ├── adoption_timing/            # First-use dates (Parquet)
│   └── samples/                    # High-confidence validation samples
├── figures/                        # Static charts (PNG)
├── scripts/                        # Analysis scripts (Python)
└── README.md
```

---

## JSON Data Format

Each `*_cumulative.json` file follows this structure:

```json
{
  "agent": "claude",
  "total_repos": 391000,
  "months": ["2025-01", "2025-02", "..."],
  "industries": [
    {
      "code": "54",
      "name": "Professional Services",
      "color": "#7c3aed",
      "values": [12000, 45000, "..."],
      "monthly": [12000, 33000, "..."]
    }
  ]
}
```

- `values[]` — Cumulative repository count per month
- `monthly[]` — New repositories added that month

---

## Local Development

No build step required. Just serve the `docs/` directory:

```bash
# Using Python
cd docs && python -m http.server 8000

# Using Node.js
npx serve docs
```

Open [http://localhost:8000](http://localhost:8000).

---

## NAICS Sectors Tracked

| Code | Industry | Code | Industry |
|------|---------|------|---------|
| 11 | Agriculture | 54 | Professional Services |
| 21 | Mining | 56 | Admin Services |
| 22 | Utilities | 61 | Education |
| 23 | Construction | 62 | Healthcare |
| 31-33 | Manufacturing | 71 | Entertainment |
| 42 | Wholesale Trade | 72 | Accommodation |
| 44-45 | Retail Trade | 81 | Other Services |
| 48-49 | Transportation | 92 | Public Admin |
| 51 | Information | | |
| 52 | Finance & Insurance | | |
| 53 | Real Estate | | |

**Excluded:** NAICS 55 (Management of Companies) — insufficient representation in public repos.

---

## Related Repositories

| Repository | Description |
|-----------|-------------|
| [ai-coding-agents-next](https://github.com/raulsedano2410/ai-coding-agents-next) | Next.js + Supabase version with daily pipeline |
| [github-repo-fetcher](https://github.com/alexanderquispe/github-repo-fetcher) | Python scripts for bulk GitHub API data collection |
| [naics-github-train](https://github.com/alexanderquispe/naics-github-train) | RoBERTa NAICS classifier training code |

---

## License

Data and analysis provided for research purposes. See individual data sources for their respective terms of use.
