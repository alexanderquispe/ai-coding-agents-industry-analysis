#!/usr/bin/env python3
"""
Update cumulative JSONs in public/data/ with classified repos.
Scans data/daily/ for all classified files not yet processed.
Tracks processed dates in data/processed_dates.txt to avoid double-counting.
"""

import json
from pathlib import Path
from collections import defaultdict

ALL_AGENTS = ['claude', 'copilot', 'codex', 'cursor']
ALL_INDUSTRIES = [
    '11', '21', '22', '23', '31-33', '42', '44-45', '48-49',
    '51', '52', '53', '54', '56', '61', '62', '71', '72', '81', '92'
]

JSON_DIR = Path('public/data')
DAILY_DIR = Path('data/daily')
PROCESSED_FILE = Path('data/processed_dates.txt')


def load_processed_dates():
    if not PROCESSED_FILE.exists():
        return set()
    with open(PROCESSED_FILE) as f:
        return set(line.strip() for line in f if line.strip())


def save_processed_date(date):
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, 'a') as f:
        f.write(date + '\n')


def find_unprocessed_files():
    """Find all classified files that haven't been integrated into cumulative JSONs."""
    processed = load_processed_dates()
    files = []
    for f in sorted(DAILY_DIR.glob('*_classified.json')):
        date = f.stem.replace('_classified', '')
        if date not in processed:
            files.append((date, f))
    return files


def update_cumulative_jsons(classified_items, current_month):
    """Update the 4 cumulative JSON files with new classified repos."""
    agent_industry_new = defaultdict(lambda: defaultdict(int))
    for item in classified_items:
        naics = item.get('naics_code', '')
        for agent_id in item.get('agents', []):
            if agent_id in ALL_AGENTS and naics in ALL_INDUSTRIES:
                agent_industry_new[agent_id][naics] += 1

    updated_agents = []

    for agent_id in ALL_AGENTS:
        json_path = JSON_DIR / f'{agent_id}_cumulative.json'
        if not json_path.exists():
            print(f'  {agent_id}: JSON not found, skipping')
            continue

        with open(json_path) as f:
            data = json.load(f)

        months = data.get('months', [])
        industries = data.get('industries', [])
        new_counts = agent_industry_new.get(agent_id, {})

        if not new_counts:
            print(f'  {agent_id}: no new repos')
            continue

        if current_month in months:
            month_idx = months.index(current_month)
        else:
            months.append(current_month)
            month_idx = len(months) - 1
            for ind in industries:
                prev_val = ind['values'][-1] if ind['values'] else 0
                ind['values'].append(prev_val)
                ind['monthly'].append(0)

        total_new = 0
        for ind in industries:
            code = ind['code']
            new_count = new_counts.get(code, 0)
            if new_count > 0:
                ind['values'][month_idx] += new_count
                ind['monthly'][month_idx] += new_count
                total_new += new_count

        data['total_repos'] = sum(ind['values'][-1] for ind in industries)
        data['months'] = months

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

        updated_agents.append(agent_id)
        print(f'  {agent_id}: +{total_new} repos -> total {data["total_repos"]:,}')

    return updated_agents


def main():
    unprocessed = find_unprocessed_files()

    if not unprocessed:
        print('No unprocessed classified files found')
        return

    print(f'Found {len(unprocessed)} unprocessed date(s): {", ".join(d for d, _ in unprocessed)}\n')

    for date, classified_file in unprocessed:
        with open(classified_file) as f:
            items = json.load(f)

        if not items:
            print(f'{date}: empty, marking as processed')
            save_processed_date(date)
            continue

        current_month = date[:7]  # YYYY-MM
        print(f'{date}: {len(items)} classified repos (month: {current_month})')

        print('Updating cumulative JSONs:')
        update_cumulative_jsons(items, current_month)

        save_processed_date(date)
        print()

    print('Done!')


if __name__ == '__main__':
    main()
