#!/usr/bin/env python3
"""
Update cumulative JSONs in public/data/ and Supabase with yesterday's classified repos.
Reads from data/daily/{date}_classified.json, updates both:
  1. public/data/{agent}_cumulative.json (for static fallback + git history)
  2. Supabase monthly_stats table (for production)
"""

import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

ALL_AGENTS = ['claude', 'copilot', 'codex', 'cursor']
ALL_INDUSTRIES = [
    '11', '21', '22', '23', '31-33', '42', '44-45', '48-49',
    '51', '52', '53', '54', '56', '61', '62', '71', '72', '81', '92'
]

JSON_DIR = Path('public/data')
DAILY_DIR = Path('data/daily')


def update_cumulative_jsons(classified_items, current_month):
    """Update the 4 cumulative JSON files with new classified repos."""
    # Count new repos per agent per industry
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
            print(f'  {agent_id}: no new repos today')
            continue

        # Check if current month already exists
        if current_month in months:
            month_idx = months.index(current_month)
        else:
            # Add new month
            months.append(current_month)
            month_idx = len(months) - 1
            for ind in industries:
                # Carry forward previous cumulative
                prev_val = ind['values'][-1] if ind['values'] else 0
                ind['values'].append(prev_val)
                ind['monthly'].append(0)

        # Add new repos to current month
        total_new = 0
        for ind in industries:
            code = ind['code']
            new_count = new_counts.get(code, 0)
            if new_count > 0:
                ind['values'][month_idx] += new_count
                ind['monthly'][month_idx] += new_count
                total_new += new_count

        # Recalculate total_repos
        data['total_repos'] = sum(ind['values'][-1] for ind in industries)
        data['months'] = months

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

        updated_agents.append(agent_id)
        print(f'  {agent_id}: +{total_new} repos -> total {data["total_repos"]:,}')

    return updated_agents


def update_supabase(classified_items, current_month):
    """Update Supabase monthly_stats with new data."""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print('  Supabase not configured, skipping')
        return

    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)

    # Count new repos per agent per industry
    agent_industry_new = defaultdict(lambda: defaultdict(int))
    for item in classified_items:
        naics = item.get('naics_code', '')
        for agent_id in item.get('agents', []):
            if agent_id in ALL_AGENTS and naics in ALL_INDUSTRIES:
                agent_industry_new[agent_id][naics] += 1

    updates = 0
    for agent_id in ALL_AGENTS:
        new_counts = agent_industry_new.get(agent_id, {})
        if not new_counts:
            continue

        # Also update total_repos from JSON
        json_path = JSON_DIR / f'{agent_id}_cumulative.json'
        if json_path.exists():
            with open(json_path) as f:
                data = json.load(f)
            supabase.table('agents').update(
                {'total_repos': data['total_repos']}
            ).eq('id', agent_id).execute()

        for industry_code in ALL_INDUSTRIES:
            count = new_counts.get(industry_code, 0)

            # Check if row exists for this month
            result = supabase.table('monthly_stats').select('*').eq(
                'agent_id', agent_id
            ).eq(
                'industry_code', industry_code
            ).eq(
                'month', current_month
            ).execute()

            existing = result.data[0] if result.data else None

            if existing:
                if count > 0:
                    supabase.table('monthly_stats').update({
                        'cumulative': existing['cumulative'] + count,
                        'new_repos': existing['new_repos'] + count
                    }).eq('id', existing['id']).execute()
                    updates += 1
            else:
                # Get previous month cumulative
                prev = supabase.table('monthly_stats').select(
                    'cumulative'
                ).eq('agent_id', agent_id).eq(
                    'industry_code', industry_code
                ).order('month', desc=True).limit(1).execute()

                prev_cum = prev.data[0]['cumulative'] if prev.data else 0

                supabase.table('monthly_stats').insert({
                    'agent_id': agent_id,
                    'industry_code': industry_code,
                    'month': current_month,
                    'cumulative': prev_cum + count,
                    'new_repos': count
                }).execute()
                updates += 1

    # Update metadata
    supabase.table('metadata').upsert({
        'key': 'last_updated',
        'value': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }).execute()

    print(f'  Supabase: {updates} rows updated')


def main():
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    current_month = yesterday[:7]  # YYYY-MM

    classified_file = DAILY_DIR / f'{yesterday}_classified.json'

    if not classified_file.exists():
        print(f'No classified file for {yesterday}')
        return

    with open(classified_file) as f:
        classified_items = json.load(f)

    if not classified_items:
        print(f'No classified items for {yesterday}')
        return

    print(f'Updating data for {yesterday} ({len(classified_items)} classified repos)')
    print(f'Month: {current_month}\n')

    # 1. Update cumulative JSONs
    print('Updating cumulative JSONs:')
    update_cumulative_jsons(classified_items, current_month)

    # 2. Update Supabase
    print('\nUpdating Supabase:')
    update_supabase(classified_items, current_month)

    print('\nDone!')


if __name__ == '__main__':
    main()
